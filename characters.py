"""Character packs: tells the app which sprite set and persona to load.

Before this module the app was single-character: the name "银狼", the sprite paths and the
frame directory were all hard-coded. Adding a second character meant editing several files,
so they are collected here instead.

A character is just a folder under `characters/`:

    characters/
      silver_wolf/            <- id, also the value stored in config["character"]
        character.json        <- name, sprite, hd_sprite, stand (frame dir)
        stand/                <- frames.json + *.png
      silver_wolf_lv999/
        character.json
        stand/

Dropping in a new folder is enough — no code change, no hard-coded list to keep in sync.
Missing or broken packs fall back to the built-in default so the pet always starts.
"""

import json
from pathlib import Path

# The original character. Its sprites live in assets/, not under characters/, because that is
# where every earlier release put them and moving them would break existing installs.
DEFAULT_ID = "silver_wolf"
DEFAULT_SPEC = {
    "name": "银狼",
    "sprite": "assets/silver_wolf.png",
    "hd_sprite": "assets/silver_wolf_hd.png",
    "stand": "assets/stand",
    "persona": "",          # empty -> use the prompt from prompts.py as before
}


def _root() -> Path:
    return Path(__file__).resolve().parent


def _read_spec(folder: Path) -> dict:
    """Read one character.json and resolve its paths against the app root."""
    try:
        raw = json.loads((folder / "character.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}

    spec = dict(DEFAULT_SPEC)
    spec.update({k: v for k, v in raw.items() if v not in (None, "")})
    # Paths in the json are relative to the app root; resolve them once here so callers never
    # have to care where the working directory is.
    for key in ("sprite", "hd_sprite", "stand"):
        if spec.get(key):
            spec[key] = str((_root() / spec[key]).resolve()) if not Path(spec[key]).is_absolute() \
                else spec[key]
    spec["id"] = folder.name
    return spec


def list_characters() -> list:
    """Every available character, default first.

    Each entry: {id, name, sprite, hd_sprite, stand, persona}. Unreadable folders are skipped.
    """
    out = []
    default = dict(DEFAULT_SPEC)
    default["id"] = DEFAULT_ID
    for key in ("sprite", "hd_sprite", "stand"):
        default[key] = str((_root() / default[key]).resolve())
    out.append(default)

    base = _root() / "characters"
    if base.is_dir():
        for folder in sorted(base.iterdir()):
            if not folder.is_dir():
                continue
            spec = _read_spec(folder)
            if spec and spec.get("name"):
                out.append(spec)
    return out


def get(character_id: str) -> dict:
    """Look one up by id, falling back to the default when it is unknown."""
    for spec in list_characters():
        if spec["id"] == character_id:
            return spec
    return list_characters()[0]


def default_id() -> str:
    return DEFAULT_ID
