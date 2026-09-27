"""Built-in keyword presets so a new user gets a sane filter for their field
without having to write one from scratch. `setup.py` lets them pick one (or
write custom keywords), and the result is saved into data/settings.json.
"""
from __future__ import annotations

PRESETS: dict[str, dict[str, list[str]]] = {
    "software": {
        "include": [
            "software engineer", "software developer", "software dev",
            "web developer", "frontend developer", "front-end developer",
            "frontend engineer", "front-end engineer",
            "backend developer", "back-end developer", "backend engineer", "back-end engineer",
            "full stack developer", "full-stack developer", "fullstack developer",
            "full stack engineer", "full-stack engineer", "fullstack engineer",
            "python developer", "javascript developer", "typescript developer",
            "react developer", "node.js developer", "node developer",
            "qa engineer", "test engineer", "sdet",
            "devops engineer", "platform engineer", "site reliability engineer",
            "data analyst", "data engineer", "junior data",
            "software engineering intern", "software development intern",
            "engineering intern", "developer intern", "programming intern",
            "junior developer", "junior software engineer", "junior engineer",
            "graduate software engineer", "graduate developer",
        ],
        "exclude_title": [
            "senior", "staff", "principal", "lead ", "director", "vp ", "head of",
            "manager", "architect", "10+ years", "sales", "marketing",
        ],
    },
    "data": {
        "include": [
            "data analyst", "data engineer", "data scientist", "junior data",
            "analytics engineer", "business intelligence analyst", "bi analyst",
            "data science intern", "data analyst intern", "reporting analyst",
            "junior data analyst", "junior data scientist", "graduate data",
        ],
        "exclude_title": [
            "senior", "staff", "principal", "lead ", "director", "vp ", "head of",
            "manager", "10+ years",
        ],
    },
    "marketing": {
        "include": [
            "marketing coordinator", "digital marketing specialist", "marketing intern",
            "content marketing", "social media coordinator", "social media specialist",
            "seo specialist", "marketing assistant", "junior marketing",
            "growth marketing", "email marketing specialist",
        ],
        "exclude_title": [
            "senior", "director", "vp ", "head of", "manager", "chief",
        ],
    },
    "customer_support": {
        "include": [
            "customer support specialist", "customer service representative",
            "technical support specialist", "support engineer", "help desk",
            "customer success associate", "support agent",
        ],
        "exclude_title": [
            "senior", "director", "vp ", "head of", "manager", "lead ",
        ],
    },
}

DEFAULT_PRESET = "software"
