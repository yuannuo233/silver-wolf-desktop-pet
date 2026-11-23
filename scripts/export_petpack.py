"""Export the sprite set as a portable .petpack (see PROTOCOL.md, Level 1).

The pack is a directory that any engine can read: frames + one manifest. Nothing in it is
Tk- or Windows-specific, which is the whole point — the pet's artwork should outlive this app.

Usage (from the repo root):
    python scripts/export_petpack.py                    -> dist/silver-wolf.petpack/
    python scripts/export_petpack.py --zip              -> also writes .petpack.zip
"""

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAND = ROOT / "assets" / "stand"
SPEC = "pet-interop/1"

# Project state name -> standard name from PROTOCOL.md section 4.
ALIASES = {
    "typing": "type",
    "console": "game",
    "doze": "sleep",
    "lollipop": "eat",
}


def build_manifest(src: dict) -> dict:
    """Turn assets/stand/frames.json into a protocol-conformant pack.json."""
    sprite = src.get("sprite", {})
    states = {}
    for name, sdef in src["states"].items():
        frames = []
        for fr in sdef["frames"]:
            frames.append({
                "file": "frames/" + fr["file"],
                "duration_ms": fr["duration_ms"],
            })
        states[name] = {
            "loop": bool(sdef.get("loop", True)),
            "one_shot": not bool(sdef.get("loop", True)),
            "frames": frames,
        }

    return {
        "spec": SPEC,
        "id": "silver-wolf",
        "name": "银狼",
        "name_en": "Silver Wolf",
        "version": "0.6.17",
        "author": "yuannuo233",
        "license": "MIT (code) / fan-art (assets)",
        "attribution": "《崩坏：星穹铁道》非官方粉丝作品，不含游戏拆包素材。"
                       "Unofficial fan work; no game-ripped assets.",
        "homepage": "https://github.com/yuannuo233/silver-wolf-desktop-pet",
        "canvas": {
            "width": sprite.get("canvas_width", 190),
            "height": sprite.get("canvas_height", 216),
            "baseline_y": sprite.get("baseline_y", 210),
            "center_x": sprite.get("center_x", 95),
            "character_height": sprite.get("character_height", 200),
        },
        "alpha": {
            "mode": "binary",
            "threshold": 128,
            "key_color": "magenta",
        },
        "aliases": ALIASES,
        "states": states,
        "behavior": {
            "default": "idle",
            "rules": [
                {"when": "dragging", "state": "idle"},
                {"when": "moving", "state": "run_right", "mirror": "run_left"},
                {"when": "host.activity=type", "state": "typing"},
                {"when": "host.activity=game", "state": "console"},
            ],
            "one_shot": [n for n, s in states.items() if s["one_shot"]],
            "priority": ["dragging", "one_shot", "moving", "activity", "default"],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Export silver-wolf .petpack")
    ap.add_argument("--out", default=str(ROOT / "dist" / "silver-wolf.petpack"))
    ap.add_argument("--zip", action="store_true", help="also write <out>.zip")
    args = ap.parse_args()

    if not (STAND / "frames.json").exists():
        print("!! assets/stand/frames.json not found; run from the repo root")
        return 1

    src = json.loads((STAND / "frames.json").read_text(encoding="utf-8"))
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "frames").mkdir(parents=True)

    copied = 0
    for sdef in src["states"].values():
        for fr in sdef["frames"]:
            s = STAND / fr["file"]
            if s.exists():
                shutil.copy2(s, out / "frames" / fr["file"])
                copied += 1

    manifest = build_manifest(src)
    (out / "pack.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    for extra in ("DISCLAIMER.md",):
        p = ROOT / extra
        if p.exists():
            shutil.copy2(p, out / "LICENSE.md")

    total_states = len(manifest["states"])
    print("packed %d frames / %d states -> %s" % (copied, total_states, out))

    if args.zip:
        zpath = out.with_suffix(out.suffix + ".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(out))
        print("zip -> %s (%.1f MB)" % (zpath, zpath.stat().st_size / 1048576))

    return 0


if __name__ == "__main__":
    sys.exit(main())
