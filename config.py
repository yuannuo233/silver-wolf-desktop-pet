"""Pet settings persistence.

Stored as a small JSON file under %APPDATA%\\SilverWolfPet\\ so it works
the same for source runs and packaged exe builds, and survives updates.
"""

import json
import os
from pathlib import Path

from prompts import PROMPTS

CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "SilverWolfPet"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "base_url": "",          # OpenAI-compatible endpoint, e.g. https://api.deepseek.com/v1
    "api_key": "",           # kept on this machine only, never uploaded
    "model": "",
    "prompt_text": PROMPTS["平衡版"],   # active persona prompt (editable)
    "size_height": 200,      # sprite height in px
    "theme": "light",        # UI theme: light / dark / cyber
    # Set to True once the first-run terms notice has been shown (see main.py).
    "terms_seen": False,
    # Follow my activity: keystrokes in any app -> pet types; a game in front -> pet plays handheld.
    "follow_activity": True,
    # Check GitHub for a newer release on startup. On by default so update notices reach the
    # people who already downloaded the exe (they are invisible to GitHub otherwise).
    "check_updates": True,
    # Tag the user has already been told about, so the same release is announced only once.
    "update_dismissed": "",
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # first run / broken file -> fall back to defaults
    return cfg


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )
