"""Validate packwiz index integrity without installing or downloading mods."""

import hashlib
import json
import sys
from pathlib import Path

import tomllib

root = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


pack = tomllib.loads((root / "pack.toml").read_text(encoding="utf-8"))
assert sha(root / "index.toml") == pack["index"]["hash"], "Stale pack index hash"
index = tomllib.loads((root / "index.toml").read_text(encoding="utf-8"))
seen = set()
for entry in index["files"]:
    path = root / entry["file"]
    assert path.resolve().is_relative_to(root), f"Unsafe path: {path}"
    assert entry["file"] not in seen, f"Duplicate: {path}"
    seen.add(entry["file"])
    assert sha(path) == entry["hash"], f"Stale hash: {path}"
    if entry.get("metafile"):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        assert data["side"] in ("client", "server", "both")
        assert data["download"].get("mode") == "metadata:curseforge" or data[
            "download"
        ]["url"].startswith("https://")
        assert data["download"]["hash"]
print(f"Validated {len(seen)} indexed files and pack/index hashes.")
unresolved = json.loads((root / "UNRESOLVED.json").read_text(encoding="utf-8"))
if unresolved:
    print(
        f"WARNING: {len(unresolved)} downloads still need resolution; fresh installs are incomplete."
    )
    if "--release" in sys.argv:
        sys.exit(1)
