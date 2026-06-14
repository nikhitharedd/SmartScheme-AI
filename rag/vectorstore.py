import logging
from typing import Any, Callable, Optional

import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_MODEL_CACHE: dict[str, SentenceTransformer] = {}


class VectorStore:
    def __init__(self, persist_dir: str = "./chroma_db") -> None:
        self.persist_dir = persist_dir
        self._client: PersistentClient = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="government_schemes",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Initialised VectorStore at '%s' (collection: '%s')",
            persist_dir,
            "government_schemes",
        )

    @staticmethod
    def _get_embeddings_function() -> Callable[[str], list[float]]:
        model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        if model_name not in _MODEL_CACHE:
            logger.info("Loading embedding model: %s", model_name)
            _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
        model = _MODEL_CACHE[model_name]

        def _embed(text: str) -> list[float]:
            return model.encode(text, normalize_embeddings=True).tolist()

        return _embed

    def add_scheme(
        self,
        scheme_id: str,
        title: str,
        description: str,
        eligibility: str,
        benefits: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        embed_fn = self._get_embeddings_function()
        combined_text = (
            f"{title} {description} {eligibility} {benefits}"
        )
        embedding = embed_fn(combined_text)
        meta: dict[str, Any] = {
            "title": title,
            "description": description,
            "eligibility": eligibility,
            "benefits": benefits,
        }
        if metadata:
            meta.update(metadata)

        try:
            self._collection.add(
                ids=[scheme_id],
                embeddings=[embedding],
                metadatas=[meta],
                documents=[combined_text],
            )
            logger.info("Added scheme '%s' (%s)", title, scheme_id)
        except Exception:
            logger.exception("Failed to add scheme '%s'", scheme_id)
            raise

    def add_schemes_batch(self, schemes: list[dict[str, Any]]) -> None:
        embed_fn = self._get_embeddings_function()
        ids: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict[str, Any]] = []
        documents: list[str] = []

        for scheme in schemes:
            scheme_id = scheme["scheme_id"]
            title = scheme.get("title", "")
            description = scheme.get("description", "")
            eligibility = scheme.get("eligibility", "")
            benefits = scheme.get("benefits", "")
            metadata = scheme.get("metadata", {})

            combined_text = f"{title} {description} {eligibility} {benefits}"
            ids.append(scheme_id)
            documents.append(combined_text)
            meta: dict[str, Any] = {
                "title": title,
                "description": description,
                "eligibility": eligibility,
                "benefits": benefits,
            }
            meta.update(metadata)
            metadatas.append(meta)

        try:
            embeddings = [embed_fn(doc) for doc in documents]
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
            logger.info("Batch added %d schemes", len(schemes))
        except Exception:
            logger.exception("Failed to batch-add %d schemes", len(schemes))
            raise

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        embed_fn = self._get_embeddings_function()
        try:
            query_emb = embed_fn(query)
            results = self._collection.query(
                query_embeddings=[query_emb],
                n_results=k,
            )
        except Exception:
            logger.exception("Search failed for query: %s", query)
            return []

        return self._format_results(results)

    def search_by_metadata(
        self, filter: dict[str, Any], k: int = 20
    ) -> list[dict[str, Any]]:
        try:
            results = self._collection.query(
                query_texts=[""],
                n_results=k,
                where=filter,
            )
        except Exception:
            logger.exception("Metadata search failed for filter: %s", filter)
            return []

        return self._format_results(results)

    def get_collection_stats(self) -> dict[str, Any]:
        try:
            count = self._collection.count()
            return {
                "collection_name": "government_schemes",
                "total_documents": count,
                "persist_directory": self.persist_dir,
            }
        except Exception:
            logger.exception("Failed to get collection stats")
            return {"error": "Unable to retrieve collection stats"}

    def delete_collection(self) -> None:
        try:
            self._client.delete_collection("government_schemes")
            self._collection = self._client.create_collection(
                name="government_schemes",
                metadata={"hnsw:space": "cosine"},
            )
            logger.warning("Deleted and recreated collection 'government_schemes'")
        except Exception:
            logger.exception("Failed to delete collection")
            raise

    @staticmethod
    def _format_results(
        results: Any,
    ) -> list[dict[str, Any]]:
        formatted: list[dict[str, Any]] = []
        if not results or not results.get("ids"):
            return formatted

        for i, doc_id in enumerate(results["ids"][0]):
            entry: dict[str, Any] = {
                "scheme_id": doc_id,
            }
            if results.get("metadatas"):
                entry["metadata"] = results["metadatas"][0][i]
            if results.get("documents"):
                entry["content"] = results["documents"][0][i]
            if results.get("distances"):
                entry["score"] = 1 - results["distances"][0][i]
            formatted.append(entry)

        return formatted
