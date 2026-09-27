# remote-job-finder

Daily pipeline that finds remote jobs worth applying to and drafts a tailored
cover blurb for each one using a local Gemma model (via Ollama) — so the
end-of-day review is "read and click submit," not "write from scratch."

**This tool never submits an application for you.** It reads public,
automation-tolerant job feeds (We Work Remotely RSS, RemoteOK's public API,
Himalayas' public API, and any Greenhouse/Lever company boards you list),
drafts a blurb per new match, and writes it all into one markdown file for
you to read and act on yourself. Deliberately does **not** touch LinkedIn —
LinkedIn's ToS prohibits automated interaction with the platform and bans
accounts that do it.

## Setup — new user

This project is portable: anyone can point it at their own resume, their own
choice of local LLM, and their own inbox without editing any code.

```bash
# 1. Install Ollama (https://ollama.com) if you haven't already.
# 2. No pip dependencies for the pipeline itself — stdlib only.
python --version   # 3.10+

# 3. Run the setup wizard.
cd src
python setup.py
```

The wizard asks for:
- **Your resume** (path to a `.md`/`.txt` file — it offers to copy it into
  `data/resume.md` so the project is self-contained)
- **Which roles you're targeting** — pick a built-in preset (software, data,
  marketing, customer support) or type custom title-matching phrases
- **Which local LLM to use** — any Ollama model name (`gemma3:1b`, `gemma3:4b`,
  `gemma2:9b`, whatever you have RAM/disk for); offers to `ollama pull` it
  for you if it's missing
- **Email** — your Gmail address + an App Password
  ([myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords),
  needs 2-Step Verification on) so you get the daily report by email

Everything it collects goes into `data/settings.json` (non-secret — resume
path, keywords, model name) and `data/.env` (the email credential — gitignored,
never committed, never leaves your machine except to Gmail's own SMTP server).

Re-run `python setup.py` anytime to change your resume, keywords, model, or
email — it won't overwrite anything you don't answer.

### Advanced: targeting specific companies

Open `data/settings.json` and add slugs to `greenhouse_companies` /
`lever_companies` (found in a company's careers URL — e.g.
`boards.greenhouse.io/stripe` → `"stripe"`) to also poll their own ATS boards
directly, on top of the public feeds.

## Run

```bash
cd src
python main.py
```

Writes `output/<today>.md` with every new match: title, company, source,
apply link, which resume angle to lead with, and a drafted cover-letter
paragraph. Re-running the same day (or after) skips jobs already surfaced —
tracked in `data/seen_jobs.json`.

## Schedule it daily

Windows Task Scheduler, same pattern as the morning-briefing project:

```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "main.py" -WorkingDirectory "C:\Users\tmkwa\OneDrive\Documents\remote-job-finder\src"
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00PM
Register-ScheduledTask -TaskName "RemoteJobFinder" -Action $action -Trigger $trigger -Description "Daily remote job scan + drafted blurbs"
```

Pick a time when Ollama will actually be running (it needs the app/service up).
Adjust the `-WorkingDirectory` to wherever you cloned this project.

## Tests

```bash
cd tests
python -m unittest discover
```

## Why not just auto-apply on LinkedIn?

- LinkedIn explicitly bans automated scraping/interaction; accounts doing it
  get banned, which kills the job search this is meant to speed up.
- Blind auto-submission produces generic applications that convert worse than
  a 30-second human-reviewed one — the bottleneck this tool removes is
  *drafting*, not *clicking*.
- Every source here is either a public API/RSS feed meant for this, or your
  own account acting on your own data on a site you're allowed to automate
  form-fill against for your own applications.
