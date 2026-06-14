import logging
from typing import Any

import streamlit as st

from utils.helpers import get_available_occupations, get_available_states
from utils.i18n import I18nManager
from utils.scheme_engine import SchemeEngine

logger = logging.getLogger(__name__)


def _build_user_profile(form_data: dict[str, Any]) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "age": form_data.get("age", 30),
        "gender": form_data.get("gender", "male"),
        "occupation": form_data.get("occupation", ""),
        "income": form_data.get("income", 0),
        "state": form_data.get("state", ""),
        "category": form_data.get("category", "general"),
    }
    return profile


def _show_scheme_card(result: dict[str, Any], t, lang: str = "en") -> None:
    from utils.scheme_engine import SchemeEngine

    scheme = result.get("scheme", {})
    score = result.get("match_score", 0)
    reasons = result.get("match_reasons", [])

    title = SchemeEngine.get_localized(scheme, "title", lang)
    desc = SchemeEngine.get_localized(scheme, "description", lang)
    benefits = SchemeEngine.get_localized(scheme, "benefits", lang)
    el = scheme.get("eligibility", {})

    with st.container(border=True):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(f"### {title}")
        with col_b:
            st.markdown(
                f"<div style='text-align:center; font-size:2rem; font-weight:bold; color:"
                f"{'#2ecc71' if score >= 80 else '#f39c12' if score >= 50 else '#e74c3c'};"
                f"'>{score}%</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<p style='text-align:center'>{t('discover_match')}</p>", unsafe_allow_html=True)

        if desc:
            st.markdown(desc)

        st.markdown(f"**{t('discover_eligibility')}:**")
        income_limit = el.get("income_limit")
        age_min = el.get("age_min")
        age_max = el.get("age_max")
        details = []
        if age_min is not None or age_max is not None:
            lo = age_min or 0
            hi = age_max or 99
            details.append(f"{t('discover_age')}: {lo}-{hi}")
        if income_limit is not None:
            details.append(f"{t('discover_income')}: \u20b9{income_limit:,}")
        for d in details:
            st.markdown(f"- {d}")

        if benefits:
            st.markdown(f"**{t('discover_benefits')}:**")
            for b in benefits[:3]:
                st.markdown(f"- {b}")
            if len(benefits) > 3:
                st.markdown(f"... +{len(benefits) - 3} {t('discover_learn_more').lower()}")

        with st.expander(t("discover_learn_more")):
            for reason in reasons:
                st.markdown(f"- {reason}")


def show() -> None:
    i18n = I18nManager.get_instance()
    t = i18n.t

    st.markdown(f"# {t('discover_title')}")
    st.markdown(f"### {t('discover_subtitle')}")
    st.markdown("---")

    if "user_profile" not in st.session_state:
        st.session_state.user_profile = None

    with st.form("discover_form"):
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

        submitted = st.form_submit_button(t("discover_btn"), type="primary", use_container_width=True)

    if submitted:
        form_data = {
            "age": age,
            "gender": gender,
            "occupation": occupation,
            "income": income,
            "state": state,
            "category": category,
        }
        st.session_state.user_profile = _build_user_profile(form_data)

        with st.spinner(t("discover_finding")):
            try:
                engine = SchemeEngine()
                engine.load_schemes()
                results = engine.recommend_schemes(st.session_state.user_profile)
                st.session_state.scheme_results = results
            except Exception:
                logger.exception("Scheme discovery failed")
                st.error(t("discover_error"))
                return

    results = st.session_state.get("scheme_results", [])
    if results:
        perfect_matches = [r for r in results if r.get("match_score", 0) == 100]
        if perfect_matches:
            st.markdown(f"### {t('discover_title')}")
            lang = st.session_state.get("language", "en")
            for result in perfect_matches:
                _show_scheme_card(result, t, lang)
        else:
            st.info(t("discover_no_schemes"))
    elif st.session_state.user_profile is not None:
        st.info(t("discover_no_schemes"))
