"""Loads the CV markdown and exposes it as modular chunks Gemma can pick from.

The CV is a single markdown file with '## Heading' sections. We split on
those so the LLM prompt can include a condensed profile + skills, plus the
full project list, without re-parsing the file per job.
"""
from __future__ import annotations

import re
from pathlib import Path


def load_resume_sections(resume_path: Path) -> dict[str, str]:
    text = resume_path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current = "header"
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*)", line)
        if m:
            sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf).strip()
    return sections


PREFERRED_SECTIONS = (
    "profile", "summary", "about", "technical skills", "skills",
    "selected projects", "projects", "work experience", "experience",
)


def build_resume_context(resume_path: Path, max_chars: int = 4000) -> str:
    """A condensed profile+skills+projects blob to feed the LLM per job.

    Keeps prompt size sane rather than dumping the whole CV every call.

    Not every resume uses '## Profile' / '## Technical Skills' / '## Selected
    Projects' headings the way this one does — those were tuned for one
    person's CV. If none of the preferred section names are found (e.g. a
    resume with different headings, or no '##' headings at all), this falls
    back to the whole document, truncated, so the pipeline still works
    reasonably for someone else's resume instead of silently sending Gemma
    an empty context.
    """
    sections = load_resume_sections(resume_path)
    parts = []
    for key in PREFERRED_SECTIONS:
        if key in sections and sections[key]:
            parts.append(f"### {key.title()}\n{sections[key]}")

    if parts:
        context = "\n\n".join(parts)
    else:
        context = resume_path.read_text(encoding="utf-8").strip()

    if len(context) > max_chars:
        context = context[:max_chars] + "\n...[truncated]"
    return context
