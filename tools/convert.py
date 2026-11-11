"""Rebuild a separate packwiz source from the adjacent Prism instance (Python 3.11+)."""

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

import tomllib

PACK = Path(__file__).resolve().parents[1]
SOURCE = PACK.parent


def quote(value):
    return json.dumps(str(value), ensure_ascii=False)


def digest(path, algorithm="sha256"):
    return hashlib.file_digest(path.open("rb"), algorithm).hexdigest()


def main():
    metadata = {}
    for path in (SOURCE / "mods/.index").glob("*.pw.toml"):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        metadata[data["filename"]] = (path, data)
    unresolved = []
    matched = 0
    for folder, pattern in [
        ("mods", "*.jar"),
        ("resourcepacks", "*.zip"),
        ("shaderpacks", "*.zip"),
    ]:
        target = PACK / folder
        target.mkdir(exist_ok=True)
        # Only remove generated manifests, never the source instance files.
        for old in target.glob("*.pw.toml"):
            old.unlink()
        pending = {}
        for path in sorted((SOURCE / folder).glob(pattern)):
            entry = metadata.get(path.name) if folder == "mods" else None
            if (
                entry
                and digest(path, entry[1]["download"]["hash-format"])
                == entry[1]["download"]["hash"]
            ):
                text = entry[0].read_text(encoding="utf-8")
                if entry[1].get("side") not in ("client", "server", "both"):
                    text = text.replace("side = ''", "side = 'both'")
                (target / entry[0].name).write_text(text, encoding="utf-8")
                matched += 1
            else:
                pending[digest(path, "sha512")] = path
        if pending:
            request = urllib.request.Request(
                "https://api.modrinth.com/v2/version_files",
                data=json.dumps(
                    {"hashes": list(pending), "algorithm": "sha512"}
                ).encode(),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Deboys-Packwiz-Conversion/1.0",
                },
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                versions = json.load(response)
            for hash_value, path in pending.items():
                version = versions.get(hash_value)
                if not version:
                    unresolved.append(
                        {
                            "file": f"{folder}/{path.name}",
                            "sha512": hash_value,
                            "reason": "No verified public download; supply a permitted URL with packwiz url add, or install manually.",
                        }
                    )
                    continue
                download = next(
                    f for f in version["files"] if f["hashes"]["sha512"] == hash_value
                )
                text = f'name = {quote(path.stem)}\nfilename = {quote(path.name)}\nside = "client"\n\n[download]\nurl = {quote(download["url"])}\nhash-format = "sha512"\nhash = {quote(hash_value)}\n\n[update.modrinth]\nmod-id = {quote(version["project_id"])}\nversion = {quote(version["id"])}\n'
                (target / (path.name + ".pw.toml")).write_text(text, encoding="utf-8")
                matched += 1
    config_target = PACK / "config"
    if config_target.exists():
        shutil.rmtree(config_target)
    shutil.copytree(
        SOURCE / "config",
        config_target,
        ignore=shutil.ignore_patterns("*.log", "*.bak", "*.old"),
    )
    # Voice-chat server settings may contain a password; do not publish them by default.
    for path in config_target.rglob("voicechat-server.properties"):
        path.unlink()
    (PACK / "UNRESOLVED.json").write_text(
        json.dumps(unresolved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    refresh()
    print(
        f"Converted {matched} downloads; {len(unresolved)} require review. See UNRESOLVED.json."
    )


def refresh():
    entries = ['hash-format = "sha256"\n']
    for folder in ["mods", "resourcepacks", "shaderpacks", "config"]:
        for path in sorted((PACK / folder).rglob("*")):
            if path.is_file():
                entries.append(
                    f"\n[[files]]\nfile = {quote(path.relative_to(PACK).as_posix())}\nhash = {quote(digest(path))}\n"
                    + ("metafile = true\n" if path.name.endswith(".pw.toml") else "")
                )
    index = PACK / "index.toml"
    index.write_text("".join(entries), encoding="utf-8")
    (PACK / "pack.toml").write_text(
        f'name = "Deboys 7.0"\nauthor = "Deboys"\nversion = "7.0.0"\npack-format = "packwiz:1.1.0"\n\n[index]\nfile = "index.toml"\nhash-format = "sha256"\nhash = "{digest(index)}"\n\n[versions]\nminecraft = "1.21.1"\nneoforge = "21.1.265"\n',
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
