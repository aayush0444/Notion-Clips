import streamlit as st
from datetime import datetime


def page_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin-bottom:2rem;">
        <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800;
                    display:flex; align-items:center; gap:0.6rem;">
            <span>{icon}</span>
            <span style="background:linear-gradient(135deg,#60A5FA,#A78BFA);
                         -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                         background-clip:text;">{title}</span>
        </div>
        {f'<div style="font-size:0.88rem; opacity:0.5; margin-top:4px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def badge(priority: str) -> str:
    cls = f"badge-{priority.lower()}"
    return f'<span class="badge {cls}">{priority}</span>'


def render_tasks(tasks):
    """Render a list of ActionItem objects as a nice task table."""
    if not tasks:
        st.markdown('<div class="notify notify-info">No tasks found.</div>', unsafe_allow_html=True)
        return

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_tasks = sorted(tasks, key=lambda x: priority_order.get(x.priority, 1))

    for item in sorted_tasks:
        due = item.due_date if item.due_date != "TBD" else "—"
        st.markdown(f"""
        <div class="task-row">
            <div style="flex:0.3;">{badge(item.priority)}</div>
            <div class="task-name">{item.task}</div>
            <div class="task-meta">👤 {item.assignee}</div>
            <div class="task-meta">📅 {due}</div>
        </div>
        """, unsafe_allow_html=True)


def render_meeting_result(result: dict):
    """Render full meeting mode results."""
    summary   = result.get("summary")
    tasks_obj = result.get("tasks")
    accuracy  = result.get("accuracy", 0)
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

    # Metrics
    task_count = len(tasks_obj.items) if tasks_obj else 0
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{accuracy}%</div><div class="lbl">Accuracy</div></div>
        <div class="metric-box"><div class="val">{task_count}</div><div class="lbl">Tasks</div></div>
        <div class="metric-box"><div class="val">{proc_time:.1f}s</div><div class="lbl">Processed In</div></div>
        <div class="metric-box"><div class="val">{duration:.0f}m</div><div class="lbl">Audio Length</div></div>
    </div>
    """, unsafe_allow_html=True)

    if summary:
        tab1, tab2, tab3 = st.tabs(["📝 Summary", "✅ Tasks", "🔑 Decisions & Next Steps"])

        with tab1:
            st.markdown(f"""
            <div class="card">
                <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700;
                            color:#60A5FA; margin-bottom:0.8rem;">{summary.title}</div>
                <div style="font-size:0.9rem; line-height:1.7; opacity:0.8;">{summary.summary}</div>
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            if tasks_obj:
                render_tasks(tasks_obj.items)

        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Key Decisions**")
                for d in summary.key_decisions:
                    st.markdown(f"• {d}")
            with col2:
                st.markdown("**🚀 Next Steps**")
                for s in summary.next_steps:
                    st.markdown(f"• {s}")


def render_youtube_result(result: dict):
    """Render full YouTube mode results."""
    insights  = result.get("insights")
    tasks_obj = result.get("tasks")
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

    task_count = len(tasks_obj.items) if tasks_obj else 0
    takeaway_count = len(insights.key_takeaways) if insights else 0

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{proc_time:.1f}s</div><div class="lbl">Processed In</div></div>
        <div class="metric-box"><div class="val">{duration:.0f}m</div><div class="lbl">Video Length</div></div>
        <div class="metric-box"><div class="val">{takeaway_count}</div><div class="lbl">Takeaways</div></div>
        <div class="metric-box"><div class="val">{task_count}</div><div class="lbl">Tasks</div></div>
    </div>
    """, unsafe_allow_html=True)

    if insights:
        tabs = ["📝 Summary", "💡 Takeaways", "📚 Topics"]
        if tasks_obj and tasks_obj.items:
            tabs.append("✅ Tasks")

        rendered_tabs = st.tabs(tabs)

        with rendered_tabs[0]:
            st.markdown(f"""
            <div class="card">
                <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700;
                            color:#A78BFA; margin-bottom:0.8rem;">{insights.title}</div>
                <div style="font-size:0.9rem; line-height:1.7; opacity:0.8;">{insights.summary}</div>
            </div>
            """, unsafe_allow_html=True)
            if insights.action_items:
                st.markdown("**✅ Action Items from Video**")
                for a in insights.action_items:
                    st.markdown(f"→ {a}")

        with rendered_tabs[1]:
            for i, t in enumerate(insights.key_takeaways, 1):
                st.markdown(f"""
                <div class="task-row">
                    <div style="font-family:'Syne',sans-serif; font-size:0.85rem; font-weight:700;
                                color:#A78BFA; flex:0.2;">{i}</div>
                    <div class="task-name">{t}</div>
                </div>
                """, unsafe_allow_html=True)

        with rendered_tabs[2]:
            for topic in insights.topics_covered:
                st.markdown(f"""
                <div class="task-row">
                    <div style="font-size:0.85rem; color:#e2e8f0;">📌 {topic}</div>
                </div>
                """, unsafe_allow_html=True)

        if tasks_obj and tasks_obj.items and len(rendered_tabs) > 3:
            with rendered_tabs[3]:
                render_tasks(tasks_obj.items)


def save_to_history(mode: str, title: str, result: dict):
    """Save a run to session history."""
    tasks = result.get("tasks")
    # Safely get task count — tasks can be None if not extracted
    task_count = len(tasks.items) if (tasks and tasks.items) else 0

    entry = {
        "mode":            mode,
        "title":           title,
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        "task_count":      task_count,
        "processing_time": result.get("processing_time", 0),
        "accuracy":        result.get("accuracy", 0),
        "result":          result,
    }
    st.session_state.history.insert(0, entry)  # newest first