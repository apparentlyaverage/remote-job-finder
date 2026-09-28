"""One-off (but reusable) utility: redrafts blurbs in output/jobs.json that
previously failed (e.g. "[LLM error: timed out]" from a run where the LLM
couldn't keep up).

Job entries in jobs.json don't store the original posting description (only
title/company/location/url), so a proper redraft needs it back. This
re-fetches the same public feeds fresh, matches each broken entry by
(title, company), and redrafts it with the real description if the posting
is still listed. Postings that have since expired off the job boards can't
be improved this way and are left as-is, clearly reported at the end.

Run standalone: `python backfill_blurbs.py`
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
import llm  # noqa: E402
import resume  # noqa: E402
import sources  # noqa: E402


def _key(title: str, company: str) -> tuple[str, str]:
    return (title.strip().lower(), company.strip().lower())


def is_broken(entry: dict) -> bool:
    blurb = (entry.get("blurb") or "").strip()
    return not blurb or blurb.startswith("[LLM error")


def main() -> None:
    jobs_json_path = config.OUTPUT_DIR / "jobs.json"
    if not jobs_json_path.exists():
        print(f"No {jobs_json_path} found — nothing to backfill.")
        return

    entries = json.loads(jobs_json_path.read_text(encoding="utf-8"))
    broken = [e for e in entries if is_broken(e)]
    print(f"{len(entries)} total entries, {len(broken)} need redrafting.")
    if not broken:
        return

    print("Fetching current listings to recover descriptions...")
    fresh_jobs = sources.fetch_all(config)
    lookup = {}
    for job in fresh_jobs:
        k = _key(job.title, job.company)
        lookup.setdefault(k, job)  # first match wins if duplicates
    print(f"  {len(fresh_jobs)} listings fetched, {len(lookup)} unique (title, company) pairs.")

    resume_context = resume.build_resume_context(config.RESUME_PATH)

    redrafted = 0
    expired = 0
    still_failed = 0

    for i, entry in enumerate(broken, 1):
        k = _key(entry["title"], entry["company"])
        job = lookup.get(k)
        if job is None:
            expired += 1
            entry["blurb"] = "[Listing no longer available — expired off the job board, can't redraft]"
            print(f"  [{i}/{len(broken)}] EXPIRED: {entry['title']} @ {entry['company']}")
            continue

        print(f"  [{i}/{len(broken)}] Redrafting: {entry['title']} @ {entry['company']}...")
        result = llm.draft_application(
            resume_context=resume_context,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            ollama_host=config.OLLAMA_HOST,
            model=config.OLLAMA_MODEL,
        )
        entry["fit"] = result["fit"]
        entry["resume_angle"] = result["resume_angle"]
        entry["blurb"] = result["blurb"]
        if result["blurb"].startswith("[LLM error"):
            still_failed += 1
        else:
            redrafted += 1

    jobs_json_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(
        f"\nDone. {redrafted} redrafted successfully, "
        f"{expired} expired (listing gone), {still_failed} still failed."
    )
    print(f"Updated {jobs_json_path}")


if __name__ == "__main__":
    start = time.time()
    main()
    print(f"\nTook {time.time() - start:.1f}s")
