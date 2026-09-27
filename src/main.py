"""Daily pipeline entry point.

Fetch remote-job listings from ToS-friendly public feeds -> filter for roles
a second-year CS student could realistically land -> dedupe against what's
already been surfaced -> draft a tailored blurb per job with a local Gemma
model via Ollama -> write everything into one reviewable markdown report.

Nothing here submits an application. You still click submit, on-site,
yourself. Run this once a day (see README for the Windows Task Scheduler
setup), then read output/<today>.md end to end.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
import filters  # noqa: E402
import llm  # noqa: E402
import mailer  # noqa: E402
import report  # noqa: E402
import resume  # noqa: E402
import sources  # noqa: E402


def main() -> None:
    print("Fetching listings...")
    all_jobs = sources.fetch_all(config)
    print(f"  {len(all_jobs)} raw listings across all sources")

    matched = filters.filter_jobs(all_jobs, config.INCLUDE_KEYWORDS, config.EXCLUDE_TITLE_KEYWORDS)
    print(f"  {len(matched)} match your keyword filters")

    seen_ids = filters.load_seen(config.SEEN_JOBS_FILE)
    fresh = filters.dedupe_against_seen(matched, seen_ids)
    print(f"  {len(fresh)} are new since the last run")

    if not fresh:
        print("Nothing new today.")
        if config.EMAIL_ON_COMPLETION:
            ok, msg = mailer.send_status_email(
                config.ENV_FILE,
                subject="Remote job finder — no new matches today",
                body="Ran successfully. No new job matches since the last run.",
            )
            print(f"  Email: {msg}")
        return

    resume_context = resume.build_resume_context(config.RESUME_PATH)

    drafted = []
    for i, job in enumerate(fresh, 1):
        print(f"  Drafting {i}/{len(fresh)}: {job.title} @ {job.company}...")
        result = llm.draft_application(
            resume_context=resume_context,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            ollama_host=config.OLLAMA_HOST,
            model=config.OLLAMA_MODEL,
        )
        drafted.append({"job": job, **result})

    out_path = report.build_report(drafted, config.OUTPUT_DIR)
    print(f"\nReport written to {out_path}")

    seen_ids.update(job.id for job in fresh)
    filters.save_seen(config.SEEN_JOBS_FILE, seen_ids)
    print("Seen-jobs cache updated. Run again tomorrow for the next batch.")

    if config.EMAIL_ON_COMPLETION:
        ok, msg = mailer.send_report_email(out_path, config.ENV_FILE)
        print(f"  Email: {msg}")


if __name__ == "__main__":
    start = time.time()
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Pipeline crashed: {exc}")
        if config.EMAIL_ON_COMPLETION:
            mailer.send_status_email(
                config.ENV_FILE,
                subject="Remote job finder — run FAILED",
                body=f"The pipeline crashed with:\n\n{exc}\n\nCheck the machine when you're back.",
            )
        raise
    print(f"\nDone in {time.time() - start:.1f}s")
