import re
from typing import Any
import streamlit as st

_INDIAN_STATES: list[str] = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

_INDIAN_OCCUPATIONS: list[str] = [
    "Farmer", "Agricultural Labourer", "Self Employed", "Salaried",
    "Daily Wage Worker", "Student", "Unemployed", "Home Maker",
    "Government Employee", "Private Sector Employee", "Business Owner",
    "Teacher", "Healthcare Worker", "Retired", "Veteran",
    "Small Business Owner", "Street Vendor", "Artisan", "Fisherman",
    "Construction Worker", "Domestic Worker",
]

_INDIAN_CATEGORIES: list[str] = [
    "General", "OBC", "SC", "ST", "EWS", "Minority",
    "Below Poverty Line (BPL)", "Above Poverty Line (APL)",
    "Women", "Children", "Senior Citizen", "Disability",
    "Transgender", "Urban", "Rural",
]

_APP_VERSION = "1.0.0"

_SANITIZE_PATTERN = re.compile(r"[<>\{\}\[\]\\;'\"]")



def setup_session_state() -> None:
    default_state: dict[str, Any] = {
        "language": "en",
        "provider": "ollama",
        "provider_config": {
            "endpoint": "http://localhost:11434",
            "model": "llama3",
        },
        "messages": [],
        "user_profile": {
            "age": None,
            "gender": None,
            "occupation": None,
            "income": None,
            "state": None,
            "category": None,
        },
        "current_page": "home",
        "scheme_results": [],
        "selected_scheme": None,
        "eligibility_result": None,
        "conversation_history": [],
        "pdf_summary": None,
        "uploaded_files": [],
        "feedback": None,
    }
    for key, val in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_available_states() -> list[str]:
    return list(_INDIAN_STATES)


def get_available_occupations() -> list[str]:
    return list(_INDIAN_OCCUPATIONS)


def get_available_categories() -> list[str]:
    return list(_INDIAN_CATEGORIES)


def generate_scheme_card(scheme: dict[str, Any], lang: str = "en") -> str:
    title_key = "title"
    desc_key = "description"
    if lang in ("hi", "te"):
        candidate_title = f"title_{lang}"
        candidate_desc = f"description_{lang}"
        if scheme.get(candidate_title):
            title_key = candidate_title
        if scheme.get(candidate_desc):
            desc_key = candidate_desc

    title = sanitize_text(scheme.get(title_key, scheme.get("title", "Unknown Scheme")))
    description = sanitize_text(
        scheme.get(desc_key, scheme.get("description", ""))
    )
    desc_truncated = truncate_text(description, max_chars=150)
    category = sanitize_text(scheme.get("category", ""))
    ministry = sanitize_text(scheme.get("ministry", ""))

    lines: list[str] = [
        f"### {title}",
        f"**Category:** {category}  ",
        f"**Ministry:** {ministry}  ",
        "",
        f"{desc_truncated}",
        "",
    ]

    return "\n".join(lines)


def format_benefits(benefits: list[str], lang: str = "en") -> str:
    if not benefits:
        if lang == "hi":
            return "कोई लाभ सूचीबद्ध नहीं हैं।"
        if lang == "te":
            return "ప్రయోజనాలు ఏవీ జాబితా చేయబడలేదు."
        return "No benefits listed."

    lines: list[str] = []
    start = "लाभ:" if lang == "hi" else "ప్రయోజనాలు:" if lang == "te" else "Benefits:"
    lines.append(f"**{start}**")
    for benefit in benefits:
        text = sanitize_text(benefit)
        lines.append(f"- {text}")

    return "\n".join(lines)


def sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    text = _SANITIZE_PATTERN.sub("", text)
    text = text.replace("|", "I")
    text = text.replace("`", "'")
    return text.strip()


def truncate_text(text: str, max_chars: int = 200) -> str:
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    if len(truncated) < len(text[:max_chars]):
        return truncated + "..."
    return text[:max_chars] + "..."


def is_valid_api_key(key: str) -> bool:
    if not key or not isinstance(key, str):
        return False
    key = key.strip()
    if not key:
        return False
    patterns = [
        re.compile(r"^sk-[A-Za-z0-9]{32,}$"),
        re.compile(r"^sk-[A-Za-z0-9_-]{20,}$"),
        re.compile(r"^[A-Za-z0-9_-]{32,}$"),
        re.compile(r"^[A-Za-z0-9]{16,}$"),
    ]
    return any(p.match(key) for p in patterns)


def get_app_version() -> str:
    return _APP_VERSION
