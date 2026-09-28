# remote-job-finder

Daily pipeline that finds remote jobs worth applying to and drafts a tailored
cover blurb for each one using a local Gemma model (via Ollama) — so the
end-of-day review is "read and click submit," not "write from scratch."

**This tool never submits an application for you.** It reads public,
automation-tolerant job feeds — We Work Remotely (RSS), RemoteOK, Himalayas,
Remotive, Jobicy, and Arbeitnow (all public JSON APIs, no key needed), plus
any Greenhouse/Lever/Ashby company boards you list — drafts a blurb per new
match, and writes it all into a markdown report and a PWA dashboard for you
to read and act on yourself. Deliberately does **not** touch LinkedIn —
LinkedIn's ToS prohibits automated interaction with the platform and bans
accounts that do it.

Remotive's API asks for max ~4 requests/day and a link back to the original
posting — this pipeline runs once daily and already links every job to its
real apply page, so both are satisfied by how it's built, not just by luck.

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
`lever_companies` / `ashby_companies` (found in a company's careers URL —
e.g. `boards.greenhouse.io/stripe` → `"stripe"`, `jobs.ashbyhq.com/notion` →
`"notion"`) to also poll their own ATS boards directly, on top of the
public feeds.

## Run

```bash
cd src
python main.py
```

Writes `output/<today>.md` with every new match: title, company, source,
apply link, which resume angle to lead with, and a drafted cover-letter
paragraph. Re-running the same day (or after) skips jobs already surfaced —
tracked in `data/seen_jobs.json`.

## Dashboard (PWA)

```bash
cd src
python serve_pwa.py
```

Opens a local dashboard at `http://localhost:8787` — every match ever
surfaced (not just today's), sortable by fit score or date, filterable by
applied/not-applied, with a copy-blurb button and an Apply button that opens
the real posting in a new tab (not embedded — most ATS/company career pages
block being framed, so this is the version that actually works everywhere).
Install it from your browser's install prompt for an app-like experience.
It's local-only: binds to `localhost`, nothing leaves your machine except
your own browser talking to it.

"Applied" status is stored in your browser's local storage — per-browser,
not synced, and not backed up anywhere. That's an intentional trade-off to
keep this stdlib-only with no database.

### Follow-up reminders

Marking a job "applied" timestamps it. 24 hours later it surfaces under
**Show: follow-up due** with a drafted follow-up email (subject + body,
using your name from the "Your name" field and, if the job had one, a line
pulled from its résumé angle). Nothing sends automatically — you either
copy the text or add the company's contact email to get a pre-filled
`mailto:` link that opens your own mail client for you to review and send.
Most job-board postings don't include a direct contact email, so the
email field is optional and the copy button is the reliable fallback.

## Fixing broken drafts after a bad run

If a run's blurbs come back as `[LLM error: ...]` (e.g. the model timed out,
ran out of RAM, or Ollama wasn't running), `python backfill_blurbs.py`
re-fetches the source feeds fresh, matches broken entries by title+company,
and redrafts anything still listed. Postings that have expired off the job
boards since get clearly marked as such rather than silently left broken.

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
