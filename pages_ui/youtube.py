import time
import streamlit as st
from pages_ui.components import (
    page_header, render_youtube_result,
    render_study_notes, render_work_brief,
    save_to_history
)


# ─── Preference Helpers ───────────────────────────────────────────────────────

def load_preferences():
    return st.session_state.get("output_prefs", {
        "mode":          "study",
        "summary":       True,
        "key_takeaways": True,
        "topics":        True,
        "action_items":  True,
        "get_tasks":     False,
    })


def save_preferences(prefs: dict):
    st.session_state["output_prefs"] = prefs


# ─── Mode Info ────────────────────────────────────────────────────────────────

MODE_INFO = {
    "study": {
        "icon":  "📚",
        "label": "Study Mode",
        "desc":  (
            "For lectures, tutorials, courses. "
            "Extracts formulas, key facts with timestamps, self-test questions, "
            "and common mistakes. Scales to video length — a 2hr lecture gets ~40 facts."
        ),
        "color": "#60A5FA",
    },
    "work": {
        "icon":  "💼",
        "label": "Work Mode",
        "desc":  (
            "For tech talks, industry videos, team-relevant content. "
            "Watch/Skip verdict, named tools, decisions, specific next actions. "
            "Structured for sharing with your team."
        ),
        "color": "#A78BFA",
    },
    "quick": {
        "icon":  "⚡",
        "label": "Quick Mode",
        "desc":  (
            "For news, docs, general interest. "
            "Conversational summary — the gist in 2 minutes. "
            "No jargon, no structure overhead."
        ),
        "color": "#34D399",
    },
}


def render():
    page_header("🎬", "YouTube Mode", "Paste any YouTube URL — get insights without watching")

    # Transcript source indicator
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

    # ═══════════════════════════════════════════════════════════════════════════
    # OUTPUT PREFERENCES
    # ═══════════════════════════════════════════════════════════════════════════
    prefs = load_preferences()

    st.markdown("""
    <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:700;
                color:#60A5FA; margin-bottom:0.8rem;">
        📋 Output Preferences
    </div>
    """, unsafe_allow_html=True)

    # Mode selector
    st.markdown(
        "<div style='font-size:0.85rem; opacity:0.6; margin-bottom:0.5rem;'>Choose output style:</div>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    selected_mode = prefs["mode"]

    for col, (mode_key, info) in zip([col1, col2, col3], MODE_INFO.items()):
        with col:
            is_selected  = selected_mode == mode_key
            border_color = info["color"] if is_selected else "rgba(255,255,255,0.08)"
            bg_hex       = "1E1B4B" if is_selected else "0F0D1A"
            st.markdown(f"""
            <div style="border:2px solid {border_color}; border-radius:12px;
                        background:#{bg_hex}; padding:0.8rem; text-align:center;
                        margin-bottom:0.4rem;">
                <div style="font-size:1.5rem;">{info['icon']}</div>
                <div style="font-family:'Syne',sans-serif; font-weight:700;
                            color:{info['color']}; font-size:0.88rem; margin:0.2rem 0;">
                    {info['label']}
                </div>
                <div style="font-size:0.73rem; opacity:0.55; line-height:1.4;">
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

    # Section toggles (shown for Quick mode only — Study/Work have fixed sections)
    if prefs["mode"] == "quick":
        st.markdown(
            "<div style='font-size:0.85rem; opacity:0.6; margin-bottom:0.5rem;'>Choose sections:</div>",
            unsafe_allow_html=True
        )
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

        any_content = any([
            prefs["summary"], prefs["key_takeaways"],
            prefs["topics"], prefs["action_items"], prefs["get_tasks"]
        ])
        if not any_content:
            st.markdown('<div class="notify notify-error">Select at least one section.</div>',
                        unsafe_allow_html=True)
    else:
        # Study / Work modes — show what will be extracted
        mode_info = MODE_INFO[prefs["mode"]]
        if prefs["mode"] == "study":
            st.markdown(f"""
            <div class="notify notify-info">
                {mode_info['icon']} Study Mode will extract:
                <b>Core Concept · Formula Sheet · Key Facts (scaled to video length) ·
                Common Mistakes · Self-Test Questions · Prerequisites · Further Reading</b><br>
                <span style="opacity:0.7;">
                A 10-min video gets ~8 facts. A 2-hour lecture gets ~40 facts with timestamps.
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="notify notify-info">
                {mode_info['icon']} Work Mode will extract:
                <b>Watch/Skip Verdict · One-Liner Summary · Key Points (scaled) ·
                Tools Mentioned · Decisions to Make · Next Actions</b><br>
                <span style="opacity:0.7;">
                Output scales to video length. Long videos get proportionally more points.
                </span>
            </div>
            """, unsafe_allow_html=True)
        any_content = True

    st.markdown("---")

    # ── Run Button ────────────────────────────────────────────────────────────
    can_run   = bool(url_input) and any_content
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

                word_count = len(transcript.split())
                st.write(f"✅ Transcript ready — {word_count:,} words (~{duration:.0f} min video)")

                # Warn about chunked processing for long videos
                if word_count > 8000:
                    st.write(
                        f"📦 Long video detected — using chunked extraction "
                        f"({word_count // 4000 + 1} passes) to prevent hallucination..."
                    )

                start = time.time()

                # Build sections dict for quick mode
                sections = {
                    "summary":       prefs.get("summary", True),
                    "key_takeaways": prefs.get("key_takeaways", True),
                    "topics":        prefs.get("topics", True),
                    "action_items":  prefs.get("action_items", True),
                }

                st.write(f"{mode_info['icon']} Extracting with {mode_info['label']}...")
                insights = extract_video_insights(
                    transcript,
                    mode=prefs["mode"],
                    sections=sections,
                    duration_minutes=duration
                )

                tasks_obj = None
                if prefs.get("get_tasks") and prefs["mode"] == "quick":
                    st.write("🗂️ Extracting tasks...")
                    raw       = extract_tasks(transcript)
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
                    "word_count":      word_count,
                }
                st.session_state["youtube_result"] = result
                status.update(label=f"✅ Done in {proc_time:.1f}s!", state="complete")

            except Exception as e:
                status.update(label="❌ Failed", state="error")
                st.markdown(f"""
                <div class="notify notify-error">
                    <b>Could not process this video.</b><br>
                    <pre style="font-size:0.8rem; margin-top:0.5rem;
                                white-space:pre-wrap;">{str(e)}</pre>
                </div>
                """, unsafe_allow_html=True)

    # ── Results ───────────────────────────────────────────────────────────────
    result = st.session_state.get("youtube_result")
    if result:
        st.markdown("---")

        used_mode = result.get("mode", "quick")
        used_info = MODE_INFO.get(used_mode, MODE_INFO["quick"])
        word_count = result.get("word_count", 0)

        st.markdown(f"""
        <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700;
                    color:#A78BFA; margin-bottom:0.3rem;">📊 Results</div>
        <div style="font-size:0.8rem; color:{used_info['color']}; margin-bottom:1rem; opacity:0.8;">
            {used_info['icon']} {used_info['label']} ·
            {word_count:,} words processed ·
            {"chunked extraction" if word_count > 8000 else "single-pass extraction"}
        </div>
        """, unsafe_allow_html=True)

        # Route to the correct renderer
        if used_mode == "study":
            render_study_notes(result)
        elif used_mode == "work":
            render_work_brief(result)
        else:
            render_youtube_result(result)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Push to Notion", use_container_width=True):
                with st.status("Pushing to Notion...", expanded=True) as status:
                    try:
                        if used_mode == "study":
                            from push_to_notion import push_study_notes
                            push_study_notes(result["insights"], result["url"])

                        elif used_mode == "work":
                            from push_to_notion import push_work_brief
                            push_work_brief(result["insights"], result["url"])

                        else:
                            from push_to_notion import push_youtube
                            push_youtube(
                                result["insights"],
                                result["url"],
                                result.get("tasks"),
                                sections=result.get("sections", {})
                            )

                        status.update(label="✅ Pushed to Notion!", state="complete")

                        # Build title for history
                        insights = result.get("insights")
                        title = getattr(insights, "title", "YouTube Video") or "YouTube Video"
                        save_to_history("youtube", title, result)

                        st.markdown(
                            '<div class="notify notify-success">✅ Saved to Notion!</div>',
                            unsafe_allow_html=True
                        )

                    except Exception as e:
                        status.update(label=f"❌ {e}", state="error")

        with col2:
            if st.button("🗑️ Clear & Process Another", use_container_width=True):
                if "youtube_result" in st.session_state:
                    del st.session_state["youtube_result"]
                st.rerun()