"""Build a Minecraft 1.21.1 filter pack for the inspected AMBUSH JAR.

Usage: py -3 tools/build_ambush_vehicle_filter.py path/to/ambush.jar
Review the generated report whenever upgrading AMBUSH; new IDs are not blocked
until the filter is rebuilt. Does not edit the packwiz index.
"""

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "moonlight-global-datapacks/deboys-ambush-vehicles-only.zip"
REPORT = ROOT / "tools/ambush-vehicle-filter-report.json"
VEHICLE_ACTIONS = {"sable_structure", "sable_formation", "sable_car", "sable_boat"}


def build(source):
    with zipfile.ZipFile(source) as jar:
        definitions = {
            name.removeprefix("data/ambush/ambushes/").removesuffix(
                ".json"
            ): json.loads(jar.read(name))
            for name in jar.namelist()
            if name.startswith("data/ambush/ambushes/") and name.endswith(".json")
        }
        profiles = {
            "ambush:"
            + name.removeprefix("data/ambush/ambush_ship_profiles/").removesuffix(
                ".json"
            ): json.loads(jar.read(name))
            for name in jar.namelist()
            if name.startswith("data/ambush/ambush_ship_profiles/")
            and name.endswith(".json")
        }

    def merge(base, overrides):
        result = dict(base)
        for key, value in overrides.items():
            if value is None:
                result.pop(key, None)
            elif isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = merge(result[key], value)
            else:
                result[key] = value
        return result

    def resolve_profile(name, visiting):
        if name not in profiles:
            raise ValueError(f"Unknown ship profile: {name}")
        if name in visiting:
            raise ValueError(f"Cyclic ship profile: {name}")
        profile = profiles[name]
        if "extends" in profile:
            action = resolve_profile(profile["extends"], visiting | {name})
        else:
            action = profile["action"]
        return merge(action, profile.get("overrides", {}))

    def has_vehicle(value, visiting=frozenset()):
        if isinstance(value, list):
            return any(has_vehicle(item, visiting) for item in value)
        if not isinstance(value, dict):
            return False
        if value.get("type") in VEHICLE_ACTIONS:
            return True
        if value.get("type") == "profile":
            name = value["profile"]
            action = merge(resolve_profile(name, visiting), value.get("overrides", {}))
            if has_vehicle(action, visiting | {name}):
                return True
        return any(has_vehicle(item, visiting) for item in value.values())

    blocked = sorted(
        name for name, data in definitions.items() if not has_vehicle(data)
    )
    preserved = sorted(set(definitions) - set(blocked))
    assert blocked and preserved, (
        "Unexpected encounter classification; review AMBUSH format"
    )
    assert "_normal_night_skeleton_barrage" in blocked
    assert "_normal_underground_speed_skeletons" in blocked
    assert "_rare_thunder_bone_tempest_raid" in blocked
    assert "_grapeshot_raid_ship" in preserved
    assert "_autocannon_pillager_car" in preserved
    assert "_illager_saw_car_berries" in preserved
    assert "_illager_saw_car_cannon" in preserved
    assert "_illager_saw_nozzle_car" in preserved
    metadata = {
        "pack": {
            "pack_format": 48,
            "description": "Deboys: AMBUSH vehicle encounters only (AMBUSH 1.1.8)",
        },
        "filter": {
            "block": [
                {
                    "namespace": "ambush",
                    "path": "ambushes/" + re.escape(name) + r"\.json",
                }
                for name in blocked
            ],
        },
    }
    patterns = [re.compile(item["path"]) for item in metadata["filter"]["block"]]
    for name in definitions:
        matches = any(
            pattern.fullmatch("ambushes/" + name + ".json") for pattern in patterns
        )
        assert matches == (name in blocked), f"Incorrect filter: {name}"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Fixed timestamps make identical source definitions produce identical ZIPs.
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as out:
        entry = zipfile.ZipInfo("pack.mcmeta", (2026, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        out.writestr(entry, json.dumps(metadata, indent=2) + "\n")
    report = {
        "source_jar": source.name,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "blocked_without_vehicles": blocked,
        "preserved_with_vehicles": preserved,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Blocked {len(blocked)} vehicle-free encounters; preserved {len(preserved)} vehicle encounters."
    )
    print(OUTPUT)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    build(Path(sys.argv[1]))
