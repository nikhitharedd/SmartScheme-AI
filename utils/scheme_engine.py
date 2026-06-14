import json
import logging
import os
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

INDIAN_STATES: list[str] = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
    "All India",
]

INDIAN_OCCUPATIONS: list[str] = [
    "Farmer", "Agricultural Labourer", "Self Employed", "Salaried",
    "Daily Wage Worker", "Student", "Unemployed", "Home Maker",
    "Government Employee", "Private Sector Employee", "Business Owner",
    "Teacher", "Healthcare Worker", "Retired", "Veteran",
    "Small Business Owner", "Street Vendor", "Artisan", "Fisherman",
    "Construction Worker", "Domestic Worker",
]

INDIAN_CATEGORIES: list[str] = [
    "General", "OBC", "SC", "ST", "EWS", "Minority",
    "Below Poverty Line (BPL)", "Above Poverty Line (APL)",
    "Women", "Children", "Senior Citizen", "Disability",
    "Transgender", "Urban", "Rural",
]

_WEIGHT_OCCUPATION = 25
_WEIGHT_CATEGORY = 15
_WEIGHT_INCOME = 15
_WEIGHT_STATE = 15
_WEIGHT_AGE = 15
_WEIGHT_GENDER = 15


class SchemeEngine:
    def __init__(self, schemes_data_path: str = "data/schemes/schemes.json"):
        self._schemes_data_path = schemes_data_path
        self._schemes: list[dict[str, Any]] = []
        self._loaded = False

    def load_schemes(self) -> list[dict[str, Any]]:
        path = Path(self._schemes_data_path)
        if not path.exists():
            logger.warning("Schemes data file not found at %s", path)
            self._schemes = []
            self._loaded = True
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load schemes data: %s", e)
            self._schemes = []
            self._loaded = True
            return []

        if isinstance(data, list):
            self._schemes = data
        elif isinstance(data, dict):
            self._schemes = data.get("schemes", [])
        else:
            self._schemes = []
        self._loaded = True
        logger.info("Loaded %d schemes from %s", len(self._schemes), path)
        return self._schemes

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_schemes()

    def get_all_schemes(self) -> list[dict[str, Any]]:
        self._ensure_loaded()
        return list(self._schemes)

    def get_scheme_by_id(self, scheme_id: str) -> dict[str, Any] | None:
        self._ensure_loaded()
        for scheme in self._schemes:
            if scheme.get("id") == scheme_id or scheme.get("scheme_id") == scheme_id:
                return dict(scheme)
        return None

    def _get_field(self, scheme: dict[str, Any], field: str, default: Any = None) -> Any:
        return scheme.get(field, default)

    def _get_criteria(self, scheme: dict[str, Any]) -> dict[str, Any]:
        return scheme.get("eligibility_criteria") or scheme.get("eligibility") or {}

    @staticmethod
    def get_localized(scheme: dict[str, Any], field: str, lang: str) -> Any:
        lang_field = f"{field}_{lang}"
        val = scheme.get(lang_field)
        if val:
            return val
        return scheme.get(field, "")

    def _safe_int(self, value: Any, default: int = 0) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _matches_occupation(self, scheme: dict[str, Any], user_occupation: str) -> bool:
        allowed = self._get_criteria(scheme).get("occupations", [])
        if not allowed:
            return True
        if "All" in allowed:
            return True
        return any(
            self._fuzzy_match(user_occupation, occ) for occ in allowed
        )

    def _matches_category(self, scheme: dict[str, Any], user_category: str) -> bool:
        allowed = self._get_criteria(scheme).get("categories", [])
        if not allowed:
            return True
        return any(
            self._fuzzy_match(user_category, cat) for cat in allowed
        )

    def _matches_income(self, scheme: dict[str, Any], user_income: float | None) -> bool:
        income_limit = self._get_criteria(scheme).get("income_limit") or self._get_criteria(scheme).get("income_max")
        if income_limit is None or user_income is None:
            return income_limit is None
        return user_income <= self._safe_float(income_limit)

    def _matches_state(self, scheme: dict[str, Any], user_state: str) -> bool:
        allowed = self._get_criteria(scheme).get("states", [])
        if not allowed:
            return True
        if "All India" in allowed:
            return True
        return any(
            self._fuzzy_match(user_state, st) for st in allowed
        )

    def _matches_gender(self, scheme: dict[str, Any], user_gender: str) -> bool:
        if not user_gender:
            return True
        allowed = self._get_criteria(scheme).get("gender", "")
        if not allowed or allowed.lower() == "all":
            return True
        return allowed.strip().lower() == user_gender.strip().lower()

    def _matches_age(self, scheme: dict[str, Any], user_age: int | None) -> bool:
        if user_age is None:
            return True
        el = self._get_criteria(scheme)
        age_min = self._safe_int(el.get("age_min"))
        age_max = self._safe_int(el.get("age_max"), 999)
        return age_min <= user_age <= age_max

    def _fuzzy_match(self, value: str, target: str) -> bool:
        a = value.strip().lower()
        b = target.strip().lower()
        if a == b:
            return True
        ratio = SequenceMatcher(None, a, b).ratio()
        return ratio > 0.8

    def recommend_schemes(self, user_profile: dict[str, Any]) -> list[dict[str, Any]]:
        self._ensure_loaded()
        if not self._schemes:
            return []

        age = self._safe_int(user_profile.get("age"))
        gender = (user_profile.get("gender") or "").strip().lower()
        occupation = (user_profile.get("occupation") or "").strip()
        income = self._safe_float(user_profile.get("income"))
        state = (user_profile.get("state") or "").strip()
        category = (user_profile.get("category") or "").strip()

        results: list[dict[str, Any]] = []

        for scheme in self._schemes:
            score = 0
            reasons: list[str] = []

            if self._matches_occupation(scheme, occupation):
                score += _WEIGHT_OCCUPATION
                reasons.append("Occupation matches scheme criteria")
            elif self._get_criteria(scheme).get("occupations"):
                reasons.append("Occupation does not fully match")
            else:
                score += _WEIGHT_OCCUPATION
                reasons.append("No occupation restriction")

            if self._matches_category(scheme, category):
                score += _WEIGHT_CATEGORY
                reasons.append("Category matches scheme criteria")
            elif self._get_criteria(scheme).get("categories"):
                reasons.append("Category does not fully match")
            else:
                score += _WEIGHT_CATEGORY
                reasons.append("No category restriction")

            if self._matches_income(scheme, income):
                score += _WEIGHT_INCOME
                reasons.append("Within income eligibility limits")
            elif self._get_criteria(scheme).get("income_max") is not None:
                reasons.append("Income exceeds eligibility limit")
            else:
                score += _WEIGHT_INCOME
                reasons.append("No income restriction")

            if self._matches_state(scheme, state):
                score += _WEIGHT_STATE
                reasons.append(f"State ({state}) is eligible")
            elif self._get_criteria(scheme).get("states"):
                reasons.append("State may not be eligible")
            else:
                score += _WEIGHT_STATE
                reasons.append("No state restriction")

            if self._matches_age(scheme, age):
                score += _WEIGHT_AGE
                reasons.append("Age within eligible range")
            elif self._get_criteria(scheme).get("age_min") is not None:
                reasons.append("Age outside eligible range")
            else:
                score += _WEIGHT_AGE
                reasons.append("No age restriction")

            if self._matches_gender(scheme, gender):
                score += _WEIGHT_GENDER
                reasons.append("Gender matches scheme criteria")
            elif self._get_criteria(scheme).get("gender"):
                reasons.append("Gender does not fully match")
            else:
                score += _WEIGHT_GENDER
                reasons.append("No gender restriction")

            results.append({
                "scheme": scheme,
                "match_score": score,
                "match_reasons": reasons,
            })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results

    def check_eligibility(
        self, scheme_id: str, user_profile: dict[str, Any]
    ) -> dict[str, Any]:
        self._ensure_loaded()
        scheme = self.get_scheme_by_id(scheme_id)
        if scheme is None:
            return {
                "status": "not_eligible",
                "score": 0,
                "reasoning": f"Scheme with ID '{scheme_id}' not found.",
                "details": {},
            }

        age = self._safe_int(user_profile.get("age"))
        gender = (user_profile.get("gender") or "").strip().lower()
        occupation = (user_profile.get("occupation") or "").strip()
        income = self._safe_float(user_profile.get("income"))
        state = (user_profile.get("state") or "").strip()
        category = (user_profile.get("category") or "").strip()

        el = self._get_criteria(scheme)
        details: dict[str, Any] = {}
        total_passed = 0
        total_checks = 0

        occ_allowed = el.get("occupations", [])
        if occ_allowed:
            total_checks += 1
            ok = self._matches_occupation(scheme, occupation)
            details["occupation"] = {
                "status": "passed" if ok else "failed",
                "expected": occ_allowed,
                "provided": occupation,
                "detail": f"Occupation '{occupation}' {'is' if ok else 'is not'} among allowed: {occ_allowed}",
            }
            if ok:
                total_passed += 1
        else:
            details["occupation"] = {
                "status": "skipped",
                "detail": "No occupation restriction for this scheme",
            }

        cat_allowed = el.get("categories", [])
        if cat_allowed:
            total_checks += 1
            ok = self._matches_category(scheme, category)
            details["category"] = {
                "status": "passed" if ok else "failed",
                "expected": cat_allowed,
                "provided": category,
                "detail": f"Category '{category}' {'is' if ok else 'is not'} among allowed: {cat_allowed}",
            }
            if ok:
                total_passed += 1
        else:
            details["category"] = {
                "status": "skipped",
                "detail": "No category restriction for this scheme",
            }

        income_limit = el.get("income_max")
        if income_limit is not None:
            total_checks += 1
            ok = self._matches_income(scheme, income)
            details["income"] = {
                "status": "passed" if ok else "failed",
                "expected": f"Income <= {income_limit}",
                "provided": income,
                "detail": (
                    f"Income {income} is {'within' if ok else 'above'} limit {income_limit}"
                ),
            }
            if ok:
                total_passed += 1
        else:
            details["income"] = {
                "status": "skipped",
                "detail": "No income restriction for this scheme",
            }

        state_allowed = el.get("states", [])
        if state_allowed:
            total_checks += 1
            ok = self._matches_state(scheme, state)
            details["state"] = {
                "status": "passed" if ok else "failed",
                "expected": state_allowed,
                "provided": state,
                "detail": f"State '{state}' {'is' if ok else 'is not'} among eligible: {state_allowed}",
            }
            if ok:
                total_passed += 1
        else:
            details["state"] = {
                "status": "skipped",
                "detail": "No state restriction for this scheme",
            }

        age_min = el.get("age_min")
        age_max = el.get("age_max")
        if age_min is not None or age_max is not None:
            total_checks += 1
            ok = self._matches_age(scheme, age)
            age_range = f"{age_min or 0}-{age_max or 999}"
            details["age"] = {
                "status": "passed" if ok else "failed",
                "expected": f"Age in range {age_range}",
                "provided": age,
                "detail": f"Age {age} is {'within' if ok else 'outside'} required range {age_range}",
            }
            if ok:
                total_passed += 1
        else:
            details["age"] = {
                "status": "skipped",
                "detail": "No age restriction for this scheme",
            }

        gender_restriction = el.get("gender", "")
        if gender_restriction and gender_restriction.lower() != "all":
            total_checks += 1
            ok = gender_restriction.lower() == gender
            details["gender"] = {
                "status": "passed" if ok else "failed",
                "expected": gender_restriction,
                "provided": gender,
                "detail": f"Gender '{gender}' {'matches' if ok else 'does not match'} requirement '{gender_restriction}'",
            }
            if ok:
                total_passed += 1
        else:
            details["gender"] = {
                "status": "skipped",
                "detail": "No gender restriction or open to all",
            }

        if total_checks == 0:
            score = 100
            status: str = "eligible"
            reasoning = "No specific eligibility criteria defined; scheme is open to all."
        else:
            score = int(round((total_passed / total_checks) * 100))
            if score == 100:
                status = "eligible"
            elif score >= 50:
                status = "partially"
            else:
                status = "not_eligible"

            passed_criteria = [k for k, v in details.items() if v.get("status") == "passed"]
            failed_criteria = [k for k, v in details.items() if v.get("status") == "failed"]
            if status == "eligible":
                reasoning = "All eligibility criteria are satisfied."
            elif status == "partially":
                reasoning = (
                    f"Partially eligible. Met {total_passed}/{total_checks} criteria. "
                    f"Failed: {', '.join(failed_criteria) if failed_criteria else 'none'}"
                )
            else:
                reasoning = (
                    f"Not eligible. Met only {total_passed}/{total_checks} criteria. "
                    f"Failed: {', '.join(failed_criteria)}"
                )

        return {
            "status": status,
            "score": score,
            "reasoning": reasoning,
            "details": details,
        }

    def get_schemes_by_category(self, category: str) -> list[dict[str, Any]]:
        self._ensure_loaded()
        cat = category.strip().lower()
        return [
            dict(s)
            for s in self._schemes
            if cat == (s.get("category") or "").strip().lower()
        ]

    def get_schemes_by_occupation(self, occupation: str) -> list[dict[str, Any]]:
        self._ensure_loaded()
        occ = occupation.strip().lower()
        results: list[dict[str, Any]] = []
        for s in self._schemes:
            allowed = self._get_criteria(s).get("occupations", [])
            if any(occ == a.strip().lower() for a in allowed):
                results.append(dict(s))
        return results

    def search_schemes(self, query: str) -> list[dict[str, Any]]:
        self._ensure_loaded()
        q = query.strip().lower()
        if not q:
            return self.get_all_schemes()

        results: list[dict[str, Any]] = []
        for s in self._schemes:
            title = (s.get("title") or "").lower()
            title_hi = (s.get("title_hi") or "").lower()
            title_te = (s.get("title_te") or "").lower()
            desc = (s.get("description") or "").lower()
            desc_hi = (s.get("description_hi") or "").lower()
            desc_te = (s.get("description_te") or "").lower()
            category = (s.get("category") or "").lower()
            ministry = (s.get("ministry") or "").lower()
            keywords = (s.get("keywords") or [])
            if isinstance(keywords, list):
                kw_text = " ".join(k.lower() for k in keywords)
            else:
                kw_text = ""

            combined = " ".join([
                title, title_hi, title_te,
                desc, desc_hi, desc_te,
                category, ministry, kw_text,
            ])
            if q in combined:
                results.append(dict(s))

        return results

    def get_statistics(self) -> dict[str, Any]:
        self._ensure_loaded()
        if not self._schemes:
            return {
                "total_schemes": 0,
                "categories": [],
                "ministries": [],
                "category_counts": {},
                "ministry_counts": {},
            }

        categories: dict[str, int] = {}
        ministries: dict[str, int] = {}

        for s in self._schemes:
            cat = (s.get("category") or "Uncategorized").strip()
            categories[cat] = categories.get(cat, 0) + 1

            minis = s.get("ministry") or "Unknown"
            if isinstance(minis, list):
                for m in minis:
                    m = m.strip()
                    ministries[m] = ministries.get(m, 0) + 1
            else:
                ministries[minis.strip()] = ministries.get(minis.strip(), 0) + 1

        return {
            "total_schemes": len(self._schemes),
            "categories": sorted(categories.keys()),
            "ministries": sorted(ministries.keys()),
            "category_counts": categories,
            "ministry_counts": ministries,
        }

    def generate_checklist(self, scheme_id: str) -> dict[str, Any]:
        self._ensure_loaded()
        scheme = self.get_scheme_by_id(scheme_id)
        if scheme is None:
            return {
                "documents": [],
                "steps": [],
                "notes": [],
                "submission_guidance": "Scheme not found.",
            }

        docs_raw = scheme.get("documents_required", [])
        if isinstance(docs_raw, str):
            documents = [d.strip() for d in docs_raw.split(",") if d.strip()]
        elif isinstance(docs_raw, list):
            documents = [str(d) for d in docs_raw]
        else:
            documents = []

        process_raw = scheme.get("application_process", [])
        if isinstance(process_raw, str):
            steps = [s.strip() for s in process_raw.split(".") if s.strip()]
        elif isinstance(process_raw, list):
            steps = [str(s) for s in process_raw]
        else:
            steps = []

        notes = []
        if scheme.get("notes"):
            raw = scheme["notes"]
            if isinstance(raw, list):
                notes = [str(n) for n in raw]
            else:
                notes = [str(raw)]

        guidance = scheme.get("submission_guidance", "")
        if not guidance:
            guidance = (
                f"Please submit the required documents to the concerned "
                f"department as per the application process. "
                f"For further assistance, visit the official website or "
                f"contact the designated helpdesk."
            )

        return {
            "documents": documents,
            "steps": steps,
            "notes": notes,
            "submission_guidance": guidance,
        }

    def get_scheme_summary(
        self, scheme_id: str, lang: str = "en"
    ) -> dict[str, Any]:
        self._ensure_loaded()
        scheme = self.get_scheme_by_id(scheme_id)
        if scheme is None:
            return {}

        title_key = "title"
        desc_key = "description"
        benefits_key = "benefits"
        if lang in ("hi", "te"):
            candidate_title = f"title_{lang}"
            candidate_desc = f"description_{lang}"
            candidate_benefits = f"benefits_{lang}"
            if scheme.get(candidate_title):
                title_key = candidate_title
            if scheme.get(candidate_desc):
                desc_key = candidate_desc
            if scheme.get(candidate_benefits):
                benefits_key = candidate_benefits

        raw_benefits = scheme.get(benefits_key, [])
        if isinstance(raw_benefits, str):
            benefits_list = [b.strip() for b in raw_benefits.split(",")]
        elif isinstance(raw_benefits, list):
            benefits_list = [str(b) for b in raw_benefits]
        else:
            benefits_list = []

        el = self._get_criteria(scheme)
        summary = {
            "scheme_id": scheme.get("id") or scheme.get("scheme_id"),
            "title": scheme.get(title_key, scheme.get("title", "")),
            "description": scheme.get(desc_key, scheme.get("description", "")),
            "category": scheme.get("category", ""),
            "ministry": scheme.get("ministry", ""),
            "benefits": benefits_list,
            "eligibility_criteria": {
                "age_min": el.get("age_min"),
                "age_max": el.get("age_max"),
                "income_limit": el.get("income_max"),
                "gender": el.get("gender", ""),
                "occupation": el.get("occupations", []),
                "category": el.get("categories", []),
                "state": el.get("states", []),
            },
            "application_process": scheme.get("application_process", []),
            "documents_required": scheme.get("documents_required", []),
            "language": lang,
        }

        return summary
