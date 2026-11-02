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
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                raise ValueError(f"Missing or invalid SHA-256 for {path}")
            size = entry.get("size")
            if isinstance(size, bool) or not isinstance(size, int) or size < 0:
                raise ValueError(f"size must be a nonnegative integer: {path}")
            old = files.get(key)
            if old:
                old_asset = unquote(urlparse(old["url"]).path.rsplit("/", 1)[-1])
                if old_asset.startswith("p_") and (output / old_asset).is_file():
                    (output / old_asset).unlink()
            files[key] = {
                "path": path, "url": url,
                "sha256": digest.lower(), "size": size
            }

    if not files:
        raise ValueError("No uploaded patch files or link entries found")
    if len(files) > 900:
        raise ValueError("Too many files in manifest")
    manifest["files"] = sorted(files.values(), key=lambda item: item["path"].casefold())
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print("Generated", len(files), "patch entries; external links override matching uploaded paths")


if __name__ == "__main__":
    main()
