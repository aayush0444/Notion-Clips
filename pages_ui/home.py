import streamlit as st


def render():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    has_ai     = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    has_notion = bool(os.getenv("NOTION_TOKEN") and os.getenv("NOTION_PAGE_ID"))
    is_ready   = has_ai and has_notion

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:2.5rem 0 1.5rem 0;">
        <div style="font-family:'Syne',sans-serif; font-size:2.8rem; font-weight:800;
                    background:linear-gradient(135deg,#60A5FA 0%,#A78BFA 100%);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    background-clip:text; line-height:1.15; margin-bottom:1rem;">
            Stop Watching.<br>Start Knowing.
        </div>
        <div style="font-size:1rem; opacity:0.55; max-width:500px; margin:0 auto;
                    line-height:1.8; font-family:'DM Sans',sans-serif;">
            Paste any YouTube URL — get a structured summary, key takeaways,
            and action items pushed straight to your Notion workspace.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA ───────────────────────────────────────────────────────────────────
    if not is_ready:
        st.markdown("""
        <div class="notify notify-info" style="text-align:center; max-width:560px; margin:0 auto 1rem auto;">
            👋 <b>First time?</b> Go to ⚙️ Settings, enter your API keys — takes 2 minutes.
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("⚙️ Go to Settings", use_container_width=True):
                st.session_state.page = "settings"
                st.rerun()
    else:
        st.markdown("""
        <div class="notify notify-success" style="text-align:center; max-width:560px; margin:0 auto 1rem auto;">
            ✅ You're all set! Paste a YouTube URL and go.
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎬 Process a Video →", use_container_width=True):
                st.session_state.page = "youtube"
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:0.75rem; font-weight:700;
                opacity:0.35; text-transform:uppercase; letter-spacing:0.12em;
                text-align:center; margin-bottom:1.5rem;">
        How it works
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    steps = [
        ("🔗", "#60A5FA", "1. Paste URL",       "Any YouTube link or video ID"),
        ("🤖", "#60A5FA", "2. AI Extracts",     "Gemini reads the transcript"),
        ("✨", "#A78BFA", "3. You Review",       "See summary, takeaways, tasks"),
        ("📓", "#A78BFA", "4. Saved to Notion",  "One click, structured page"),
    ]

    for col, (icon, color, title, desc) in zip([col1, col2, col3, col4], steps):
        with col:
            st.markdown(f"""
            <div style="text-align:center; padding:1.2rem 0.8rem; border-radius:14px;
                        border:1px solid rgba(96,165,250,0.12);
                        background:rgba(96,165,250,0.04);">
                <div style="font-size:1.6rem; margin-bottom:0.5rem;">{icon}</div>
                <div style="font-family:'Syne',sans-serif; font-size:0.82rem; font-weight:700;
                            color:{color}; margin-bottom:0.3rem;">{title}</div>
                <div style="font-size:0.75rem; opacity:0.45; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────────────────────────────────────
    history  = st.session_state.get("history", [])
    videos   = len(history)
    tasks    = sum(h.get("task_count", 0) for h in history)
    avg_time = (sum(h.get("processing_time", 0) for h in history) / videos) if videos else 0

    st.markdown(f"""
    <div class="metric-row" style="justify-content:center; max-width:500px; margin:0 auto;">
        <div class="metric-box">
            <div class="val">{videos}</div>
            <div class="lbl">Videos Processed</div>
        </div>
        <div class="metric-box">
            <div class="val">{tasks}</div>
            <div class="lbl">Tasks Extracted</div>
        </div>
        <div class="metric-box">
            <div class="val">{f"{avg_time:.0f}s" if avg_time else "—"}</div>
            <div class="lbl">Avg Process Time</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── What you get ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:0.75rem; font-weight:700;
                opacity:0.35; text-transform:uppercase; letter-spacing:0.12em;
                text-align:center; margin-bottom:1.2rem;">
        What you get from every video
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("📝", "#60A5FA", "Summary",       "3-4 sentence executive summary of the entire video"),
        ("💡", "#A78BFA", "Key Takeaways", "Up to 7 most important points worth remembering"),
        ("📚", "#60A5FA", "Topics Covered","Main sections and subjects the video covers"),
        ("✅", "#A78BFA", "Action Items",  "Things to do or explore after watching"),
    ]

    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, color, title, desc) in zip([c1, c2, c3, c4], features):
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center; padding:1.2rem 1rem;">
                <div style="font-size:1.4rem; margin-bottom:0.4rem;">{icon}</div>
                <div style="color:{color}; font-weight:700; font-family:'Syne',sans-serif;
                            font-size:0.85rem; margin-bottom:0.3rem;">{title}</div>
                <div style="font-size:0.78rem; opacity:0.5; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)