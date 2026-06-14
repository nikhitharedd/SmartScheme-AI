import streamlit as st
from utils.i18n import I18nManager


def show() -> None:
    i18n = I18nManager.get_instance()
    t = i18n.t

    st.markdown(f"# {t('app_title')}")
    st.markdown(f"### {t('app_subtitle')}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<p style='font-size:1.3rem'>{t('app_tagline')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p>{t('home_description')}</p>", unsafe_allow_html=True)

        if st.button(t("home_start_btn"), type="primary", use_container_width=True):
            st.session_state.current_page = "discover"
            st.rerun()

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("\U0001f3a4", key="home_voice_btn_big", help=t("voice_speak_now"), use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
        st.markdown(f"<p style='text-align:center'>{t('home_voice_btn')}</p>", unsafe_allow_html=True)

    st.markdown("---")
    cols = st.columns(2)
    features = [
        ("\U0001f50d", t("home_feature_discovery"), t("home_feature_discovery_desc")),
        ("\U0001f4ac", t("home_feature_chat"), t("home_feature_chat_desc")),
        ("\u2705", t("home_feature_eligibility"), t("home_feature_eligibility_desc")),
        ("\U0001f4c4", t("home_feature_pdf"), t("home_feature_pdf_desc")),
    ]
    for idx, (icon, title, desc) in enumerate(features):
        with cols[idx % 2]:
            st.markdown(f"### {icon} {title}")
            st.markdown(desc)

    st.markdown("---")
    st.markdown(t("footer_disclaimer"))
