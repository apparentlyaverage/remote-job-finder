"""Per-user, non-secret settings, written by setup.py into data/settings.json.

Kept separate from data/.env (which holds only the email credential) so the
settings file can be committed/shared/backed up without any secret in it.
"""
from __future__ import annotations

import json
from pathlib import Path

from keyword_presets import DEFAULT_PRESET, PRESETS

DEFAULTS = {
    "resume_path": "",  # filled in by setup.py; falls back to data/resume.md
    "ollama_model": "gemma3:4b",
    "include_keywords": PRESETS[DEFAULT_PRESET]["include"],
    "exclude_title_keywords": PRESETS[DEFAULT_PRESET]["exclude_title"],
    "greenhouse_companies": [],
    "lever_companies": [],
    "ashby_companies": [],
}


def load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save_settings(settings_path: Path, settings: dict) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
