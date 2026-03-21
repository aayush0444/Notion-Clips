import time
import streamlit as st
from pages_ui.components import page_header, render_youtube_result, save_to_history


# ─── Preference helpers ───────────────────────────────────────────────────────

def load_preferences():
    """Load saved preferences from session state or return defaults."""
    return st.session_state.get("output_prefs", {
        "mode":          "study",
        "summary":       True,
        "key_takeaways": True,
        "topics":        True,
        "action_items":  True,
        "get_tasks":     False,
    })


def save_preferences(prefs: dict):
    """Persist preferences to session state."""
    st.session_state["output_prefs"] = prefs


# ─── Mode descriptions shown in UI ───────────────────────────────────────────

MODE_INFO = {
    "study": {
        "icon":  "📚",
        "label": "Study Mode",
        "desc":  "Technical depth. Preserves exact terms, formulas, definitions. For lectures, tutorials, courses.",
        "color": "#60A5FA",
    },
    "work": {
        "icon":  "💼",
        "label": "Work Mode",
        "desc":  "What your team needs to know. Tools, recommendations, decisions. For tech talks, industry videos.",
        "color": "#A78BFA",
    },
    "quick": {
        "icon":  "⚡",
        "label": "Quick Mode",
        "desc":  "The gist in 60 seconds. Conversational, no jargon. For news, docs, general interest videos.",
        "color": "#34D399",
    },
}


def render():
    page_header("🎬", "YouTube Mode", "Paste any YouTube URL — get insights without watching")

    # ── Transcript source indicator ───────────────────────────────────────────
    from youtube_mode import get_transcript_source_info
    source_info = get_transcript_source_info()
    st.markdown(f"""
    <div style="background:#0F0D1A; border:1px solid rgba(96,165,250,0.2);
                border-radius:10px; padding:0.6rem 1rem; margin-bottom:1rem;
                font-size:0.82rem; color:#94A3B8;">
        📡  <b style="color:#60A5FA;">Transcript sources:</b>&nbsp;{source_info}
    </div>
    """, unsafe_allow_html=True)

    # ── URL Input ─────────────────────────────────────────────────────────────
    url_input = st.text_input(
        "YouTube URL or Video ID",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Supports all YouTube URL formats"
    )

    if url_input:
        from youtube_mode import extract_video_id
        video_id = extract_video_id(url_input.strip())
        st.markdown(f"""
        <div class="card" style="padding:0.7rem 1rem;">
            <div style="font-size:0.78rem; opacity:0.5;">Video ID detected:</div>
            <div style="font-family:'Syne',sans-serif; font-weight:700; color:#A78BFA;">
                {video_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════
    # OUTPUT PREFERENCES PANEL
    # ═══════════════════════════════════════════════════════════════════════
    prefs = load_preferences()

    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:700;
                color:#60A5FA; margin-bottom:0.8rem;">
        📋 Output Preferences
    </div>
    """, unsafe_allow_html=True)

    # ── Level 2: Mode selector ────────────────────────────────────────────
    st.markdown("<div style='font-size:0.85rem; opacity:0.6; margin-bottom:0.5rem;'>Choose output style:</div>",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    selected_mode = prefs["mode"]

    for col, (mode_key, info) in zip([col1, col2, col3], MODE_INFO.items()):
        with col:
            is_selected = selected_mode == mode_key
            border_color = info["color"] if is_selected else "rgba(255,255,255,0.08)"
            bg_color = "1E1B4B" if is_selected else "0F0D1A"
            st.markdown(f"""
            <div style="border:2px solid {border_color}; border-radius:12px;
                        background:#{bg_color}; padding:0.8rem; text-align:center;
                        margin-bottom:0.4rem;">
                <div style="font-size:1.5rem;">{info['icon']}</div>
                <div style="font-family:'Syne',sans-serif; font-weight:700;
                            color:{info['color']}; font-size:0.88rem; margin:0.2rem 0;">
                    {info['label']}
                </div>
                <div style="font-size:0.75rem; opacity:0.55; line-height:1.4;">
                    {info['desc']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(
                "✓ Selected" if is_selected else "Select",
                key=f"mode_{mode_key}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                prefs["mode"] = mode_key
                save_preferences(prefs)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Level 1: Section toggles ──────────────────────────────────────────
    st.markdown("<div style='font-size:0.85rem; opacity:0.6; margin-bottom:0.5rem;'>Choose what appears in your Notion page:</div>",
                unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    section_cols = {
        "summary":       (c1, "📝 Summary"),
        "key_takeaways": (c2, "🔑 Takeaways"),
        "topics":        (c3, "📚 Topics"),
        "action_items":  (c4, "✅ Actions"),
        "get_tasks":     (c5, "🗂️ Task DB"),
    }

    for key, (col, label) in section_cols.items():
        with col:
            new_val = st.checkbox(label, value=prefs[key], key=f"sec_{key}")
            if new_val != prefs[key]:
                prefs[key] = new_val
                save_preferences(prefs)

    # Warn if nothing selected
    any_content = any([
        prefs["summary"], prefs["key_takeaways"],
        prefs["topics"], prefs["action_items"], prefs["get_tasks"]
    ])
    if not any_content:
        st.markdown('<div class="notify notify-error">Select at least one section to include in the output.</div>',
                    unsafe_allow_html=True)

    # Quick mode warning — sections auto-limited by the prompt
    if prefs["mode"] == "quick":
        st.markdown("""
        <div class="notify notify-info" style="margin-top:0.5rem;">
            ⚡ Quick Mode caps output regardless of section selection —
            2-sentence summary, 3 takeaways, minimal topics.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Run button ────────────────────────────────────────────────────────
    can_run = bool(url_input) and any_content
    mode_info = MODE_INFO[prefs["mode"]]

    if st.button(
        f"🚀 Process Video  [{mode_info['icon']} {mode_info['label']}]",
        use_container_width=True,
        disabled=not can_run
    ):
        with st.status("Processing YouTube video...", expanded=True) as status:
            try:
                from youtube_mode import extract_video_id, get_youtube_transcript
                from gemini import extract_video_insights, extract_tasks, deduplicate_tasks, calculate_accuracy

                video_id = extract_video_id(url_input.strip())

                st.write("📥 Fetching transcript...")
                transcript, duration = get_youtube_transcript(video_id)
                st.write(f"✅ Transcript ready — {len(transcript.split()):,} words")

                start = time.time()

                # Build sections dict for gemini
                sections = {
                    "summary":       prefs["summary"],
                    "key_takeaways": prefs["key_takeaways"],
                    "topics":        prefs["topics"],
                    "action_items":  prefs["action_items"],
                }

                st.write(f"{mode_info['icon']} Extracting insights in {mode_info['label']}...")
                insights = extract_video_insights(
                    transcript,
                    mode=prefs["mode"],
                    sections=sections
                )

                tasks_obj = None
                if prefs["get_tasks"]:
                    st.write("🗂️ Extracting tasks...")
                    raw = extract_tasks(transcript)
                    tasks_obj = deduplicate_tasks(raw)

                proc_time = time.time() - start
                accuracy  = calculate_accuracy(tasks_obj) if tasks_obj else 0

                result = {
                    "insights":        insights,
                    "tasks":           tasks_obj,
                    "accuracy":        accuracy,
                    "processing_time": proc_time,
                    "duration":        duration,
                    "url":             url_input,
                    "mode":            prefs["mode"],
                    "sections":        sections,
                }
                st.session_state["youtube_result"] = result
                status.update(label=f"✅ Done in {proc_time:.1f}s!", state="complete")

            except Exception as e:
                status.update(label="❌ Failed", state="error")
                st.markdown(f"""
                <div class="notify notify-error">
                    <b>Could not process this video</b><br>
                    <pre style="font-size:0.8rem; margin-top:0.5rem;
                                white-space:pre-wrap;">{str(e)}</pre>
                </div>
                """, unsafe_allow_html=True)

    # ── Results ───────────────────────────────────────────────────────────
    result = st.session_state.get("youtube_result")
    if result:
        st.markdown("---")

        # Show which mode was used
        used_mode = result.get("mode", "study")
        used_info = MODE_INFO.get(used_mode, MODE_INFO["study"])
        st.markdown(f"""
        <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700;
                    color:#A78BFA; margin-bottom:0.5rem;">📊 Results</div>
        <div style="font-size:0.8rem; color:{used_info['color']}; margin-bottom:1rem; opacity:0.8;">
            {used_info['icon']} Generated in {used_info['label']}
        </div>
        """, unsafe_allow_html=True)

        render_youtube_result(result)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Push to Notion", use_container_width=True):
                with st.status("Pushing to Notion...", expanded=True) as status:
                    try:
                        from push_to_notion import push_youtube
                        push_youtube(
                            result["insights"],
                            result["url"],
                            result.get("tasks"),
                            sections=result.get("sections", {})
                        )
                        status.update(label="✅ Pushed to Notion!", state="complete")
                        title = result["insights"].title if result.get("insights") else "YouTube Video"
                        save_to_history("youtube", title, result)
                        st.markdown('<div class="notify notify-success">✅ Saved to Notion!</div>',
                                    unsafe_allow_html=True)
                    except Exception as e:
                        status.update(label=f"❌ {e}", state="error")
        with col2:
            if st.button("🗑️ Clear & Process Another", use_container_width=True):
                if "youtube_result" in st.session_state:
                    del st.session_state["youtube_result"]
                st.rerun()