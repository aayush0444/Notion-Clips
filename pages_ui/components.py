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
    """Render full YouTube Quick mode results — unchanged."""
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


# ─── Study Mode renderer ──────────────────────────────────────────────────────

def render_study_notes(result: dict):
    """Render Study Mode results (StudyNotes model)."""
    notes     = result.get("insights")
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

    if not notes:
        st.markdown('<div class="notify notify-error">No study notes found in result.</div>',
                    unsafe_allow_html=True)
        return

    formula_count  = len(notes.formula_sheet)
    selftest_count = len(notes.self_test)

    # Metrics
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{proc_time:.1f}s</div><div class="lbl">Processed In</div></div>
        <div class="metric-box"><div class="val">{duration:.0f}m</div><div class="lbl">Video Length</div></div>
        <div class="metric-box"><div class="val">{formula_count}</div><div class="lbl">Formulas</div></div>
        <div class="metric-box"><div class="val">{selftest_count}</div><div class="lbl">Self-Test Qs</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Core concept — the most visually prominent thing on the page
    st.markdown(f"""
    <div style="background:rgba(251,191,36,0.08); border:2px solid rgba(251,191,36,0.3);
                border-radius:14px; padding:1.2rem 1.5rem; margin:1rem 0 1.5rem 0;">
        <div style="font-family:'Syne',sans-serif; font-size:0.72rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:0.1em; color:#FCD34D;
                    opacity:0.7; margin-bottom:0.5rem;">📐 Core Concept — Memorise This</div>
        <div style="font-size:1rem; line-height:1.7; color:#FEF3C7; font-weight:500;">
            {notes.core_concept}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs for the rest
    tab_labels = ["📋 Formulas", "⚡ Key Facts", "⚠️ Mistakes", "🧪 Self-Test", "📚 Resources"]
    tabs = st.tabs(tab_labels)

    # ── Formulas tab ──────────────────────────────────────────────────────────
    with tabs[0]:
        if not notes.formula_sheet:
            st.markdown('<div class="notify notify-info">No formulas or equations in this video.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='font-size:0.82rem; opacity:0.5; margin-bottom:0.8rem;'>"
                "Each formula with variable definitions. Click to copy.</div>",
                unsafe_allow_html=True
            )
            for formula in notes.formula_sheet:
                st.code(formula, language=None)

    # ── Key facts tab ─────────────────────────────────────────────────────────
    with tabs[1]:
        if not notes.key_facts:
            st.markdown('<div class="notify notify-info">No key facts extracted.</div>',
                        unsafe_allow_html=True)
        else:
            for i, fact in enumerate(notes.key_facts, 1):
                st.markdown(f"""
                <div class="task-row">
                    <div style="font-family:'Syne',sans-serif; font-size:0.9rem; font-weight:700;
                                color:#A78BFA; min-width:1.8rem;">{i}</div>
                    <div class="task-name" style="font-size:0.88rem;">{fact}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Common mistakes tab ───────────────────────────────────────────────────
    with tabs[2]:
        if not notes.common_mistakes:
            st.markdown('<div class="notify notify-info">No common mistakes identified from this video.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='font-size:0.82rem; opacity:0.5; margin-bottom:0.8rem;'>"
                "Things students typically get wrong about this topic.</div>",
                unsafe_allow_html=True
            )
            for mistake in notes.common_mistakes:
                st.markdown(f"""
                <div class="task-row" style="border-color:rgba(251,146,60,0.2);
                                             background:rgba(251,146,60,0.04);">
                    <div style="font-size:1.1rem; min-width:1.8rem;">⚠️</div>
                    <div class="task-name" style="color:#FB923C; font-size:0.88rem;">{mistake}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Self-test tab ─────────────────────────────────────────────────────────
    with tabs[3]:
        if not notes.self_test:
            st.markdown('<div class="notify notify-info">No self-test questions generated.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='font-size:0.82rem; opacity:0.5; margin-bottom:1rem;'>"
                "Try to answer each question before expanding it. "
                "Active recall is more effective than re-reading.</div>",
                unsafe_allow_html=True
            )
            for i, question in enumerate(notes.self_test, 1):
                with st.expander(f"Q{i}: {question}"):
                    st.text_area(
                        "Your answer:",
                        placeholder="Write your answer here before looking anything up...",
                        key=f"selftest_answer_{i}",
                        height=100
                    )

    # ── Resources tab ─────────────────────────────────────────────────────────
    with tabs[4]:
        has_prereqs  = bool(notes.prerequisites)
        has_reading  = bool(notes.further_reading)

        if not has_prereqs and not has_reading:
            st.markdown('<div class="notify notify-info">No prerequisites or reading resources extracted.</div>',
                        unsafe_allow_html=True)
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📚 Prerequisites**")
                if has_prereqs:
                    for prereq in notes.prerequisites:
                        st.markdown(f"• {prereq}")
                else:
                    st.markdown("*None identified*")
            with col2:
                st.markdown("**📖 Further Reading**")
                if has_reading:
                    for resource in notes.further_reading:
                        st.markdown(f"• {resource}")
                else:
                    st.markdown("*None identified*")


# ─── Work Mode renderer ───────────────────────────────────────────────────────

def render_work_brief(result: dict):
    """Render Work Mode results (WorkBrief model)."""
    brief     = result.get("insights")
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

    if not brief:
        st.markdown('<div class="notify notify-error">No work brief found in result.</div>',
                    unsafe_allow_html=True)
        return

    # Metrics
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{proc_time:.1f}s</div><div class="lbl">Processed In</div></div>
        <div class="metric-box"><div class="val">{duration:.0f}m</div><div class="lbl">Video Length</div></div>
        <div class="metric-box"><div class="val">{len(brief.tools_mentioned)}</div><div class="lbl">Tools</div></div>
        <div class="metric-box"><div class="val">{len(brief.decisions_to_make)}</div><div class="lbl">Decisions</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Watch / Skip verdict — the most important thing, shown at the very top
    verdict = brief.watch_or_skip.strip()
    is_watch = verdict.lower().startswith("watch")

    if is_watch:
        verdict_bg    = "rgba(34,197,94,0.08)"
        verdict_border = "rgba(34,197,94,0.35)"
        verdict_color  = "#4ADE80"
        verdict_label  = "🟢 WATCH"
    else:
        verdict_bg    = "rgba(239,68,68,0.08)"
        verdict_border = "rgba(239,68,68,0.35)"
        verdict_color  = "#F87171"
        verdict_label  = "🔴 SKIP"

    st.markdown(f"""
    <div style="background:{verdict_bg}; border:2px solid {verdict_border};
                border-radius:14px; padding:1.2rem 1.5rem; margin:1rem 0 0.5rem 0;">
        <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:800;
                    color:{verdict_color}; margin-bottom:0.4rem;">{verdict_label}</div>
        <div style="font-size:0.9rem; line-height:1.6; color:#e2e8f0;">
            {verdict}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # One-liner as a quote
    st.markdown(f"""
    <div style="border-left:3px solid rgba(167,139,250,0.5); padding:0.5rem 1rem;
                margin:0.5rem 0 1.5rem 0; font-style:italic;
                font-size:0.9rem; opacity:0.75; color:#e2e8f0;">
        {brief.one_liner}
    </div>
    """, unsafe_allow_html=True)

    # Tabs for the rest
    tab_labels = ["💡 Key Points", "🛠️ Tools", "✅ Decisions", "🚀 Actions"]
    tabs = st.tabs(tab_labels)

    # ── Key points ────────────────────────────────────────────────────────────
    with tabs[0]:
        if not brief.key_points:
            st.markdown('<div class="notify notify-info">No key points extracted.</div>',
                        unsafe_allow_html=True)
        else:
            for point in brief.key_points:
                st.markdown(f"""
                <div class="task-row">
                    <div class="task-name" style="font-size:0.88rem;">{point}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Tools ─────────────────────────────────────────────────────────────────
    with tabs[1]:
        if not brief.tools_mentioned:
            st.markdown('<div class="notify notify-info">No specific tools mentioned in this video.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='font-size:0.82rem; opacity:0.5; margin-bottom:1rem;'>"
                "Named tools, libraries, platforms, and companies from this video.</div>",
                unsafe_allow_html=True
            )
            # Render each tool as a code-style badge in a flex-wrap layout
            tools_html = " &nbsp; ".join(
                f'<code style="background:rgba(96,165,250,0.1); border:1px solid rgba(96,165,250,0.2); '
                f'padding:3px 10px; border-radius:6px; font-size:0.85rem; color:#93C5FD;">{tool}</code>'
                for tool in brief.tools_mentioned
            )
            st.markdown(
                f'<div style="display:flex; flex-wrap:wrap; gap:0.5rem; padding:0.5rem 0;">{tools_html}</div>',
                unsafe_allow_html=True
            )

    # ── Decisions — interactive Streamlit checkboxes ───────────────────────────
    with tabs[2]:
        if not brief.decisions_to_make:
            st.markdown('<div class="notify notify-info">No specific decisions identified.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='font-size:0.82rem; opacity:0.5; margin-bottom:0.8rem;'>"
                "Check off decisions as your team evaluates them.</div>",
                unsafe_allow_html=True
            )
            for i, decision in enumerate(brief.decisions_to_make):
                st.checkbox(decision, value=False, key=f"work_decision_{i}")

    # ── Next actions ──────────────────────────────────────────────────────────
    with tabs[3]:
        if not brief.next_actions:
            st.markdown('<div class="notify notify-info">No specific next actions identified.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='font-size:0.82rem; opacity:0.5; margin-bottom:0.8rem;'>"
                "Concrete, doable-today actions from this video.</div>",
                unsafe_allow_html=True
            )
            for action in brief.next_actions:
                st.markdown(f"""
                <div class="task-row">
                    <div style="color:#A78BFA; min-width:1.2rem; font-size:0.9rem;">→</div>
                    <div class="task-name" style="font-size:0.88rem;">{action}</div>
                </div>
                """, unsafe_allow_html=True)


# ─── History ──────────────────────────────────────────────────────────────────

def save_to_history(mode: str, title: str, result: dict):
    """Save a run to session history."""
    tasks = result.get("tasks")
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