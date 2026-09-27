"""Local Gemma calls via Ollama's HTTP API (no external network calls,
no API keys — everything stays on this machine).
"""
from __future__ import annotations

import json
import urllib.request

PROMPT_TEMPLATE = """You are helping a second-year BSc Computer Science student in South Africa \
apply to REMOTE jobs quickly. Below is a condensed version of their resume, followed by a job \
posting. Do three things, and ONLY these three, in the exact format shown:

FIT: <a number 1-5, 5 = strong fit, 1 = weak fit, based on skills/seniority match>
RESUME_ANGLE: <one sentence: which resume project/skill to lead with for this specific job>
BLURB: <a tailored 3-4 sentence cover-letter paragraph, first person, specific to this job, \
mentioning one concrete detail from the resume that matches what the job asks for. No greeting \
or sign-off, just the paragraph.>

--- RESUME ---
{resume}

--- JOB POSTING ---
Title: {title}
Company: {company}
Location: {location}
Description:
{description}
--- END ---

Respond in exactly the FIT/RESUME_ANGLE/BLURB format above, nothing else.
"""


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
    fit = None
    angle = ""
    blurb = ""
    lines = text.strip().splitlines()
    blurb_lines: list[str] = []
    mode = None
    for line in lines:
        if line.upper().startswith("FIT:"):
            mode = None
            raw = line.split(":", 1)[1].strip()
            digits = "".join(c for c in raw if c.isdigit())
            fit = int(digits[0]) if digits else None
        elif line.upper().startswith("RESUME_ANGLE:"):
            mode = None
            angle = line.split(":", 1)[1].strip()
        elif line.upper().startswith("BLURB:"):
            mode = "blurb"
            blurb_lines.append(line.split(":", 1)[1].strip())
        elif mode == "blurb":
            blurb_lines.append(line.strip())
    blurb = " ".join(x for x in blurb_lines if x).strip()
    if not blurb:
        blurb = text.strip()  # fallback: model didn't follow format
    return {"fit": fit, "resume_angle": angle, "blurb": blurb}
