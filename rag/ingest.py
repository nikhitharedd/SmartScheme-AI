import csv
import json
import logging
import os
from typing import Any, Optional

import fitz

from rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)

_SUPPORTED_FORMATS = [".json", ".csv", ".pdf"]


class DocumentIngester:
    def __init__(self, vectorstore: VectorStore) -> None:
        self.vectorstore = vectorstore

    def ingest_scheme_data(self, filepath: str) -> int:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in _SUPPORTED_FORMATS:
            logger.warning("Unsupported format '%s' for file: %s", ext, filepath)
            return 0
        if ext == ".pdf":
            logger.warning(
                "Use ingest_pdf() for PDF files; ingest_scheme_data expects JSON or CSV."
            )
            return 0

        try:
            if ext == ".json":
                schemes = self._read_json(filepath)
            else:
                schemes = self._read_csv(filepath)
        except Exception:
            logger.exception("Failed to read file: %s", filepath)
            return 0

        if not schemes:
            logger.info("No schemes found in %s", filepath)
            return 0

        self.vectorstore.add_schemes_batch(schemes)
        logger.info("Ingested %d schemes from %s", len(schemes), filepath)
        return len(schemes)

    def ingest_pdf(self, filepath: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "file": filepath,
            "total_chunks": 0,
            "pages_extracted": 0,
            "status": "success",
        }

        try:
            text, num_pages = self._extract_text_from_pdf(filepath)
        except Exception:
            logger.exception("Failed to extract text from PDF: %s", filepath)
            return {"file": filepath, "total_chunks": 0, "status": "failed"}

        if not text.strip():
            logger.warning("No text extracted from PDF: %s", filepath)
            return {**result, "pages_extracted": num_pages, "status": "no_text"}

        chunks = self._split_text(text)
        metadata = self._extract_metadata_from_pdf(filepath)

        schemes: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{os.path.basename(filepath)}_chunk_{idx:04d}"
            schemes.append(
                {
                    "scheme_id": chunk_id,
                    "title": metadata.get("title", os.path.basename(filepath)),
                    "description": chunk,
                    "eligibility": "",
                    "benefits": "",
                    "metadata": {
                        **metadata,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "source": "pdf",
                    },
                }
            )

        self.vectorstore.add_schemes_batch(schemes)
        result["total_chunks"] = len(chunks)
        result["pages_extracted"] = num_pages
        logger.info(
            "Ingested PDF '%s': %d chunks from %d pages",
            filepath,
            len(chunks),
            num_pages,
        )
        return result

    def clear_and_reingest(self, filepath: str) -> None:
        logger.info("Clearing collection before re-ingest of %s", filepath)
        self.vectorstore.delete_collection()
        self.ingest_scheme_data(filepath)

    @staticmethod
    def get_supported_formats() -> list[str]:
        return list(_SUPPORTED_FORMATS)

    @staticmethod
    def _split_text(
        text: str, chunk_size: int = 500, overlap: int = 50
    ) -> list[str]:
        if chunk_size <= overlap:
            chunk_size = overlap + 50

        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            if end >= text_len:
                chunks.append(text[start:].strip())
                break

            split_at = text.rfind(" ", start + chunk_size - overlap, end)
            if split_at <= start:
                split_at = end

            chunks.append(text[start:split_at].strip())
            start = split_at

        return chunks

    @staticmethod
    def _extract_metadata_from_pdf(filepath: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "filename": os.path.basename(filepath),
            "source": "pdf",
        }
        try:
            doc = fitz.open(filepath)
            pdf_meta = doc.metadata
            if pdf_meta:
                if pdf_meta.get("title"):
                    metadata["title"] = pdf_meta["title"]
                if pdf_meta.get("author"):
                    metadata["author"] = pdf_meta["author"]
                if pdf_meta.get("subject"):
                    metadata["subject"] = pdf_meta["subject"]
            doc.close()
        except Exception:
            logger.warning("Could not extract PDF metadata from %s", filepath)
        return metadata

    @staticmethod
    def _extract_text_from_pdf(filepath: str) -> tuple[str, int]:
        doc = fitz.open(filepath)
        num_pages = doc.page_count
        full_text_parts: list[str] = []

        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            text = page.get_text()
            full_text_parts.append(text)

        doc.close()
        return "\n".join(full_text_parts), num_pages

    @staticmethod
    def _read_json(filepath: str) -> list[dict[str, Any]]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            schemes = data.get("schemes") or data.get("data") or []
            if isinstance(schemes, list):
                return schemes
        raise ValueError("JSON structure not recognised; expected a list or {schemes: [...]}")

    @staticmethod
    def _read_csv(filepath: str) -> list[dict[str, Any]]:
        schemes: list[dict[str, Any]] = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scheme: dict[str, Any] = {
                    "scheme_id": row.get("scheme_id", ""),
                    "title": row.get("title", ""),
                    "description": row.get("description", ""),
                    "eligibility": row.get("eligibility", ""),
                    "benefits": row.get("benefits", ""),
                    "metadata": {},
                }
                meta_keys = [k for k in row if k not in scheme]
                for key in meta_keys:
                    scheme["metadata"][key] = row[key]
                schemes.append(scheme)
        return schemes
