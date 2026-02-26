import streamlit as st
from pages_ui.components import page_header, render_meeting_result, render_youtube_result


def render():
    page_header("📋", "History", "All past runs — full results expandable")

    history = st.session_state.get("history", [])

    if not history:
        st.markdown("""
        <div style="text-align:center; padding:4rem 0; opacity:0.4;">
            <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
            <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:600;">
                No runs yet
            </div>
            <div style="font-size:0.85rem; margin-top:0.5rem;">
                Process a meeting or YouTube video to see history here
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Summary stats ─────────────────────────────────────────────────────────
    meetings   = sum(1 for h in history if h["mode"] == "meeting")
    videos     = sum(1 for h in history if h["mode"] == "youtube")
    total_tasks = sum(h.get("task_count", 0) for h in history)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{len(history)}</div><div class="lbl">Total Runs</div></div>
        <div class="metric-box"><div class="val">{meetings}</div><div class="lbl">Meetings</div></div>
        <div class="metric-box"><div class="val">{videos}</div><div class="lbl">Videos</div></div>
        <div class="metric-box"><div class="val">{total_tasks}</div><div class="lbl">Tasks Created</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Filter ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_mode = st.radio("Filter", ["All", "🎙️ Meetings", "🎬 YouTube"],
                               horizontal=True, label_visibility="collapsed")
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state["history"] = []
            st.rerun()

    # Apply filter
    filtered = history
    if "Meeting" in filter_mode:
        filtered = [h for h in history if h["mode"] == "meeting"]
    elif "YouTube" in filter_mode:
        filtered = [h for h in history if h["mode"] == "youtube"]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── History entries ───────────────────────────────────────────────────────
    for i, entry in enumerate(filtered):
        mode_icon  = "🎙️" if entry["mode"] == "meeting" else "🎬"
        mode_color = "#60A5FA" if entry["mode"] == "meeting" else "#A78BFA"
        task_count = entry.get("task_count", 0)
        proc_time  = entry.get("processing_time", 0)
        accuracy   = entry.get("accuracy", 0)

        with st.expander(
            f"{mode_icon}  {entry['title']}  ·  {entry['timestamp']}",
            expanded=False
        ):
            # Mini metrics
            st.markdown(f"""
            <div class="metric-row" style="margin-bottom:1rem;">
                <div class="metric-box">
                    <div class="val" style="font-size:1.2rem;">{entry['timestamp']}</div>
                    <div class="lbl">Timestamp</div>
                </div>
                <div class="metric-box">
                    <div class="val" style="font-size:1.2rem;">{task_count}</div>
                    <div class="lbl">Tasks</div>
                </div>
                <div class="metric-box">
                    <div class="val" style="font-size:1.2rem;">{proc_time:.1f}s</div>
                    <div class="lbl">Processed In</div>
                </div>
                {'<div class="metric-box"><div class="val" style="font-size:1.2rem;">' + str(accuracy) + '%</div><div class="lbl">Accuracy</div></div>' if entry["mode"] == "meeting" else ''}
            </div>
            """, unsafe_allow_html=True)

            # Full result
            result = entry.get("result", {})
            if result:
                if entry["mode"] == "meeting":
                    render_meeting_result(result)
                else:
                    render_youtube_result(result)

            # Re-push button
            if st.button(f"📤 Re-push to Notion", key=f"repush_{i}", use_container_width=True):
                with st.status("Pushing to Notion...", expanded=True) as status:
                    try:
                        if entry["mode"] == "meeting":
                            from push_to_notion import push_meeting
                            push_meeting(result["tasks"], result["summary"])
                        else:
                            from push_to_notion import push_youtube
                            push_youtube(result["insights"], result.get("url", ""), result.get("tasks"))
                        status.update(label="✅ Re-pushed to Notion!", state="complete")
                    except Exception as e:
                        status.update(label=f"❌ {e}", state="error")