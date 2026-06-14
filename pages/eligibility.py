import logging
from typing import Any

import streamlit as st

from utils.helpers import get_available_occupations, get_available_states
from utils.i18n import I18nManager
from utils.scheme_engine import SchemeEngine

logger = logging.getLogger(__name__)


def _user_profile_form(t) -> dict[str, Any] | None:
    st.markdown(f"### {t('eligibility_title')}")

    with st.form("eligibility_profile_form"):
        cols = st.columns(2)
        with cols[0]:
            age = st.number_input(t("discover_age"), min_value=1, max_value=120, value=30)
        with cols[1]:
            gender = st.selectbox(
                t("discover_gender"),
                options=["male", "female", "other"],
                format_func=lambda x: t(f"gender_{x}"),
            )
        with cols[0]:
            occupation = st.selectbox(t("discover_occupation"), options=get_available_occupations())
        with cols[1]:
            income = st.number_input(
                t("discover_income"), min_value=0, max_value=10000000, value=0, step=10000
            )
        with cols[0]:
            state = st.selectbox(t("discover_state"), options=get_available_states())
        with cols[1]:
            category = st.selectbox(
                t("discover_category"),
                options=["general", "obc", "sc", "st", "ews"],
                format_func=lambda x: t(f"category_{x}"),
            )

        submitted = st.form_submit_button(t("common_submit"), type="primary", use_container_width=True)

    if submitted:
        return {
            "age": age,
            "gender": gender,
            "occupation": occupation,
            "income": income,
            "state": state,
            "category": category,
        }
    return None


def _show_eligibility_result(result: dict[str, Any], t) -> None:
    status = result.get("status", "not_eligible")
    score = result.get("score", 0)
    reasoning = result.get("reasoning", "")
    details = result.get("details", {})

    if status == "eligible":
        badge = "\U0001f7e2"
        color = "#2ecc71"
        label = t("eligibility_eligible")
    elif status == "partially":
        badge = "\u26a0\ufe0f"
        color = "#f39c12"
        label = t("eligibility_partially")
    else:
        badge = "\u274c"
        color = "#e74c3c"
        label = t("eligibility_not_eligible")

    st.markdown(
        f"<div style='padding:1rem; border-radius:10px; border:2px solid {color}; text-align:center;'>"
        f"<span style='font-size:3rem'>{badge}</span>"
        f"<h3 style='color:{color}'>{label}</h3>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(f"**{t('discover_match')}:** {score}%")
    st.progress(score / 100.0)

    st.markdown(f"**{t('eligibility_reasoning')}:** {reasoning}")

    st.markdown(f"### {t('eligibility_details')}")
    for criterion, info in details.items():
        status_icon = "\u2705" if info.get("status") == "passed" else "\u274c" if info.get("status") == "failed" else "\u2796"
        detail_text = info.get("detail", "")
        label_map = {k: t(f"discover_{k}") if k in ("age", "gender", "occupation", "income", "state", "category") else k.title() for k in ("occupation", "category", "income", "state", "age", "gender")}
        label = label_map.get(criterion, criterion.title())
        st.markdown(f"{status_icon} **{label}:** {detail_text}")


def show() -> None:
    i18n = I18nManager.get_instance()
    t = i18n.t

    st.markdown(f"# {t('eligibility_title')}")
    st.markdown(f"### {t('eligibility_subtitle')}")

    if "eligibility_profile" not in st.session_state:
        st.session_state.eligibility_profile = None

    if st.session_state.eligibility_profile is None:
        profile = _user_profile_form(t)
        if profile is not None:
            st.session_state.eligibility_profile = profile
            st.rerun()
        return

    st.success(t("common_success"))
    if st.button(t("common_retry"), use_container_width=True):
        st.session_state.eligibility_profile = None
        st.session_state.eligibility_result = None
        st.rerun()

    st.markdown("---")

    engine = SchemeEngine()
    engine.load_schemes()
    all_schemes = engine.get_all_schemes()

    if not all_schemes:
        st.warning(t("discover_no_schemes"))
        return

    lang = st.session_state.get("language", "en")
    scheme_options = {
        s.get("id") or s.get("scheme_id", ""):
        SchemeEngine.get_localized(s, "title", lang)
        for s in all_schemes
    }
    selected_id = st.selectbox(
        t("eligibility_select_scheme"),
        options=list(scheme_options.keys()),
        format_func=lambda x: scheme_options[x],
    )

    if st.button(t("eligibility_check_btn"), type="primary", use_container_width=True):
        with st.spinner(t("common_loading")):
            try:
                result = engine.check_eligibility(selected_id, st.session_state.eligibility_profile)
                st.session_state.eligibility_result = result
            except Exception:
                logger.exception("Eligibility check failed")
                st.error(t("eligibility_error"))
                return

    if st.session_state.get("eligibility_result"):
        _show_eligibility_result(st.session_state.eligibility_result, t)
