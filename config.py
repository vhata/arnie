"""Configuration loading, saving, and validation for Arnie."""

import json
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "config.json"

DEFAULTS = {
    "start_hour": 10,
    "end_hour": 19,
    "frequency_minutes": 30,
    "tier_days": [14, 14],
    "sound": "Ping",
}


def load_config() -> dict:
    """Load config from config.json, falling back to defaults for missing keys."""
    config = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        user = json.loads(CONFIG_FILE.read_text())
        for key in DEFAULTS:
            if key in user:
                config[key] = user[key]
    return config


def save_config(config: dict):
    """Write config to config.json (atomic write)."""
    # Only save keys that are in DEFAULTS
    to_save = {k: config[k] for k in DEFAULTS if k in config}
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(to_save, indent=2) + "\n")
    tmp.replace(CONFIG_FILE)


def validate_config(config: dict) -> list[str]:
    """Return a list of validation errors, empty if valid."""
    errors = []
    sh = config.get("start_hour")
    eh = config.get("end_hour")
    freq = config.get("frequency_minutes")
    td = config.get("tier_days")
    sound = config.get("sound")

    if not isinstance(sh, int) or not 0 <= sh <= 23:
        errors.append(f"start_hour must be 0-23, got {sh!r}")
    if not isinstance(eh, int) or not 0 <= eh <= 23:
        errors.append(f"end_hour must be 0-23, got {eh!r}")
    if isinstance(sh, int) and isinstance(eh, int) and sh >= eh:
        errors.append(f"start_hour ({sh}) must be before end_hour ({eh})")
    if not isinstance(freq, int) or freq < 1:
        errors.append(f"frequency_minutes must be a positive integer, got {freq!r}")
    if not isinstance(td, list) or not td or not all(isinstance(d, int) and d > 0 for d in td):
        errors.append(f"tier_days must be a non-empty list of positive integers, got {td!r}")
    if not isinstance(sound, str) or not sound:
        errors.append(f"sound must be a non-empty string, got {sound!r}")

    return errors
