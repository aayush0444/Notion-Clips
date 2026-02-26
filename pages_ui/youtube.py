import time
import streamlit as st
from pages_ui.components import page_header, render_youtube_result, save_to_history


def render():
    page_header("🎬", "YouTube Mode", "Paste any YouTube URL — get insights without watching")

    # ── URL Input ─────────────────────────────────────────────────────────────
    url_input = st.text_input(
        "YouTube URL or Video ID",
        placeholder="https://www.youtube.com/watch?v=... or paste a video ID",
        help="Supports all YouTube URL formats"
    )

    if url_input:
        # Try to show a preview embed
        from youtube_mode import extract_video_id
        video_id = extract_video_id(url_input.strip())
        st.markdown(f"""
        <div class="card" style="padding:0.8rem 1rem;">
            <div style="font-size:0.8rem; opacity:0.5;">Video ID detected:</div>
            <div style="font-family:'Syne',sans-serif; font-weight:700; color:#A78BFA;">
                {video_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Extract options ───────────────────────────────────────────────────────
    st.markdown("**What do you want to extract?**")

    col1, col2 = st.columns(2)
    with col1:
        get_insights = st.checkbox("💡 Key insights & takeaways", value=True,
                                    help="Summary, key points, topics covered, action items")
    with col2:
        get_tasks = st.checkbox("✅ Action items & tasks", value=False,
                                 help="Structured tasks with assignee, due date, priority")

    if not get_insights and not get_tasks:
        st.markdown('<div class="notify notify-error">Please select at least one extraction option.</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # ── Run button ────────────────────────────────────────────────────────────
    can_run = bool(url_input) and (get_insights or get_tasks)

    if st.button("🚀 Process Video", use_container_width=True, disabled=not can_run):
        with st.status("Processing YouTube video...", expanded=True) as status:
            try:
                from youtube_mode import extract_video_id, get_youtube_transcript
                from gemini import (extract_video_insights, extract_tasks,
                                    deduplicate_tasks, calculate_accuracy)

                video_id = extract_video_id(url_input.strip())

                st.write("📥 Fetching transcript from YouTube...")
                transcript, duration = get_youtube_transcript(video_id)

                start = time.time()

                insights  = None
                tasks_obj = None

                if get_insights:
                    st.write("🤖 Extracting key insights with Gemini...")
                    insights = extract_video_insights(transcript)

                if get_tasks:
                    st.write("📋 Extracting action items...")
                    raw = extract_tasks(transcript)
                    tasks_obj = deduplicate_tasks(raw)

                # If only tasks, create minimal insights for Notion title
                if get_tasks and not get_insights:
                    from models import VideoInsights
                    insights = VideoInsights(
                        title=f"Video {video_id}",
                        summary="Task extraction mode.",
                        key_takeaways=[], topics_covered=[], action_items=[]
                    )

                proc_time = time.time() - start
                accuracy  = calculate_accuracy(tasks_obj) if tasks_obj else 0

                result = {
                    "insights":        insights,
                    "tasks":           tasks_obj,
                    "accuracy":        accuracy,
                    "processing_time": proc_time,
                    "duration":        duration,
                    "url":             url_input,
                }
                st.session_state["youtube_result"] = result
                status.update(label=f"✅ Done in {proc_time:.1f}s!", state="complete")

            except Exception as e:
                status.update(label=f"❌ Error: {e}", state="error")
                st.exception(e)

    # ── Results ───────────────────────────────────────────────────────────────
    result = st.session_state.get("youtube_result")
    if result:
        st.markdown("---")
        st.markdown("""
        <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700;
                    color:#A78BFA; margin-bottom:1rem;">📊 Results</div>
        """, unsafe_allow_html=True)

        render_youtube_result(result)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Push to Notion", use_container_width=True):
                with st.status("Pushing to Notion...", expanded=True) as status:
                    try:
                        from push_to_notion import push_youtube
                        push_youtube(result["insights"], result["url"], result.get("tasks"))
                        status.update(label="✅ Pushed to Notion!", state="complete")
                        title = result["insights"].title if result.get("insights") else "YouTube Video"
                        save_to_history("youtube", title, result)
                        st.markdown('<div class="notify notify-success">✅ Successfully saved to Notion!</div>',
                                    unsafe_allow_html=True)
                    except Exception as e:
                        status.update(label=f"❌ {e}", state="error")
        with col2:
            if st.button("🗑️ Clear & Process Another", use_container_width=True):
                if "youtube_result" in st.session_state:
                    del st.session_state["youtube_result"]
                st.rerun()