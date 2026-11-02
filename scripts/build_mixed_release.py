#!/usr/bin/env python3
"""Build a cumulative game patch release from uploaded files plus external download links."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote

from build_release import build, BLOCKED


def normalize_path(path):
    if not isinstance(path, str):
        raise ValueError("path must be a string")
    parts = path.split("/")
    if (not path or path.startswith("/") or any(
        not part or part in (".", "..") or part.endswith((" ", "."))
        or ":" in part or "\\" in part or any(ord(c) < 32 for c in part)
        for part in parts
    )):
        raise ValueError(f"Unsafe game-relative path: {path}")
    if (parts[-1].lower() in BLOCKED
        or any(p.startswith(".") for p in parts)):
        raise ValueError(f"Protected game path: {path}")
    return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--source", type=Path, default=Path("updates"))
    p.add_argument("--links", type=Path, default=Path("patch_links.json"))
    p.add_argument("--output", type=Path, default=Path("release_assets"))
    args = p.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        raise ValueError("Invalid repo")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", args.tag):
        raise ValueError("Invalid release tag")

    local_files = [
        f for f in args.source.rglob("*")
        if f.is_file() and f.name != ".gitkeep"
    ] if args.source.is_dir() else []

    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Release output directory must be empty")

    if local_files:
        manifest = build(args.repo, args.tag, args.source, args.output)
    else:
        output.mkdir(parents=True, exist_ok=True)
        manifest = {"version": args.tag, "files": []}

    files = {x["path"].casefold(): x for x in manifest["files"]}
    if args.links.is_file():
        links = json.loads(args.links.read_text(encoding="utf-8"))
        if not isinstance(links, dict) or not isinstance(links.get("files"), list):
            raise ValueError("patch_links.json must be an object with a files array")
        seen = set()
        for entry in links["files"]:
            if not isinstance(entry, dict):
                raise ValueError("A patch entry must be an object")
            path = normalize_path(entry.get("path"))
            key = path.casefold()
            if key in seen:
                raise ValueError(f"Duplicate download path: {path}")
            seen.add(key)
            url = entry.get("url")
            if not isinstance(url, str) or not urlparse(url).scheme == "https":
                raise ValueError(f"Only HTTPS downloads are allowed: {path}")
            parsed = urlparse(url)
            if not parsed.hostname or parsed.username or parsed.password:
                raise ValueError(f"Invalid download URL for {path}")
            digest = entry.get("sha256")
            # SHA-256 and size are optional for URL-only patches. Existing
            # values, when present, still provide verification to new clients.
            if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)):
                raise ValueError(f"Invalid SHA-256 for {path}")
            size = entry.get("size")
            if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 0):
                raise ValueError(f"size must be a nonnegative integer: {path}")
            old = files.get(key)
            if old:
                old_asset = unquote(urlparse(old["url"]).path.rsplit("/", 1)[-1])
                if old_asset.startswith("p_") and (output / old_asset).is_file():
                    (output / old_asset).unlink()
            file_entry = {"path": path, "url": url}
            if digest is not None:
                file_entry["sha256"] = digest.lower()
            if size is not None:
                file_entry["size"] = size
            # Optional exact file inside a ZIP; useful when the download
            # URL points at an archive containing more than one XML.
            zip_entry = entry.get("zip_entry")
            if zip_entry is not None:
                file_entry["zip_entry"] = normalize_path(zip_entry)
            files[key] = file_entry

    archives = []
    if args.links.is_file():
        raw_archives = links.get("archives", [])
        if not isinstance(raw_archives, list) or len(raw_archives) > 100:
            raise ValueError("archives must be an array with at most 100 ZIP patches")
        seen_names = set()
        for archive in raw_archives:
            if not isinstance(archive, dict):
                raise ValueError("Each archives entry must be an object")
            name = archive.get("name", "update.zip")
            if (not isinstance(name, str) or not name or len(name) > 160
                    or "/" in name or "\\" in name or ":" in name):
                raise ValueError("Invalid ZIP patch name")
            if name.casefold() in seen_names:
                raise ValueError("Each ZIP patch must have a unique name")
            seen_names.add(name.casefold())
            url = archive.get("url")
            if not isinstance(url, str) or urlparse(url).scheme != "https":
                raise ValueError(f"ZIP patch must use HTTPS: {name}")
            parsed = urlparse(url)
            if not parsed.hostname or parsed.username or parsed.password:
                raise ValueError(f"Invalid ZIP URL: {name}")
            digest = archive.get("sha256")
            if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)):
                raise ValueError(f"Invalid ZIP SHA-256: {name}")
            size = archive.get("size")
            if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 0):
                raise ValueError(f"Invalid ZIP size: {name}")
            archive_entry = {"name": name, "url": url}
            if digest is not None:
                archive_entry["sha256"] = digest.lower()
            if size is not None:
                archive_entry["size"] = size
            archives.append(archive_entry)

    if not files and not archives:
        raise ValueError("No uploaded files, external file links, or ZIP patches registered")
    if len(files) > 900:
        raise ValueError("Too many files in manifest")
    manifest["files"] = sorted(files.values(), key=lambda item: item["path"].casefold())
    if archives:
        manifest["archives"] = archives
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print("Generated", len(files), "files and", len(archives), "ZIP archives; external links override uploaded files")


if __name__ == "__main__":
    main()
