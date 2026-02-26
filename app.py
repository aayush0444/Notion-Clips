import streamlit as st

st.set_page_config(
    page_title="NotionClip — YouTube to Notion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --blue:        #60A5FA;
    --blue-deep:   #3B82F6;
    --purple:      #A78BFA;
    --purple-deep: #7C3AED;
    --glow-blue:   rgba(96,165,250,0.18);
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3,h4,h5,h6         { font-family: 'Syne', sans-serif !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a14 0%, #0f0d1a 100%);
    border-right: 1px solid rgba(96,165,250,0.1);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; }

.grad-text {
    background: linear-gradient(135deg, var(--blue) 0%, var(--purple) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.card {
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid rgba(96,165,250,0.13);
    background: rgba(15,15,26,0.6);
    backdrop-filter: blur(12px);
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: rgba(96,165,250,0.3); }

.metric-row  { display:flex; gap:1rem; margin:1rem 0; flex-wrap:wrap; }
.metric-box  {
    flex: 1; min-width: 110px;
    background: linear-gradient(135deg, rgba(96,165,250,0.07), rgba(167,139,250,0.07));
    border: 1px solid rgba(167,139,250,0.18);
    border-radius: 12px; padding: 1rem; text-align: center;
}
.metric-box .val {
    font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(135deg, var(--blue), var(--purple));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.metric-box .lbl {
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.08em; opacity: 0.5; margin-top: 2px;
}

.badge { display:inline-block; padding:2px 10px; border-radius:20px;
         font-size:0.72rem; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; }
.badge-high   { background:rgba(239,68,68,0.15);  color:#f87171; border:1px solid rgba(239,68,68,0.3); }
.badge-medium { background:rgba(234,179,8,0.15);  color:#fbbf24; border:1px solid rgba(234,179,8,0.3); }
.badge-low    { background:rgba(34,197,94,0.15);  color:#4ade80; border:1px solid rgba(34,197,94,0.3); }

.stButton > button {
    background: linear-gradient(135deg, var(--blue-deep), var(--purple-deep)) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    box-shadow: 0 4px 20px rgba(96,165,250,0.18) !important;
    transition: opacity 0.2s, transform 0.1s !important;
}
.stButton > button:hover { opacity: 0.87 !important; transform: translateY(-1px) !important; }

.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(15,15,26,0.8) !important;
    border: 1px solid rgba(96,165,250,0.18) !important;
    border-radius: 10px !important; color: #e2e8f0 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 2px var(--glow-blue) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,15,26,0.4) !important; border-radius: 10px !important;
    padding: 4px !important; border: 1px solid rgba(96,165,250,0.1) !important; gap:4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important; color: rgba(226,232,240,0.5) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--blue-deep), var(--purple-deep)) !important;
    color: white !important;
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--blue), var(--purple)) !important;
}

hr { border-color: rgba(96,165,250,0.1) !important; }

.streamlit-expanderHeader {
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    color: var(--blue) !important; background: rgba(96,165,250,0.05) !important;
    border-radius: 8px !important;
}

.task-row {
    display:flex; align-items:center; gap:1rem; padding:0.7rem 1rem;
    border-radius:10px; border:1px solid rgba(96,165,250,0.1);
    margin-bottom:0.5rem; background:rgba(15,15,26,0.4); transition:background 0.15s;
}
.task-row:hover { background: rgba(96,165,250,0.06); }
.task-name { flex:3; font-size:0.88rem; color:#e2e8f0; }
.task-meta { flex:1; font-size:0.76rem; color:rgba(226,232,240,0.45); }

.notify { padding:0.75rem 1.1rem; border-radius:10px; margin:0.5rem 0; font-size:0.86rem; }
.notify-success { background:rgba(34,197,94,0.1);  border:1px solid rgba(34,197,94,0.25);  color:#4ade80; }
.notify-error   { background:rgba(239,68,68,0.1);  border:1px solid rgba(239,68,68,0.25);  color:#f87171; }
.notify-info    { background:rgba(96,165,250,0.1); border:1px solid rgba(96,165,250,0.25); color:var(--blue); }

.orb { position:fixed; border-radius:50%; filter:blur(90px); pointer-events:none; z-index:-1; }
.orb-1 { width:450px; height:450px; background:rgba(59,130,246,0.05);  top:-120px; right:-100px; }
.orb-2 { width:350px; height:350px; background:rgba(124,58,237,0.05);  bottom:40px; left:-80px; }
</style>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
""", unsafe_allow_html=True)

# ── Session defaults ───────────────────────────────────────────────────────────
for key, val in {"page": "home", "history": [], "last_result": None}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 1.5rem 0;">
        <div style="font-family:'Syne',sans-serif; font-size:1.25rem; font-weight:800;
                    background:linear-gradient(135deg,#60A5FA,#A78BFA);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    background-clip:text;">
            🧠 NotionClip
        </div>
        <div style="font-size:0.7rem; opacity:0.35; letter-spacing:0.1em;
                    text-transform:uppercase; margin-top:3px;">
            YouTube → Notion
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation — YouTube only (no Meeting Mode in deployed version)
    pages = {
        "home":     ("🏠", "Home"),
        "youtube":  ("🎬", "YouTube Mode"),
        "history":  ("📋", "History"),
        "settings": ("⚙️", "Settings"),
    }

    for key, (icon, label) in pages.items():
        is_active = st.session_state.page == key
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")

    # Connection status
    import os
    from dotenv import load_dotenv
    load_dotenv()

    has_ai     = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    has_notion = bool(os.getenv("NOTION_TOKEN") and os.getenv("NOTION_PAGE_ID"))

    st.markdown(f"""
    <div style="font-size:0.75rem; opacity:0.5; padding:0 0.4rem;">
        <div style="margin-bottom:5px;">{'🟢' if has_ai     else '🔴'} AI Model</div>
        <div>                          {'🟢' if has_notion  else '🔴'} Notion</div>
    </div>
    """, unsafe_allow_html=True)

    if not (has_ai and has_notion):
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚙️ Setup Keys", use_container_width=True, key="sidebar_settings"):
            st.session_state.page = "settings"
            st.rerun()

# ── Page Router ────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "home":
    from pages_ui.home     import render
elif page == "youtube":
    from pages_ui.youtube  import render
elif page == "history":
    from pages_ui.history  import render
elif page == "settings":
    from pages_ui.settings import render
else:
    from pages_ui.home     import render

render()