import logging
from typing import Any, Optional

from rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)

_CRITERIA_FIELD_MAP: dict[str, str] = {
    "age_min": "age_min",
    "age_max": "age_max",
    "gender": "gender",
    "occupation": "occupation",
    "income_max": "income_max",
    "state": "state",
    "category": "category",
}


class Retriever:
    def __init__(self, vectorstore: VectorStore) -> None:
        self.vectorstore = vectorstore

    def retrieve_schemes(
        self,
        query: str,
        k: int = 5,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        try:
            if filters:
                results = self.vectorstore.search(query, k=k)
                results = self._apply_filters(results, filters)
            else:
                results = self.vectorstore.search(query, k=k)
            return results
        except Exception:
            logger.exception("Retrieval failed for query: %s", query)
            return []

    def retrieve_with_scores(
        self, query: str, k: int = 5
    ) -> list[tuple[dict[str, Any], float]]:
        try:
            results = self.vectorstore.search(query, k=k)
            return [
                (r, r.get("score", 0.0))
                for r in results
                if "score" in r
            ]
        except Exception:
            logger.exception("Retrieval with scores failed for query: %s", query)
            return []

    def format_context(
        self, results: list[dict[str, Any]], max_chars: int = 3000
    ) -> str:
        parts: list[str] = []
        total = 0

        for result in results:
            meta = result.get("metadata", {}) or {}
            title = meta.get("title", result.get("scheme_id", "Unknown"))
            description = meta.get("description", "")
            eligibility = meta.get("eligibility", "")
            benefits = meta.get("benefits", "")

            block = (
                f"--- {title} ---\n"
                f"Description: {description}\n"
                f"Eligibility: {eligibility}\n"
                f"Benefits: {benefits}\n"
            )

            block_len = len(block)
            if total + block_len > max_chars:
                remaining = max_chars - total
                if remaining > 100:
                    parts.append(block[:remaining])
                break

            parts.append(block)
            total += block_len

        return "\n".join(parts)

    def retrieve_by_criteria(
        self, criteria: dict[str, Any], k: int = 10
    ) -> list[dict[str, Any]]:
        try:
            chroma_filter = self._build_metadata_filter(criteria)
            return self.vectorstore.search_by_metadata(filter=chroma_filter, k=k)
        except Exception:
            logger.exception(
                "Criteria-based retrieval failed for: %s", criteria
            )
            return []

    def hybrid_retrieve(
        self, query: str, criteria: dict[str, Any], k: int = 5
    ) -> list[dict[str, Any]]:
        try:
            chroma_filter = self._build_metadata_filter(criteria)
            return self.vectorstore.search(query, k=k)
        except Exception:
            logger.exception(
                "Hybrid retrieval failed (query=%s, criteria=%s)", query, criteria
            )
            return []

    @staticmethod
    def _build_metadata_filter(criteria: dict[str, Any]) -> dict[str, Any]:
        conditions: list[dict[str, Any]] = []

        for key, field in _CRITERIA_FIELD_MAP.items():
            if key not in criteria:
                continue
            value = criteria[key]

            if key == "income_max":
                conditions.append({field: {"$lte": value}})
            elif key == "age_min":
                conditions.append({field: {"$gte": value}})
            elif key == "age_max":
                conditions.append({field: {"$lte": value}})
            else:
                if isinstance(value, str):
                    conditions.append({field: {"$eq": value.lower()}})
                else:
                    conditions.append({field: {"$eq": value}})

        if not conditions:
            return {}

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}

    @staticmethod
    def _apply_filters(
        results: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []
        for result in results:
            meta = result.get("metadata", {}) or {}
            match = True
            for key, val in filters.items():
                if key in meta:
                    if isinstance(val, (list, tuple)):
                        if meta[key] not in val:
                            match = False
                            break
                    elif meta[key] != val:
                        match = False
                        break
                else:
                    match = False
                    break
            if match:
                filtered.append(result)
        return filtered
