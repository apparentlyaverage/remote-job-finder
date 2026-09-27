"""Builds the daily reviewable markdown report."""
from __future__ import annotations

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
