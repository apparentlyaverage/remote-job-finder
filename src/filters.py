"""Keyword-based filtering and dedup against previously-seen jobs."""
from __future__ import annotations

import json
from pathlib import Path

from sources import Job


def matches(job: Job, include_keywords: list[str], exclude_title_keywords: list[str]) -> bool:
    title_lower = job.title.lower()
    for bad in exclude_title_keywords:
        if bad.lower() in title_lower:
            return False
    # Title-only on purpose: matching against the description too let generic
    # boilerplate ("entry-level friendly", "no experience needed") drag in
    # unrelated roles. A real tech-role phrase in the title is a much
    # stronger signal.
    return any(kw.lower() in title_lower for kw in include_keywords)


def filter_jobs(jobs: list[Job], include_keywords: list[str], exclude_title_keywords: list[str]) -> list[Job]:
    return [j for j in jobs if matches(j, include_keywords, exclude_title_keywords)]


def load_seen(seen_path: Path) -> set[str]:
    if not seen_path.exists():
        return set()
    try:
        return set(json.loads(seen_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(seen_path: Path, seen_ids: set[str]) -> None:
    seen_path.parent.mkdir(parents=True, exist_ok=True)
    seen_path.write_text(json.dumps(sorted(seen_ids), indent=2), encoding="utf-8")


def dedupe_against_seen(jobs: list[Job], seen_ids: set[str]) -> list[Job]:
    return [j for j in jobs if j.id not in seen_ids]
