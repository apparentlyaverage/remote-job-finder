"""Local Gemma calls via Ollama's HTTP API (no external network calls,
no API keys — everything stays on this machine).
"""
from __future__ import annotations

import json
import re
import urllib.request

PROMPT_TEMPLATE = """You are helping a second-year BSc Computer Science student in South Africa \
apply to REMOTE jobs quickly. Below is a condensed version of their resume, followed by a job \
posting. Do three things, and ONLY these three, in the exact plain-text format shown — no \
markdown, no asterisks, no headers, just the three lines below with your answer after each colon:

FIT: <a single digit 1-5, 5 = strong fit, 1 = weak fit, based on skills/seniority match>
RESUME_ANGLE: <one sentence: which resume project/skill to lead with for this specific job>
BLURB: <a tailored 3-4 sentence cover-letter paragraph, first person, specific to this job, \
mentioning one concrete detail from the resume that matches what the job asks for. No greeting \
or sign-off, just the paragraph, all on one line.>

--- RESUME ---
{resume}

--- JOB POSTING ---
Title: {title}
Company: {company}
Location: {location}
Description:
{description}
--- END ---

Respond with exactly those three lines (FIT:, RESUME_ANGLE:, BLURB:) and nothing else — no
markdown formatting, no extra commentary before or after.
"""

# Tolerant of a weaker model's looser formatting: markdown bold/heading
# markers around the label, a missing colon, or the label and value split
# across lines instead of on one line.
_HEADER_RE = re.compile(
    r"^[\*#\s]*(FIT|RESUME[_ ]ANGLE|BLURB)[\*#\s]*:?[\*#\s]*(.*)$",
    re.IGNORECASE,
)
_LABEL_KEY = {"FIT": "fit", "RESUME_ANGLE": "angle", "RESUME ANGLE": "angle", "BLURB": "blurb"}


def draft_application(
    resume_context: str,
    title: str,
    company: str,
    location: str,
    description: str,
    ollama_host: str,
    model: str,
    timeout: int = 90,
) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        resume=resume_context,
        title=title,
        company=company,
        location=location or "Remote",
        description=description[:3000],
    )
    payload = json.dumps(
        {"model": model, "prompt": prompt, "stream": False}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{ollama_host}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        return {"fit": None, "resume_angle": "", "blurb": f"[LLM error: {exc}]"}

    raw_text = body.get("response", "")
    return _parse_response(raw_text)


def _parse_response(text: str) -> dict:
    sections: dict[str, list[str]] = {"fit": [], "angle": [], "blurb": []}
    current: str | None = None

    for raw_line in text.strip().splitlines():
        m = _HEADER_RE.match(raw_line)
        if m:
            label = m.group(1).upper().replace("  ", " ")
            key = _LABEL_KEY.get(label)
            if key:
                current = key
                remainder = m.group(2).strip()
                if remainder:
                    sections[current].append(remainder)
                continue
        # Not a header line — if we're inside a section, keep collecting it.
        # (Blank lines between sections are just skipped, not appended.)
        if current and raw_line.strip():
            sections[current].append(raw_line.strip())

    fit_raw = " ".join(sections["fit"])
    digits = "".join(c for c in fit_raw if c.isdigit())
    fit = int(digits[0]) if digits else None

    angle = " ".join(sections["angle"]).strip()
    blurb = " ".join(sections["blurb"]).strip()

    if not blurb:
        # Model didn't follow the format at all — fall back to the raw text
        # rather than silently returning nothing.
        blurb = text.strip()

    return {"fit": fit, "resume_angle": angle, "blurb": blurb}
