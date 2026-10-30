#!/usr/bin/env python3
"""Convert updates/<client-relative-path> into cumulative GitHub Release assets."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

BLOCKED = {
    "clientconfiguration.xml", "launcher_config.json", "client_version.txt",
    "bns_launcher.exe", "manifest.json",
}

def build(repo: str, tag: str, source: Path, output: Path):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Invalid repository name")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", tag):
        raise ValueError("Invalid release tag")
    source, output = source.resolve(), output.resolve()
    if not source.is_dir() or source == output or source in output.parents or output in source.parents:
        raise ValueError("Invalid input or output directory")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty")
    entries = []
    for file in sorted(source.rglob("*")):
        if file.is_symlink():
            raise ValueError(f"Symlink not allowed: {file}")
        if not file.is_file() or file.name == ".gitkeep":
            continue
        relative = file.relative_to(source).as_posix()
        parts = relative.split("/")
        if (any(p in ("", ".", "..") or p.endswith((" ", ".")) or ":" in p or "\\" in p for p in parts)
                or any(ord(c) < 32 for c in relative)):
            raise ValueError(f"Unsafe game path: {relative}")
        if file.name.lower() in BLOCKED or any(p.startswith(".") for p in parts):
            raise ValueError(f"Protected file: {relative}")
        if file.stat().st_size > 2_000_000_000:
            raise ValueError(f"Asset too large: {relative}")
        h = hashlib.sha256()
        with file.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        digest = h.hexdigest()
        namehash = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20]
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", file.name)[:100]
        asset = f"p_{namehash}_{safe_name}"
        entries.append((file, relative, asset, digest, file.stat().st_size))
    if not entries or len(entries) > 900:
        raise ValueError("Provide between 1 and 900 patch files in updates/")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"version": tag, "files": []}
    for file, path, asset, digest, size in entries:
        shutil.copy2(file, output / asset)
        manifest["files"].append({
            "path": path,
            "url": f"https://github.com/{repo}/releases/download/{quote(tag, safe='')}/{quote(asset, safe='')}",
            "sha256": digest,
            "size": size,
        })
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Ready: {tag}, {len(entries)} patch files")
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source", type=Path, default=Path("updates"))
    parser.add_argument("--output", type=Path, default=Path("release_assets"))
    args = parser.parse_args()
    build(args.repo, args.tag, args.source, args.output)
