"""Validate packwiz index integrity without installing or downloading mods."""

import hashlib
import json
import subprocess
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
        download = data["download"]
        if "url" in download:
            assert download["url"].startswith(("https://", "http://")), (
                f"Invalid download URL: {path}"
            )
        else:
            assert download.get("mode") == "metadata:curseforge", (
                f"Missing download URL: {path}"
            )
        if download.get("mode") == "metadata:curseforge":
            curseforge = data["update"]["curseforge"]
            assert curseforge["file-id"] > 0 and curseforge["project-id"] > 0
        assert data["download"]["hash"]
if (root / ".git").exists():
    result = subprocess.run(
        ["git", "--no-pager", "check-ignore", "--stdin"],
        input="\n".join(sorted(seen)) + "\n",
        text=True,
        capture_output=True,
        cwd=root,
    )
    assert result.returncode in (0, 1), result.stderr
    assert not result.stdout.strip(), "Indexed files ignored by Git:\n" + result.stdout
print(f"Validated {len(seen)} indexed files and pack/index hashes.")
unresolved = json.loads((root / "UNRESOLVED.json").read_text(encoding="utf-8"))
if unresolved:
    print(
        f"WARNING: {len(unresolved)} downloads still need resolution; fresh installs are incomplete."
    )
    if "--release" in sys.argv:
        sys.exit(1)
