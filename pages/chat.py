import logging

import streamlit as st

from ai.provider_router import AIProviderRouter
from utils.conversation import ConversationManager
from utils.i18n import I18nManager
from utils.scheme_engine import SchemeEngine

logger = logging.getLogger(__name__)

_WELCOME_SHOWN_KEY = "chat_welcome_shown"


def _init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = ConversationManager()
    if _WELCOME_SHOWN_KEY not in st.session_state:
        st.session_state[_WELCOME_SHOWN_KEY] = False


def _show_welcome(t) -> None:
    if st.session_state[_WELCOME_SHOWN_KEY]:
        return
    st.session_state.messages.append({"role": "assistant", "content": t("chat_welcome_msg")})
    st.session_state[_WELCOME_SHOWN_KEY] = True


def _display_messages(t) -> None:
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        avatar = "\U0001f916" if role == "assistant" else "\U0001f464"
        with st.chat_message(role, avatar=avatar):
            st.markdown(content)


def _get_ai_response(user_message: str, t, lang: str = "en") -> str:
    cm: ConversationManager = st.session_state.conversation_manager
    intent = cm.detect_intent(user_message)

    engine = SchemeEngine()
    engine.load_schemes()
    scheme_context = ""

    if intent == "scheme_discovery":
        prefs = cm.extract_user_preferences(user_message)
        if prefs:
            profile = {
                "age": prefs.get("age", 30),
                "gender": prefs.get("gender", "male"),
                "occupation": prefs.get("occupation", ""),
                "income": prefs.get("income", 0),
                "state": prefs.get("state", ""),
                "category": prefs.get("category", "general"),
            }
            results = engine.recommend_schemes(profile)
            if results:
                lines = [t("chat_response_schemes_header") + "\n"]
                for r in results[:5]:
                    s = r["scheme"]
                    title = SchemeEngine.get_localized(s, "title", lang)
                    lines.append(f"- **{title}** (match: {r['match_score']}%)")
                scheme_context = "\n".join(lines)
                cm.add_message("assistant", scheme_context)
                return scheme_context
        else:
            schemes = engine.get_all_schemes()
            if schemes:
                cats = set(s.get("category", "General") for s in schemes)
                scheme_context = t("chat_response_schemes_available").format(
                    count=len(schemes), categories=len(cats)
                )
                cm.add_message("assistant", scheme_context)
                return scheme_context

    elif intent == "eligibility_check":
        prefs = cm.extract_user_preferences(user_message)
        if prefs:
            profile = {
                "age": prefs.get("age", 30),
                "gender": prefs.get("gender", "male"),
                "occupation": prefs.get("occupation", ""),
                "income": prefs.get("income", 0),
                "state": prefs.get("state", ""),
                "category": prefs.get("category", "general"),
            }
            results = engine.recommend_schemes(profile)
            if results:
                top = results[0]
                s = top["scheme"]
                title = SchemeEngine.get_localized(s, "title", lang)
                benefits = SchemeEngine.get_localized(s, "benefits", lang)
                scheme_context = t("chat_response_eligibility").format(
                    scheme=title, score=top['match_score']
                ) + "\n\n" + (
                    f"**{t('pdf_benefits_label')}:** {', '.join(benefits)}\n\n"
                    f"**{t('pdf_documents_label')}:** {', '.join(s.get('documents_required', []))}"
                )
                cm.add_message("assistant", scheme_context)
                return scheme_context

    provider_name = st.session_state.get("provider", "ollama")
    config = st.session_state.get("provider_config", {})

    if scheme_context:
        prompt = cm.format_prompt(user_message, scheme_context, lang)
    else:
        prompt = cm.format_prompt(user_message, lang=lang)
    try:
        provider = AIProviderRouter.create_provider(provider_name, config)
        response_text = provider.generate(prompt)
    except Exception:
        logger.exception("AI response generation failed")
        if scheme_context:
            response_text = scheme_context
        else:
            response_text = t("chat_error")

    return response_text


def show() -> None:
    i18n = I18nManager.get_instance()
    t = i18n.t

    _init_session()
    _show_welcome(t)

    st.markdown(f"# {t('chat_title')}")
    st.markdown(f"### {t('chat_subtitle')}")

    col_clear, _ = st.columns([1, 5])
    with col_clear:
        if st.button(t("chat_clear_btn"), use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_manager = ConversationManager()
            st.session_state[_WELCOME_SHOWN_KEY] = False
            st.rerun()

    st.markdown("---")

    _display_messages(t)

    col_input, col_voice = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            t("chat_input_placeholder"),
            key="chat_input",
            label_visibility="collapsed",
        )
    with col_voice:
        voice_pressed = st.button("\U0001f3a4", key="chat_voice_btn", help=t("chat_voice_hint"), use_container_width=True)

    col_send, _ = st.columns([1, 5])
    with col_send:
        send_pressed = st.button(t("chat_send_btn"), type="primary", use_container_width=True)

    if voice_pressed:
        st.info(t("chat_voice_hint"))

    if send_pressed and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        cm: ConversationManager = st.session_state.conversation_manager
        cm.add_message("user", user_input)

        with st.chat_message("assistant", avatar="\U0001f916"):
            with st.spinner(t("chat_thinking")):
                lang = st.session_state.get("language", "en")
                response = _get_ai_response(user_input, t, lang)

        st.session_state.messages.append({"role": "assistant", "content": response})
        cm.add_message("assistant", response)
        st.rerun()
