import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.i18n import I18nManager
from utils.helpers import setup_session_state

st.set_page_config(
    page_title="SmartScheme AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

i18n = I18nManager.get_instance()

setup_session_state()

i18n.set_language(st.session_state.get("language", "en"))

t = i18n.t

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,100..900;1,100..900&family=Noto+Sans+Telugu:wght@100..900&family=Noto+Sans+Devanagari:wght@100..900&display=swap');
    html, body, .stApp, [class*="css"], [class*="st-"], p, span, div, label, li, a, h1, h2, h3, h4, h5, h6 {
        font-family: 'Noto Sans', 'Noto Sans Telugu', 'Noto Sans Devanagari',
                     'Nirmala UI', 'Mangal', 'Lohit Devanagari', 'Lohit Telugu',
                     'Noto Sans CJK SC', 'Noto Sans CJK JP',
                     sans-serif;
    }
    code, pre, .stCodeBlock { font-family: monospace; }
    .stTextInput, .stSelectbox { margin-bottom: 0.75rem; }
    .stTextInput label, .stSelectbox label { padding-top: 0.5rem !important; padding-bottom: 0.25rem !important; white-space: normal !important; word-break: break-word; }
    .streamlit-expanderContent { padding-top: 0.75rem !important; }
    .st-bq, .st-emotion-cache-1wivap2, .st-emotion-cache-1aezhbc { white-space: normal !important; word-break: break-word; }
    .row-widget { overflow: visible !important; }
    details > summary { white-space: normal !important; word-break: break-word; padding-right: 3.5rem !important; position: relative; z-index: 1; }
    .st-emotion-cache-1aezhbc { padding-right: 3.5rem !important; }
    .stApp { font-size: 1.1rem; }
    .stButton > button {
        font-size: 1.1rem;
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
        font-weight: 600;
        line-height: 1.3;
    }
    .stTextInput > div > div > input { font-size: 1.1rem; }
    .stSelectbox > div > div > div { font-size: 1.1rem; }
    h1 { font-size: 2.2rem !important; }
    h2 { font-size: 1.8rem !important; }
    h3 { font-size: 1.4rem !important; }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 1rem;
    }
    .nav-container {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .nav-container .stButton > button {
        font-size: 1rem;
        padding: 0.5rem 0.3rem;
        min-height: 70px;
        white-space: normal;
        word-break: break-word;
        line-height: 1.2;
    }
    .st-emotion-cache-1wivap2 { font-size: 1.1rem; }
    @media (max-width: 768px) {
        .stButton > button { font-size: 0.9rem; padding: 0.4rem 0.5rem; }
    }
    *:focus { outline: 3px solid #FFD700 !important; outline-offset: 2px !important; }
    .skip-link {
        position: absolute; left: -9999px; z-index: 999;
        padding: 1em; background: #000; color: #fff; text-decoration: none;
    }
    .skip-link:focus { left: 50%; transform: translateX(-50%); }
    .voice-button {
        font-size: 2rem !important; padding: 1.5rem !important;
        border-radius: 50% !important; width: 100px !important;
        height: 100px !important; text-align: center !important; line-height: 1 !important;
    }
    .active-nav .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: 2px solid #FFD700 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f'<a href="#main-content" class="skip-link">{t("a11y_skip_link")}</a>', unsafe_allow_html=True)

st.markdown(f"""
<div class="main-header">
    <h1>{t('app_title')}</h1>
    <p style="font-size:1.3rem; margin-top:0.5rem;">{t('app_subtitle')}</p>
</div>
""", unsafe_allow_html=True)

page_list = [
    ("home", "🏠", "nav_home"),
    ("discover", "🔍", "nav_discover"),
    ("chat", "💬", "nav_chat"),
    ("eligibility", "✅", "nav_eligibility"),
    ("pdf_summary", "📄", "nav_pdf_summary"),
    ("settings", "⚙️", "nav_settings"),
]

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
curr = st.session_state.current_page

nav_cols = st.columns(6)
for i, (page_id, icon, label_key) in enumerate(page_list):
    with nav_cols[i]:
        label = t(label_key)
        active_class = "active-nav" if curr == page_id else ""
        st.markdown(f'<div class="{active_class}">', unsafe_allow_html=True)
        btn_label = f"{icon}\n{label}"
        if st.button(btn_label, key=f"nav_{page_id}", use_container_width=True):
            st.session_state.current_page = page_id
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

st.markdown('<div id="main-content">', unsafe_allow_html=True)

current_page = st.session_state.get("current_page", "home")

if current_page == "home":
    from pages.home import show as show_home
    show_home()
elif current_page == "discover":
    from pages.discover import show as show_discover
    show_discover()
elif current_page == "chat":
    from pages.chat import show as show_chat
    show_chat()
elif current_page == "eligibility":
    from pages.eligibility import show as show_eligibility
    show_eligibility()
elif current_page == "pdf_summary":
    from pages.pdf_summary import show as show_pdf
    show_pdf()
elif current_page == "settings":
    from pages.settings import show as show_settings
    show_settings()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    f"<p style='text-align:center; color: #888;'>{t('footer_text')}</p>",
    unsafe_allow_html=True,
)
