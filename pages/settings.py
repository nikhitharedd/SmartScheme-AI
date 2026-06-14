import logging
from typing import Any

import streamlit as st

from ai.provider_router import AIProviderRouter
from utils.helpers import is_valid_api_key
from utils.i18n import I18nManager

logger = logging.getLogger(__name__)


def _change_language(lang_code: str, t) -> None:
    try:
        i18n = I18nManager.get_instance()
        i18n.set_language(lang_code)
        st.session_state.language = lang_code
    except ValueError:
        st.error(t("common_error"))


def _validate_and_save(t) -> None:
    provider = st.session_state.get("settings_provider", "ollama")
    config: dict[str, Any] = {}

    if provider == "ollama":
        config["endpoint"] = st.session_state.get("settings_ollama_endpoint", "http://localhost:11434")
        config["model"] = st.session_state.get("settings_ollama_model", "llama3")
    elif provider == "openai":
        api_key = st.session_state.get("settings_openai_api_key", "")
        if not is_valid_api_key(api_key):
            st.error(t("settings_api_key_hint"))
            return
        config["api_key"] = api_key
        config["model"] = st.session_state.get("settings_openai_model", "gpt-4o-mini")
    elif provider == "gemini":
        api_key = st.session_state.get("settings_gemini_api_key", "")
        if not is_valid_api_key(api_key):
            st.error(t("settings_api_key_hint"))
            return
        config["api_key"] = api_key
        config["model"] = st.session_state.get("settings_gemini_model", "gemini-pro")

    valid, msg = AIProviderRouter.validate_config(provider, config)
    if not valid:
        st.error(msg)
        return

    st.session_state.provider = provider
    st.session_state.provider_config = config
    st.success(t("settings_saved"))


def show() -> None:
    i18n = I18nManager.get_instance()
    t = i18n.t

    st.markdown(f"# {t('settings_title')}")
    st.markdown(f"### {t('settings_subtitle')}")
    st.markdown("---")

    current_lang = st.session_state.get("language", "en")
    lang = st.selectbox(
        t("settings_language"),
        options=["en", "te", "hi"],
        format_func=lambda x: {"en": "English", "te": "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41", "hi": "\u0939\u093f\u0928\u094d\u0926\u0940"}.get(x, x),
        index=["en", "te", "hi"].index(current_lang) if current_lang in ["en", "te", "hi"] else 0,
        key="settings_language_selector",
    )
    if lang != current_lang:
        _change_language(lang, t)
        st.rerun()

    st.markdown("---")

    st.markdown(f"### {t('settings_voice_tts')} / {t('settings_voice_stt')}")
    col1, col2 = st.columns(2)
    with col1:
        st.toggle(t("settings_voice_tts"), value=st.session_state.get("tts_enabled", True), key="tts_toggle")
    with col2:
        st.toggle(t("settings_voice_stt"), value=st.session_state.get("stt_enabled", True), key="stt_toggle")

    st.markdown("---")

    st.markdown(f"### {t('settings_advanced_title')}")
    current_provider = st.session_state.get("provider", "ollama")
    provider = st.selectbox(
        t("settings_ai_provider"),
        options=["ollama", "openai", "gemini"],
        format_func=lambda x: t(f"settings_{x}"),
        index=["ollama", "openai", "gemini"].index(current_provider) if current_provider in ["ollama", "openai", "gemini"] else 0,
        key="settings_provider",
    )

    if provider == "ollama":
        st.text_input(
            t("settings_endpoint"),
            value=st.session_state.get("provider_config", {}).get("endpoint", "http://localhost:11434"),
            key="settings_ollama_endpoint",
        )
        st.text_input(
            t("settings_model"),
            value=st.session_state.get("provider_config", {}).get("model", "llama3"),
            key="settings_ollama_model",
        )
    elif provider == "openai":
        st.text_input(
            t("settings_api_key"),
            type="password",
            value=st.session_state.get("provider_config", {}).get("api_key", ""),
            help=t("settings_api_key_hint"),
            key="settings_openai_api_key",
        )
        st.text_input(
            t("settings_model"),
            value=st.session_state.get("provider_config", {}).get("model", "gpt-4o-mini"),
            key="settings_openai_model",
        )
    elif provider == "gemini":
        st.text_input(
            t("settings_api_key"),
            type="password",
            value=st.session_state.get("provider_config", {}).get("api_key", ""),
            help=t("settings_api_key_hint"),
            key="settings_gemini_api_key",
        )
        st.text_input(
            t("settings_model"),
            value=st.session_state.get("provider_config", {}).get("model", "gemini-pro"),
            key="settings_gemini_model",
        )

    if st.button(t("settings_save_btn"), type="primary", use_container_width=True):
        _validate_and_save(t)
