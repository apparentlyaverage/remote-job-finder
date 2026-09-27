"""One-time interactive setup wizard for a new user of this pipeline.

Run this once (`python setup.py`), answer a few questions, and get the same
daily remote-job pipeline the original build was made for — your own resume,
your own choice of local LLM, your own filter, your own inbox. Nothing here
talks to any external service except the ones you explicitly point it at
(Ollama on your own machine, Gmail's SMTP with your own app password).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from keyword_presets import PRESETS  # noqa: E402
from settings import DEFAULTS, load_settings, save_settings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
ENV_FILE = DATA_DIR / ".env"
RESUME_DEST = DATA_DIR / "resume.md"


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or (default or "")


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    default_str = "Y/n" if default_yes else "y/N"
    answer = input(f"{prompt} ({default_str}): ").strip().lower()
    if not answer:
        return default_yes
    return answer.startswith("y")


def choose_preset() -> tuple[list[str], list[str]]:
    print("\nWhich kind of roles are you targeting? Pick a preset, or 'custom' to type your own.")
    names = list(PRESETS.keys())
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")
    print(f"  {len(names) + 1}. custom")

    choice = ask("Enter a number", "1")
    try:
        idx = int(choice)
    except ValueError:
        idx = 1

    if 1 <= idx <= len(names):
        preset = PRESETS[names[idx - 1]]
        return list(preset["include"]), list(preset["exclude_title"])

    # custom
    print("\nEnter phrases that must appear in a job TITLE to count as a match.")
    print("Comma-separated, e.g.: marketing coordinator, content marketing, marketing intern")
    include_raw = ask("Include phrases")
    include = [s.strip() for s in include_raw.split(",") if s.strip()]

    print("\nEnter words that, if in the title, exclude a job outright (seniority, etc).")
    print("Comma-separated, e.g.: senior, director, manager")
    exclude_raw = ask("Exclude phrases", "senior, staff, director, manager")
    exclude = [s.strip() for s in exclude_raw.split(",") if s.strip()]
    return include, exclude


def setup_resume() -> str:
    print("\n--- Resume ---")
    print("Point me at your resume (.md or .txt works best; PDF/.docx aren't parsed).")
    while True:
        raw = ask("Path to your resume file")
        if not raw:
            print("A resume path is required.")
            continue
        path = Path(raw).expanduser()
        if not path.exists():
            print(f"Couldn't find {path}. Try again.")
            continue
        break

    if ask_yes_no(f"Copy it into {RESUME_DEST} so this project is self-contained?", True):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, RESUME_DEST)
        print(f"Copied to {RESUME_DEST}")
        return ""  # empty -> config.py falls back to data/resume.md
    return str(path)


def setup_ollama_model() -> str:
    print("\n--- Local LLM (via Ollama) ---")
    print("Any Ollama model works. Larger = better writing, slower + more disk/RAM.")
    print("Examples: gemma3:1b (fast, ~1GB), gemma3:4b (balanced, ~3.3GB), gemma2:9b (~5.4GB)")
    model = ask("Ollama model name", "gemma3:4b")

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=15)
        have_it = model in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("Couldn't run `ollama list` — make sure Ollama is installed and on your PATH.")
        have_it = False

    if not have_it:
        if ask_yes_no(f"'{model}' isn't installed yet. Pull it now? (this downloads several GB)", True):
            subprocess.run(["ollama", "pull", model])
        else:
            print(f"OK — run `ollama pull {model}` yourself before the pipeline can use it.")
    return model


def setup_email() -> None:
    print("\n--- Email notifications ---")
    if not ask_yes_no("Set up email notifications now?", True):
        print("Skipping — you can copy data/.env.example to data/.env later.")
        return

    print("You'll need a Gmail App Password (not your normal password):")
    print("  1. Turn on 2-Step Verification: myaccount.google.com/security")
    print("  2. Generate one at: myaccount.google.com/apppasswords")
    sender = ask("Gmail address to send FROM")
    recipient = ask("Email address to send TO", sender)
    app_password = ask("App password (16 characters, spaces don't matter)")
    app_password = app_password.replace(" ", "")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(
        f"GMAIL_APP_PASSWORD={app_password}\n"
        f"GMAIL_SENDER={sender}\n"
        f"GMAIL_RECIPIENT={recipient}\n",
        encoding="utf-8",
    )
    print(f"Saved to {ENV_FILE} (gitignored — never committed).")


def main() -> None:
    print("=== remote-job-finder setup ===\n")
    existing = load_settings(SETTINGS_FILE) if SETTINGS_FILE.exists() else dict(DEFAULTS)

    resume_path = setup_resume()
    include_keywords, exclude_keywords = choose_preset()
    ollama_model = setup_ollama_model()

    settings = dict(existing)
    settings.update(
        {
            "resume_path": resume_path,
            "ollama_model": ollama_model,
            "include_keywords": include_keywords,
            "exclude_title_keywords": exclude_keywords,
        }
    )
    save_settings(SETTINGS_FILE, settings)
    print(f"\nSaved settings to {SETTINGS_FILE}")

    setup_email()

    print("\n=== Setup complete ===")
    print("Run the pipeline with:")
    print("    cd src")
    print("    python main.py")


if __name__ == "__main__":
    main()
