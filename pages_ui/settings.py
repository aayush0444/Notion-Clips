import os
import streamlit as st
from dotenv import load_dotenv, set_key, dotenv_values
from pages_ui.components import page_header

ENV_PATH = ".env"

def load_current_values():
    if os.path.exists(ENV_PATH):
        return dotenv_values(ENV_PATH)
    return {}

def save_env_value(key: str, value: str):
    if not os.path.exists(ENV_PATH):
        open(ENV_PATH, "w").close()
    set_key(ENV_PATH, key, value)

def render():
    page_header("⚙️", "Settings", "Enter your API keys — saved locally, never sent anywhere")

    # Always load fresh from file, never prefill with existing values
    # This keeps credentials private — user must re-enter if they want to change

    # ── Step 1: AI Model ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:700;
                color:#60A5FA; margin:0.5rem 0 0.3rem 0;">
        Step 1 — AI Model
        <span style="font-size:0.75rem; opacity:0.5; font-weight:400;"> (pick one)</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 How to get a free Gemini key", expanded=False):
        st.markdown("""
        1. Go to [aistudio.google.com](https://aistudio.google.com/app/apikey)
        2. Sign in with Google
        3. Click **Create API Key**
        4. Copy and paste it below

        Free tier: **60 requests/minute** — more than enough.
        """)

    with st.expander("📖 How to get an OpenRouter key (optional)", expanded=False):
        st.markdown("""
        1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
        2. Create a free account → click **Create Key**
        3. Paste below

        Use this to access GPT-4o, Claude, or Mistral instead of Gemini.
        If both keys are set, OpenRouter takes priority.
        """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Google Gemini** *(recommended, free)*")
        google_key = st.text_input("Google API Key",
                                    type="password",
                                    placeholder="Paste your Gemini key here",
                                    label_visibility="collapsed")
    with col2:
        st.markdown("**OpenRouter** *(optional)*")
        openrouter_key = st.text_input("OpenRouter Key",
                                        type="password",
                                        placeholder="Paste your OpenRouter key here",
                                        label_visibility="collapsed")

    selected_model = "openai/gpt-4o-mini"
    if openrouter_key:
        model_options = {
            "openai/gpt-4o-mini":            "GPT-4o Mini (cheap + fast)",
            "openai/gpt-4o":                 "GPT-4o (most capable)",
            "anthropic/claude-3-haiku":      "Claude 3 Haiku",
            "mistralai/mistral-7b-instruct": "Mistral 7B (free tier)",
        }
        selected_model = st.selectbox(
            "Model to use",
            options=list(model_options.keys()),
            format_func=lambda x: model_options[x]
        )

    st.markdown("---")

    # ── Step 2: Notion ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:700;
                color:#A78BFA; margin:0.5rem 0 0.3rem 0;">
        Step 2 — Notion
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 Step by step Notion setup", expanded=False):
        st.markdown("""
        **Get your Integration Token:**
        1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
        2. Click **+ New integration** → name it anything → Submit
        3. Copy the token (starts with `ntn_`)

        **Get your Page ID:**
        1. Create a new Notion page — e.g. "YouTube Notes Hub"
        2. URL looks like: `notion.so/YouTube-Notes-Hub-abc123def456...`
        3. Copy the last 32 characters — that's your Page ID

        **Connect integration to your page:**
        1. Open your Notion page
        2. Click `...` top right → **Connections** → find your integration → **Connect**
        3. ⚠️ Skip this and nothing will push to Notion
        """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Notion Integration Token**")
        notion_token = st.text_input("Notion Token",
                                      type="password",
                                      placeholder="Paste your ntn_... token here",
                                      label_visibility="collapsed")
    with col2:
        st.markdown("**Notion Parent Page ID**")
        notion_page_id = st.text_input("Page ID",
                                        placeholder="32-character ID from your page URL",
                                        label_visibility="collapsed")

    st.markdown("---")

    # ── Save + Test ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Settings", use_container_width=True, type="primary"):
            saved = []
            if google_key:
                save_env_value("GOOGLE_API_KEY", google_key)
                saved.append("Gemini key")
            if openrouter_key:
                save_env_value("OPENROUTER_API_KEY", openrouter_key)
                save_env_value("OPENROUTER_MODEL", selected_model)
                saved.append("OpenRouter key")
            if notion_token:
                save_env_value("NOTION_TOKEN", notion_token)
                saved.append("Notion token")
            if notion_page_id:
                save_env_value("NOTION_PAGE_ID", notion_page_id)
                saved.append("Notion page ID")

            load_dotenv(override=True)

            if saved:
                st.markdown(f'<div class="notify notify-success">✅ Saved: {", ".join(saved)}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<div class="notify notify-error">Nothing to save — fill in at least one field.</div>',
                            unsafe_allow_html=True)

    with col2:
        if st.button("🔌 Test Connections", use_container_width=True):
            load_dotenv(override=True)
            results = []

            gkey = os.getenv("GOOGLE_API_KEY")
            if gkey:
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0).invoke("say ok")
                    results.append(("✅", "Gemini connected"))
                except Exception as e:
                    results.append(("❌", f"Gemini: {str(e)[:80]}"))

            orkey = os.getenv("OPENROUTER_API_KEY")
            if orkey:
                try:
                    from langchain_openai import ChatOpenAI
                    ChatOpenAI(model="openai/gpt-4o-mini", api_key=orkey,
                               base_url="https://openrouter.ai/api/v1",
                               temperature=0).invoke("say ok")
                    results.append(("✅", "OpenRouter connected"))
                except Exception as e:
                    results.append(("❌", f"OpenRouter: {str(e)[:80]}"))

            ntoken = os.getenv("NOTION_TOKEN")
            if ntoken:
                try:
                    import requests
                    r = requests.get("https://api.notion.com/v1/users/me",
                                     headers={"Authorization": f"Bearer {ntoken}",
                                              "Notion-Version": "2022-06-28"})
                    if r.status_code == 200:
                        results.append(("✅", "Notion connected"))
                    else:
                        results.append(("❌", f"Notion: {r.json().get('message')}"))
                except Exception as e:
                    results.append(("❌", f"Notion: {e}"))

            if not results:
                st.markdown('<div class="notify notify-error">No keys saved yet — save first, then test.</div>',
                            unsafe_allow_html=True)
            for icon, msg in results:
                cls = "notify-success" if icon == "✅" else "notify-error"
                st.markdown(f'<div class="notify {cls}">{icon} {msg}</div>',
                            unsafe_allow_html=True)

    st.markdown("---")

    # ── Status — using native Streamlit columns, no f-string HTML ────────────
    load_dotenv(override=True)

    has_ai     = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    has_ntoken = bool(os.getenv("NOTION_TOKEN"))
    has_npage  = bool(os.getenv("NOTION_PAGE_ID"))
    all_good   = has_ai and has_ntoken and has_npage

    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:0.75rem; font-weight:700;
                opacity:0.4; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.8rem;">
        Current Status
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, label, ok in [(c1, "AI Key", has_ai), (c2, "Notion Token", has_ntoken), (c3, "Notion Page", has_npage)]:
        with col:
            st.markdown(f"""
            <div class="metric-box">
                <div style="font-size:1.4rem;">{"🟢" if ok else "🔴"}</div>
                <div class="lbl" style="margin-top:4px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    if all_good:
        st.markdown('<div class="notify notify-success" style="text-align:center; margin-top:1rem;">✅ All set! Go process a video.</div>',
                    unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎬 Go to YouTube Mode →", use_container_width=True):
                st.session_state.page = "youtube"
                st.rerun()