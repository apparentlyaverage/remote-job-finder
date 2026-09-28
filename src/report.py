"""Builds the daily reviewable markdown report, plus a JSON data file the
PWA dashboard reads. The JSON file accumulates every match ever surfaced
(deduped by job id, same as the seen-jobs cache) rather than being
overwritten each run, so the dashboard shows an ongoing list you can work
through across days, not just today's batch.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def build_report(drafted_jobs: list[dict], output_dir: Path) -> Path:
    """drafted_jobs: list of {job: Job, fit, resume_angle, blurb}"""
    today = date.today().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{today}.md"

    # Highest fit first, unscored last
    drafted_jobs = sorted(
        drafted_jobs, key=lambda d: (d["fit"] if d["fit"] is not None else -1), reverse=True
    )

    lines = [f"# Remote job matches — {today}", "", f"{len(drafted_jobs)} new match(es) today.", ""]
    for d in drafted_jobs:
        job = d["job"]
        fit = d["fit"]
        fit_str = f"{fit}/5" if fit is not None else "unscored"
        lines.append(f"## {job.title} — {job.company} ({fit_str})")
        lines.append(f"- **Source:** {job.source}  ·  **Location:** {job.location or 'Remote'}")
        lines.append(f"- **Apply here:** {job.url}")
        if d["resume_angle"]:
            lines.append(f"- **Lead with:** {d['resume_angle']}")
        lines.append("")
        lines.append("**Drafted cover blurb** (edit before use):")
        lines.append("")
        lines.append(f"> {d['blurb']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def append_json(drafted_jobs: list[dict], output_dir: Path, jobs_json_path: Path | None = None) -> Path:
    """Appends today's drafted matches to output/jobs.json (deduped by job
    id), for the PWA dashboard. Returns the path written.
    """
    today = date.today().isoformat()
    jobs_json_path = jobs_json_path or output_dir / "jobs.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if jobs_json_path.exists():
        try:
            existing = json.loads(jobs_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    existing_ids = {e.get("id") for e in existing}

    for d in drafted_jobs:
        job = d["job"]
        if job.id in existing_ids:
            continue
        existing.append(
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "source": job.source,
                "location": job.location or "Remote",
                "url": job.url,
                "fit": d["fit"],
                "resume_angle": d["resume_angle"],
                "blurb": d["blurb"],
                "date_found": today,
            }
        )
        existing_ids.add(job.id)

    jobs_json_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return jobs_json_path
