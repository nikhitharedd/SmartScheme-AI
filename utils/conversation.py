import re
from typing import Any

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

_OCCUPATION_KEYWORDS: dict[str, str] = {
    "farmer": "Farmer",
    "agriculture": "Agricultural Labourer",
    "cultivation": "Farmer",
    "self employed": "Self Employed",
    "business": "Business Owner",
    "salaried": "Salaried",
    "employee": "Salaried",
    "private job": "Private Sector Employee",
    "government job": "Government Employee",
    "govt": "Government Employee",
    "student": "Student",
    "studying": "Student",
    "unemployed": "Unemployed",
    "home maker": "Home Maker",
    "housewife": "Home Maker",
    "teacher": "Teacher",
    "doctor": "Healthcare Worker",
    "nurse": "Healthcare Worker",
    "retired": "Retired",
    "pensioner": "Retired",
    "veteran": "Veteran",
    "ex serviceman": "Veteran",
    "daily wage": "Daily Wage Worker",
    "laborer": "Daily Wage Worker",
    "labour": "Daily Wage Worker",
    "vendor": "Street Vendor",
    "artisan": "Artisan",
    "fisherman": "Fisherman",
    "construction": "Construction Worker",
    "domestic help": "Domestic Worker",
    "maid": "Domestic Worker",
    "driver": "Daily Wage Worker",
    "small business": "Small Business Owner",
    "shopkeeper": "Small Business Owner",
}

_INTENT_PATTERNS: dict[str, list[str]] = {
    "scheme_discovery": [
        "scheme", "yojana", "benefit", "scholarship", "loan",
        "pension", "help", "schemes", "yojanas", "subsidy",
        "grant", "assistance", "program", "plan",
    ],
    "eligibility_check": [
        "eligible", "qualify", "can i", "apply", "check",
        "am i eligible", "do i qualify", "eligibility",
        "criteria", "requirements", "required",
    ],
    "pdf_related": [
        "pdf", "document", "upload", "summary", "download",
        "file", "attachment", "form", "application form",
    ],
}


class ConversationManager:
    def __init__(self, max_history: int = 10):
        self._max_history = max_history
        self._history: list[dict[str, str]] = []

    def add_message(self, role: str, content: str, lang: str = "en") -> None:
        role = role.strip().lower()
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role '{role}'. Must be 'user' or 'assistant'.")

        self._history.append({
            "role": role,
            "content": content.strip(),
            "lang": lang,
        })

        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self) -> list[dict[str, str]]:
        return list(self._history)

    def get_context(self) -> str:
        if not self._history:
            return ""

        lines: list[str] = []
        for msg in self._history:
            speaker = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{speaker}: {msg['content']}")
        return "\n".join(lines)

    def clear_history(self) -> None:
        self._history.clear()

    def get_conversation_length(self) -> int:
        return len(self._history)

    def detect_intent(self, message: str) -> str:
        text = message.strip().lower()

        for intent, keywords in _INTENT_PATTERNS.items():
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text, re.IGNORECASE):
                    return intent

        return "general"

    def extract_user_preferences(self, message: str) -> dict[str, Any]:
        text = message.strip()
        preferences: dict[str, Any] = {}

        age_match = re.search(r"\b(\d{1,3})\s*(years?\s*old|years?\s*of\s*age|yr?s?)\b", text, re.IGNORECASE)
        if not age_match:
            age_match = re.search(r"\bage[:\s]*(\d{1,3})\b", text, re.IGNORECASE)
        if not age_match:
            age_match = re.search(r"\b(\d{1,3})\s*(yr|year|y/o)\b", text, re.IGNORECASE)
        if age_match:
            preferences["age"] = int(age_match.group(1))

        income_match = re.search(
            r"(?:income|salary|earn|earning|monthly)\s*(?:is|of|:)?\s*"
            r"(?:rs\.?\s*|inr\s*|₹\s*)?(\d{1,2}(?:,\d{3})*(?:\.\d{1,2})?)",
            text, re.IGNORECASE,
        )
        if not income_match:
            income_match = re.search(
                r"(?:rs\.?\s*|inr\s*|₹\s*)?(\d{1,2}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:per\s*month|monthly)",
                text, re.IGNORECASE,
            )
        if income_match:
            raw = income_match.group(1).replace(",", "")
            try:
                preferences["income"] = float(raw)
            except ValueError:
                pass

        state_keywords: list[str] = []
        for st in _INDIAN_STATES:
            pattern = r"\b" + re.escape(st.lower()) + r"\b"
            if re.search(pattern, text.lower()):
                if st != "All India":
                    state_keywords.append(st)
        if state_keywords:
            preferences["state"] = state_keywords[0]

        detected_occupation: str | None = None
        text_lower = text.lower()
        best_match_len = 0
        for keyword, occupation in _OCCUPATION_KEYWORDS.items():
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text_lower):
                if len(keyword) > best_match_len:
                    best_match_len = len(keyword)
                    detected_occupation = occupation
        if detected_occupation:
            preferences["occupation"] = detected_occupation

        category_keywords: dict[str, list[str]] = {
            "General": ["general", "gen"],
            "OBC": ["obc", "other backward class", "backward class"],
            "SC": ["sc", "scheduled caste"],
            "ST": ["st", "scheduled tribe", "tribe"],
            "EWS": ["ews", "economically weaker"],
            "Minority": ["minority", "muslim", "christian", "sikh", "jain", "buddhist", "parsi"],
            "Below Poverty Line (BPL)": ["bpl", "below poverty line", "poverty"],
            "Women": ["women", "woman", "female", "girl", "mahila"],
            "Senior Citizen": ["senior", "senior citizen", "old age", "elderly", "aged"],
            "Disability": ["disability", "disabled", "divyang", "handicapped", "physically challenged"],
            "Transgender": ["transgender", "trans", "third gender"],
            "Rural": ["rural", "gramin", "village"],
            "Urban": ["urban", "city", "town", "shahari"],
        }
        for cat, cat_kws in category_keywords.items():
            for ck in cat_kws:
                if re.search(r"\b" + re.escape(ck) + r"\b", text_lower):
                    preferences["category"] = cat
                    break
            if "category" in preferences:
                break

        gender_match = re.search(r"\b(gender|male|female|man|woman|boy|girl)\b", text_lower)
        if gender_match:
            g = gender_match.group(1).lower()
            if g in ("male", "man", "boy"):
                preferences["gender"] = "male"
            elif g in ("female", "woman", "girl"):
                preferences["gender"] = "female"

        return preferences

    def format_prompt(
        self, user_message: str, scheme_context: str = "", lang: str = "en"
    ) -> str:
        history_str = self.get_context()
        lang_instructions = {
            "en": "Respond in English.",
            "te": "Respond in Telugu (తెలుగు). Use Telugu script for all responses.",
            "hi": "Respond in Hindi (हिन्दी). Use Devanagari script for all responses.",
        }
        lang_instruction = lang_instructions.get(lang, "Respond in English.")
        parts: list[str] = [
            "You are SmartScheme AI, a helpful assistant for Indian government scheme information.",
            "You provide information about government schemes, check eligibility, and help users discover benefits.",
            lang_instruction,
            "",
        ]

        if scheme_context:
            parts.append("=== Scheme Information ===")
            parts.append(scheme_context)
            parts.append("")

        if history_str:
            parts.append("=== Conversation History ===")
            parts.append(history_str)
            parts.append("")

        parts.append("=== Current Query ===")
        parts.append(f"User: {user_message}")
        parts.append("")
        parts.append("Assistant:")

        return "\n".join(parts)

    def summarize_conversation(self) -> str:
        if not self._history:
            return "No conversation history."

        total = len(self._history)
        user_msgs = sum(1 for m in self._history if m["role"] == "user")
        assistant_msgs = total - user_msgs

        user_content: list[str] = []
        assistant_content: list[str] = []
        for m in self._history:
            if m["role"] == "user":
                user_content.append(m["content"])
            else:
                assistant_content.append(m["content"])

        summary = (
            f"Conversation Summary:\n"
            f"Total messages: {total} ({user_msgs} user, {assistant_msgs} assistant)\n"
        )

        if user_content:
            summary += f"User topics: {' | '.join(user_content[:3])}"
            if len(user_content) > 3:
                summary += f" (+{len(user_content) - 3} more)"

        intents_detected = set()
        for m in self._history:
            if m["role"] == "user":
                intents_detected.add(self.detect_intent(m["content"]))
        if intents_detected:
            summary += f"\nDetected intents: {', '.join(sorted(intents_detected))}"

        return summary
