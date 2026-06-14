import logging
import os
import tempfile

import streamlit as st

from ai.provider_router import AIProviderRouter
from rag.ingest import DocumentIngester
from rag.vectorstore import VectorStore
from utils.i18n import I18nManager

logger = logging.getLogger(__name__)

_SUMMARIZATION_PROMPT_TEMPLATE = """Summarise the following government scheme document in a clear structured format. {lang_instruction} Use the sections below:

**Summary**: A 2-3 sentence overview of what the scheme is about.

**Eligibility Criteria**: Who can apply (age, income, category, occupation, etc).

**Benefits**: What beneficiaries receive (financial amounts, services, etc).

**Documents Required**: List of documents needed for application.

**Application Process**: Step-by-step process to apply.

Document text:
{text}

Structured summary:"""


def _generate_summary(extracted_text: str, t) -> str | None:
    provider_name = st.session_state.get("provider", "ollama")
    config = st.session_state.get("provider_config", {})
    lang = st.session_state.get("language", "en")
    lang_instructions = {
        "en": "Respond in English.",
        "te": "Respond in Telugu (తెలుగు). Use Telugu script for all responses.",
        "hi": "Respond in Hindi (हिन्दी). Use Devanagari script for all responses.",
    }
    lang_instruction = lang_instructions.get(lang, "Respond in English.")

    try:
        provider = AIProviderRouter.create_provider(provider_name, config)
        prompt = _SUMMARIZATION_PROMPT_TEMPLATE.format(
            text=extracted_text[:8000], lang_instruction=lang_instruction
        )
        response = provider.generate(prompt)
        return response
    except Exception:
        logger.exception("AI summary generation failed")
        return None


def _display_summary_sections(summary_text: str, t) -> None:
    sections: dict[str, str] = {
        t("pdf_summary_label"): "",
        t("pdf_eligibility_label"): "",
        t("pdf_benefits_label"): "",
        t("pdf_documents_label"): "",
        t("pdf_process_label"): "",
    }

    current_key: str | None = None
    for line in summary_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        for key in sections:
            if key.lower() in stripped.lower() and ":" in stripped:
                current_key = key
                parts = stripped.split(":", 1)
                if len(parts) > 1:
                    sections[key] += parts[1].strip() + "\n"
                break
        else:
            if current_key:
                sections[current_key] += stripped + "\n"

    for section_title, content in sections.items():
        st.markdown(f"### {section_title}")
        if content:
            st.markdown(content)
        else:
            st.markdown(f"*{t('common_none')}*")
        st.markdown("---")


def show() -> None:
    i18n = I18nManager.get_instance()
    t = i18n.t

    st.markdown(f"# {t('pdf_title')}")
    st.markdown(f"### {t('pdf_subtitle')}")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        t("pdf_upload_btn"),
        type=["pdf"],
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.info(t("pdf_no_file"))
        return

    if st.button("\U0001f50a", key="pdf_listen_btn", help=t("voice_listen_btn"), use_container_width=True):
        st.info(t("voice_listening"))

    with st.spinner(t("pdf_processing")):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            vs = VectorStore(persist_dir="./chroma_db")
            ingester = DocumentIngester(vs)
            ingest_result = ingester.ingest_pdf(tmp_path)

            if ingest_result.get("status") == "failed":
                st.error(t("pdf_error"))
                os.unlink(tmp_path)
                return

            if ingest_result.get("status") == "no_text":
                st.warning(t("pdf_error"))
                os.unlink(tmp_path)
                return

            st.success(t("common_success"))
            st.markdown(f"**{t('pdf_extracted_from')}:** {uploaded_file.name}")
            st.markdown(
                f"*Pages: {ingest_result.get('pages_extracted', 0)}, "
                f"Chunks: {ingest_result.get('total_chunks', 0)}*"
            )

            extracted_text, _ = DocumentIngester._extract_text_from_pdf(tmp_path)
            os.unlink(tmp_path)

        except Exception:
            logger.exception("PDF processing failed")
            st.error(t("pdf_error"))
            return

    if not extracted_text.strip():
        st.error(t("pdf_error"))
        return

    summary = _generate_summary(extracted_text, t)

    st.markdown("---")
    if summary:
        _display_summary_sections(summary, t)
    else:
        st.error(t("pdf_error"))
