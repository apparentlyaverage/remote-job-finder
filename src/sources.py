"""Fetchers for public, automation-tolerant remote-job feeds.

Every source here either publishes an official public API/RSS feed or is a
company's own ATS board meant to be polled by applicants' tools. Nothing here
scrapes or automates against LinkedIn or any site whose ToS forbids it.

Each fetcher returns a list of normalized dicts:
    {id, source, title, company, url, location, description, posted_at}
"""
from __future__ import annotations

import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

USER_AGENT = "remote-job-finder/0.1 (personal job search tool; contact: sizomgadle887@gmail.com)"


def _get(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Job:
    id: str
    source: str
    title: str
    company: str
    url: str
    location: str = ""
    description: str = ""
    posted_at: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "location": self.location,
            "description": self.description,
            "posted_at": self.posted_at,
        }


def fetch_wwr(feed_urls: list[str]) -> list[Job]:
    """We Work Remotely RSS feeds."""
    jobs: list[Job] = []
    for feed_url in feed_urls:
        try:
            raw = _get(feed_url)
        except Exception as exc:  # noqa: BLE001
            print(f"[wwr] failed to fetch {feed_url}: {exc}")
            continue
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as exc:
            print(f"[wwr] failed to parse {feed_url}: {exc}")
            continue
        for item in root.findall(".//item"):
            title_raw = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            desc = _strip_html(item.findtext("description") or "")
            guid = (item.findtext("guid") or link).strip()
            # WWR titles are usually "Company: Job Title"
            company, _, title = title_raw.partition(":")
            title = title.strip() or title_raw
            company = company.strip() if title else "Unknown"
            jobs.append(
                Job(
                    id=f"wwr:{guid}",
                    source="weworkremotely",
                    title=title,
                    company=company or "Unknown",
                    url=link,
                    location="Remote",
                    description=desc,
                )
            )
    return jobs


def fetch_remoteok(api_url: str) -> list[Job]:
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[remoteok] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[remoteok] failed to parse JSON: {exc}")
        return []
    jobs: list[Job] = []
    for entry in data:
        if not isinstance(entry, dict) or "id" not in entry or "position" not in entry:
            continue  # first element is a legal notice, not a job
        jobs.append(
            Job(
                id=f"remoteok:{entry.get('id')}",
                source="remoteok",
                title=entry.get("position", ""),
                company=entry.get("company", "Unknown"),
                url=entry.get("url") or f"https://remoteok.com/remote-jobs/{entry.get('id')}",
                location=entry.get("location") or "Remote",
                description=_strip_html(entry.get("description", "")),
                posted_at=entry.get("date", ""),
            )
        )
    return jobs


def fetch_himalayas(api_url: str) -> list[Job]:
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[himalayas] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[himalayas] failed to parse JSON: {exc}")
        return []
    postings = data.get("jobs", data) if isinstance(data, dict) else data
    jobs: list[Job] = []
    for entry in postings or []:
        if not isinstance(entry, dict):
            continue
        guid = entry.get("guid") or entry.get("id") or entry.get("slug")
        if not guid:
            continue
        title = entry.get("title", "")
        company = (entry.get("companyName") or entry.get("company") or "Unknown")
        url = entry.get("applicationLink") or entry.get("url") or ""
        desc = _strip_html(entry.get("description", "") or entry.get("excerpt", ""))
        jobs.append(
            Job(
                id=f"himalayas:{guid}",
                source="himalayas",
                title=title,
                company=company,
                url=url,
                location="Remote",
                description=desc,
                posted_at=str(entry.get("pubDate", "")),
            )
        )
    return jobs


def fetch_greenhouse(company_slug: str) -> list[Job]:
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[greenhouse:{company_slug}] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[greenhouse:{company_slug}] failed to parse JSON: {exc}")
        return []
    jobs: list[Job] = []
    for entry in data.get("jobs", []):
        jobs.append(
            Job(
                id=f"greenhouse:{company_slug}:{entry.get('id')}",
                source="greenhouse",
                title=entry.get("title", ""),
                company=company_slug,
                url=entry.get("absolute_url", ""),
                location=(entry.get("location") or {}).get("name", ""),
                description=_strip_html(entry.get("content", "")),
                posted_at=entry.get("updated_at", ""),
            )
        )
    return jobs


def fetch_lever(company_slug: str) -> list[Job]:
    api_url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[lever:{company_slug}] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[lever:{company_slug}] failed to parse JSON: {exc}")
        return []
    jobs: list[Job] = []
    for entry in data:
        categories = entry.get("categories", {}) or {}
        jobs.append(
            Job(
                id=f"lever:{company_slug}:{entry.get('id')}",
                source="lever",
                title=entry.get("text", ""),
                company=company_slug,
                url=entry.get("hostedUrl", ""),
                location=categories.get("location", ""),
                description=_strip_html(entry.get("descriptionPlain", entry.get("description", ""))),
                posted_at=str(entry.get("createdAt", "")),
            )
        )
    return jobs


def fetch_remotive(api_url: str) -> list[Job]:
    """Remotive's public API. Their docs ask for max ~4 requests/day and
    proper attribution back to the original job URL — this pipeline runs
    once daily and already links every job to its real posting, so both
    conditions are met by design, not just by accident.
    """
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[remotive] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[remotive] failed to parse JSON: {exc}")
        return []
    jobs: list[Job] = []
    for entry in data.get("jobs", []):
        jobs.append(
            Job(
                id=f"remotive:{entry.get('id')}",
                source="remotive",
                title=entry.get("title", ""),
                company=entry.get("company_name", "Unknown"),
                url=entry.get("url", ""),
                location=entry.get("candidate_required_location") or "Remote",
                description=_strip_html(entry.get("description", "")),
                posted_at=entry.get("publication_date", ""),
            )
        )
    return jobs


def fetch_jobicy(api_url: str) -> list[Job]:
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[jobicy] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[jobicy] failed to parse JSON: {exc}")
        return []
    jobs: list[Job] = []
    for entry in data.get("jobs", []):
        jobs.append(
            Job(
                id=f"jobicy:{entry.get('id')}",
                source="jobicy",
                title=entry.get("jobTitle", ""),
                company=entry.get("companyName", "Unknown"),
                url=entry.get("url", ""),
                location=entry.get("jobGeo") or "Remote",
                description=_strip_html(entry.get("jobDescription", entry.get("jobExcerpt", ""))),
                posted_at="",
            )
        )
    return jobs


def fetch_arbeitnow(api_url: str) -> list[Job]:
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[arbeitnow] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[arbeitnow] failed to parse JSON: {exc}")
        return []
    jobs: list[Job] = []
    for entry in data.get("data", []):
        # Arbeitnow lists both remote and on-site roles — only keep remote
        # ones, since that's the whole point of this pipeline.
        if not entry.get("remote"):
            continue
        jobs.append(
            Job(
                id=f"arbeitnow:{entry.get('slug')}",
                source="arbeitnow",
                title=entry.get("title", ""),
                company=entry.get("company_name", "Unknown"),
                url=entry.get("url", ""),
                location=entry.get("location") or "Remote",
                description=_strip_html(entry.get("description", "")),
                posted_at=str(entry.get("created_at", "")),
            )
        )
    return jobs


def fetch_ashby(company_slug: str) -> list[Job]:
    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{company_slug}"
    try:
        raw = _get(api_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[ashby:{company_slug}] failed to fetch: {exc}")
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[ashby:{company_slug}] failed to parse JSON: {exc}")
        return []
    jobs: list[Job] = []
    for entry in data.get("jobs", []):
        jobs.append(
            Job(
                id=f"ashby:{company_slug}:{entry.get('id')}",
                source="ashby",
                title=entry.get("title", ""),
                company=company_slug,
                url=entry.get("jobUrl") or entry.get("applyUrl", ""),
                location=entry.get("location") or ("Remote" if entry.get("isRemote") else ""),
                description=_strip_html(entry.get("descriptionPlain", entry.get("descriptionHtml", ""))),
                posted_at=entry.get("publishedAt", ""),
            )
        )
    return jobs


def fetch_all(config) -> list[Job]:
    jobs: list[Job] = []
    jobs += fetch_wwr(config.WWR_FEEDS)
    jobs += fetch_remoteok(config.REMOTEOK_API)
    jobs += fetch_himalayas(config.HIMALAYAS_API)
    jobs += fetch_remotive(config.REMOTIVE_API)
    jobs += fetch_jobicy(config.JOBICY_API)
    jobs += fetch_arbeitnow(config.ARBEITNOW_API)
    for slug in config.GREENHOUSE_COMPANIES:
        jobs += fetch_greenhouse(slug)
    for slug in config.LEVER_COMPANIES:
        jobs += fetch_lever(slug)
    for slug in config.ASHBY_COMPANIES:
        jobs += fetch_ashby(slug)
    return jobs
