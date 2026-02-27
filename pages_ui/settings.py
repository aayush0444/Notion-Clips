import os
import requests
import streamlit as st
from dotenv import load_dotenv, set_key, dotenv_values
from pages_ui.components import page_header

ENV_PATH = ".env"

def save_env_value(key, value):
    if not os.path.exists(ENV_PATH):
        open(ENV_PATH, "w").close()
    set_key(ENV_PATH, key, value)

def get_app_key_status():
    """
    Check if app's shared OpenRouter key exists in Streamlit secrets.
    Returns True/False only — never returns the actual key value.
    The key itself never leaves the server.
    """
    try:
        return bool(st.secrets.get("OPENROUTER_API_KEY", ""))
    except Exception:
        return False

def render():
    page_header("⚙️", "Settings", "Just connect Notion — AI is already set up for you")

    app_has_key = get_app_key_status()

    # ── AI Section ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:700;
                color:#60A5FA; margin:0.5rem 0 0.8rem 0;">
        🤖 AI Model
    </div>
    """, unsafe_allow_html=True)

    if app_has_key:
        # Show it's provided — but NEVER show the key value
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            <div style="background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(124,58,237,0.08));
                        border:1px solid rgba(96,165,250,0.25); border-radius:12px;
                        padding:1rem 1.2rem;">
                <div style="font-family:'Syne',sans-serif; font-weight:700;
                            color:#60A5FA; margin-bottom:0.3rem;">
                    ✅ OpenRouter — Provided by NotionClip
                </div>
                <div style="font-size:0.8rem; opacity:0.55; line-height:1.6;">
                    AI is powered by OpenRouter and pre-configured.<br>
                    You don't need your own API key.
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            # Show masked key — looks like a key field but value is always hidden dots
            # The actual key is NEVER passed to this input — just asterisks as placeholder
            st.markdown("<br>", unsafe_allow_html=True)
            st.text_input(
                "API Key",
                value="",
                placeholder="sk-or-••••••••••••••••",
                disabled=True,        # cannot click, cannot type, cannot copy
                label_visibility="collapsed",
                help="This key is managed by NotionClip and is not accessible to users."
            )

        st.markdown("""
        <div style="font-size:0.78rem; opacity:0.4; margin-top:0.5rem; margin-left:0.2rem;">
            🔒 Key is server-side only — not visible or copyable for security.
        </div>
        """, unsafe_allow_html=True)

    else:
        # Running locally without app key — show input fields
        st.markdown("""
        <div class="notify notify-info">
            Running locally? Add your own Gemini or OpenRouter key below.
            On the hosted version at notionclip.streamlit.app, AI is pre-provided.
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📖 How to get a free Gemini key", expanded=False):
            st.markdown("""
            1. Go to [aistudio.google.com](https://aistudio.google.com/app/apikey)
            2. Sign in with Google → **Create API Key**
            3. Copy and paste below
            """)

        with st.expander("📖 Or use OpenRouter (GPT-4o, Claude, Mistral)", expanded=False):
            st.markdown("""
            1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
            2. Create free account → **Create Key** → paste below
            """)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Google Gemini** *(free)*")
            google_key = st.text_input("Gemini Key", type="password",
                                        placeholder="AIza...",
                                        label_visibility="collapsed")
        with col2:
            st.markdown("**OpenRouter** *(optional)*")
            openrouter_key = st.text_input("OpenRouter Key", type="password",
                                            placeholder="sk-or-...",
                                            label_visibility="collapsed")

    st.markdown("---")

    # ── Notion Setup ──────────────────────────────────────────────────────────
    step_label = "Step 1" if app_has_key else "Step 2"

    st.markdown(f"""
    <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:700;
                color:#A78BFA; margin:0.5rem 0 0.8rem 0;">
        📓 {step_label} — Connect Notion
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 How to set up Notion (3 quick steps)", expanded=False):
        st.markdown("""
        **1. Create an Integration**
        - Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
        - Click **+ New integration** → name it anything → Submit
        - Copy the token — starts with `ntn_`

        **2. Get your Page ID**
        - Create a new Notion page — e.g. *"YouTube Notes"*
        - URL: `notion.so/YouTube-Notes-abc123def456...`
        - Last 32 characters = your Page ID

        **3. Connect integration to your page**
        - Open your Notion page → click `...` top right
        - → **Connections** → find your integration → **Connect**
        - ⚠️ Skip this and pushes will fail
        """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Notion Integration Token**")
        notion_token = st.text_input(
            "Notion Token",
            type="password",
            placeholder="ntn_...",
            label_visibility="collapsed"
        )
    with col2:
        st.markdown("**Notion Parent Page ID**")
        notion_page_id = st.text_input(
            "Page ID",
            placeholder="32-character ID from page URL",
            label_visibility="collapsed"
        )

    st.markdown("---")

    # ── Save + Test ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Settings", use_container_width=True, type="primary"):
            saved = []

            # Only save AI keys if app key not provided (local use)
            if not app_has_key:
                if "google_key" in dir() and google_key:
                    save_env_value("GOOGLE_API_KEY", google_key)
                    saved.append("Gemini key")
                if "openrouter_key" in dir() and openrouter_key:
                    save_env_value("OPENROUTER_API_KEY", openrouter_key)
                    saved.append("OpenRouter key")

            if notion_token:
                save_env_value("NOTION_TOKEN", notion_token)
                saved.append("Notion token")
            if notion_page_id:
                save_env_value("NOTION_PAGE_ID", notion_page_id)
                saved.append("Notion page ID")

            load_dotenv(override=True)

            if saved:
                st.markdown(
                    f'<div class="notify notify-success">✅ Saved: {", ".join(saved)}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="notify notify-error">Nothing to save — fill in the Notion fields above.</div>',
                    unsafe_allow_html=True
                )

    with col2:
        if st.button("🔌 Test Connections", use_container_width=True):
            load_dotenv(override=True)
            results = []

            # Test AI — just check model loads, never expose key
            try:
                from gemini import get_model
                get_model().invoke("say ok")
                results.append(("✅", "AI model working"))
            except Exception as e:
                results.append(("❌", f"AI: {str(e)[:80]}"))

            # Test Notion
            ntoken = os.getenv("NOTION_TOKEN")
            if ntoken:
                try:
                    r = requests.get(
                        "https://api.notion.com/v1/users/me",
                        headers={
                            "Authorization": f"Bearer {ntoken}",
                            "Notion-Version": "2022-06-28"
                        }
                    )
                    if r.status_code == 200:
                        results.append(("✅", "Notion connected"))
                    else:
                        results.append(("❌", f"Notion: {r.json().get('message')}"))
                except Exception as e:
                    results.append(("❌", f"Notion: {e}"))
            else:
                results.append(("❌", "Notion token not saved yet"))

            for icon, msg in results:
                cls = "notify-success" if icon == "✅" else "notify-error"
                st.markdown(
                    f'<div class="notify {cls}">{icon} {msg}</div>',
                    unsafe_allow_html=True
                )

    st.markdown("---")

    # ── Status Indicators ─────────────────────────────────────────────────────
    load_dotenv(override=True)

    has_ai     = app_has_key or bool(
                    os.getenv("GOOGLE_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    has_ntoken = bool(os.getenv("NOTION_TOKEN"))
    has_npage  = bool(os.getenv("NOTION_PAGE_ID"))
    all_good   = has_ai and has_ntoken and has_npage

    c1, c2, c3 = st.columns(3)
    for col, label, ok in [
        (c1, "AI Model",     has_ai),
        (c2, "Notion Token", has_ntoken),
        (c3, "Notion Page",  has_npage)
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-box">
                <div style="font-size:1.4rem;">{"🟢" if ok else "🔴"}</div>
                <div class="lbl" style="margin-top:4px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    if all_good:
        st.markdown("""
        <div class="notify notify-success" style="text-align:center; margin-top:1rem;">
            ✅ All set! Go process a video.
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎬 Go to YouTube Mode →", use_container_width=True):
                st.session_state.page = "youtube"
                st.rerun()