"""Central config for the remote-job-finder pipeline.

Everything USER-SPECIFIC (resume, target role keywords, which LLM to run,
email address) lives in data/settings.json + data/.env, written by
`python setup.py` — not in this file. That's what makes the project portable:
a new person runs the wizard once and gets their own version of this pipeline
without editing any code. This file only holds things that are the same for
everyone (source URLs) plus the loader that pulls in their settings.
"""
from pathlib import Path

from settings import load_settings

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
SEEN_JOBS_FILE = DATA_DIR / "seen_jobs.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
ENV_FILE = DATA_DIR / ".env"

_settings = load_settings(SETTINGS_FILE)

# Path to the resume this pipeline drafts against. Falls back to
# data/resume.md (copied there by setup.py) if settings.json doesn't
# override it with an absolute path elsewhere.
RESUME_PATH = Path(_settings["resume_path"]) if _settings["resume_path"] else DATA_DIR / "resume.md"

# Ollama config — model name is the user's choice, set by setup.py.
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = _settings["ollama_model"]

# Email config
EMAIL_ON_COMPLETION = True

# Filtering — the user's chosen preset or custom keywords, from setup.py.
INCLUDE_KEYWORDS = _settings["include_keywords"]
EXCLUDE_TITLE_KEYWORDS = _settings["exclude_title_keywords"]

# Company slugs to poll on Greenhouse / Lever / Ashby, set by setup.py (optional).
GREENHOUSE_COMPANIES: list[str] = _settings["greenhouse_companies"]
LEVER_COMPANIES: list[str] = _settings["lever_companies"]
ASHBY_COMPANIES: list[str] = _settings["ashby_companies"]

# --- Sources (same for every user; public feeds, no keys needed) -----------

WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    # WWR's data-jobs category slug changes over time and 403s bots when
    # wrong; data-analyst roles still surface via keyword match on the
    # programming feed + RemoteOK/Himalayas. Re-add here if you confirm the
    # current slug at https://weworkremotely.com/remote-jobs.
]

REMOTEOK_API = "https://remoteok.com/api"
HIMALAYAS_API = "https://himalayas.app/jobs/api?limit=40"
REMOTIVE_API = "https://remotive.com/api/remote-jobs?category=software-dev"
JOBICY_API = "https://jobicy.com/api/v2/remote-jobs?count=50&industry=dev"
ARBEITNOW_API = "https://www.arbeitnow.com/api/job-board-api"

# Require "remote" to appear somewhere (title, location or description) unless
# the source is remote-only by definition.
REMOTE_ONLY_SOURCES = {"weworkremotely", "remoteok", "himalayas", "remotive", "jobicy"}
