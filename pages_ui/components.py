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


# ─── Study Mode Renderer ──────────────────────────────────────────────────────

def render_study_notes(result: dict):
    """
    Render StudyNotes output — structured for actual studying.
    Core concept prominent. Formulas as code. Self-test interactive.
    """
    notes     = result.get("insights")
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

    if not notes:
        st.markdown('<div class="notify notify-error">No study notes generated.</div>',
                    unsafe_allow_html=True)
        return

    formula_count  = len(notes.formula_sheet)
    fact_count     = len(notes.key_facts)
    question_count = len(notes.self_test)

    # Metric row
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{proc_time:.1f}s</div><div class="lbl">Processed In</div></div>
        <div class="metric-box"><div class="val">{duration:.0f}m</div><div class="lbl">Video Length</div></div>
        <div class="metric-box"><div class="val">{formula_count}</div><div class="lbl">Formulas</div></div>
        <div class="metric-box"><div class="val">{fact_count}</div><div class="lbl">Key Facts</div></div>
        <div class="metric-box"><div class="val">{question_count}</div><div class="lbl">Self-Test Qs</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Core Concept — the most prominent element on the page
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(234,179,8,0.12),rgba(234,179,8,0.06));
                border:1px solid rgba(234,179,8,0.3); border-radius:14px;
                padding:1.2rem 1.5rem; margin:1rem 0;">
        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase;
                    letter-spacing:0.1em; color:#FBBF24; margin-bottom:0.5rem;">
            📐 Core Concept — Memorise This
        </div>
        <div style="font-family:'Syne',sans-serif; font-size:1.05rem; font-weight:600;
                    color:#FDE68A; line-height:1.6;">
            {notes.core_concept}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab_labels = ["📋 Formulas", "⚡ Key Facts", "⚠️ Mistakes", "🧪 Self-Test", "📚 Resources"]
    tabs = st.tabs(tab_labels)

    # ── Formulas ──────────────────────────────────────────────────────────────
    with tabs[0]:
        if not notes.formula_sheet:
            st.markdown(
                '<div class="notify notify-info">No mathematical formulas in this video.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="font-size:0.82rem; opacity:0.55; margin-bottom:1rem;">'
                'Each entry shows the formula and the meaning of every variable. '
                'Timestamp (≈MM:SS) indicates where in the video it appears.'
                '</div>',
                unsafe_allow_html=True
            )
            for formula in notes.formula_sheet:
                st.code(formula, language=None)

    # ── Key Facts ─────────────────────────────────────────────────────────────
    with tabs[1]:
        if not notes.key_facts:
            st.markdown('<div class="notify notify-info">No key facts extracted.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:0.82rem; opacity:0.55; margin-bottom:1rem;">'
                f'{len(notes.key_facts)} facts extracted. Timestamps (≈MM:SS) show where '
                f'in the video each fact is explained.'
                f'</div>',
                unsafe_allow_html=True
            )
            for i, fact in enumerate(notes.key_facts, 1):
                st.markdown(f"""
                <div class="task-row">
                    <div style="font-family:'Syne',sans-serif; font-size:0.85rem; font-weight:700;
                                color:#A78BFA; flex:0.15; min-width:28px;">{i}</div>
                    <div class="task-name">{fact}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Common Mistakes ───────────────────────────────────────────────────────
    with tabs[2]:
        if not notes.common_mistakes:
            st.markdown(
                '<div class="notify notify-info">'
                'No common mistakes explicitly identified in this video.'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="font-size:0.82rem; opacity:0.55; margin-bottom:1rem;">'
                'These are errors specific to this topic — things that are easy to get wrong.'
                '</div>',
                unsafe_allow_html=True
            )
            for mistake in notes.common_mistakes:
                st.markdown(f"""
                <div class="task-row" style="border-color:rgba(251,146,60,0.2);">
                    <div style="font-size:1rem; flex:0.1;">⚠️</div>
                    <div class="task-name" style="color:#FB923C;">{mistake}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Self-Test ─────────────────────────────────────────────────────────────
    with tabs[3]:
        if not notes.self_test:
            st.markdown('<div class="notify notify-info">No self-test questions generated.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="notify notify-info" style="margin-bottom:1rem;">
                💡 <b>{len(notes.self_test)} questions</b> generated from this video.
                Type your answer in the box before clicking "Show Answer" —
                active recall is more effective than passive reading.
            </div>
            """, unsafe_allow_html=True)

            for i, question in enumerate(notes.self_test, 1):
                with st.expander(f"Q{i}: {question}", expanded=False):
                    st.text_area(
                        "Your answer:",
                        key=f"selftest_{i}_{id(notes)}",
                        height=100,
                        placeholder="Write your answer here before checking..."
                    )
                    st.markdown(
                        '<div style="font-size:0.78rem; opacity:0.45; margin-top:0.3rem;">'
                        'Answer is in the video. Push to Notion to get toggle blocks '
                        'where you can store your answer permanently.'
                        '</div>',
                        unsafe_allow_html=True
                    )

    # ── Resources ─────────────────────────────────────────────────────────────
    with tabs[4]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📚 Prerequisites**")
            if notes.prerequisites:
                for prereq in notes.prerequisites:
                    st.markdown(f"• {prereq}")
            else:
                st.markdown(
                    '<div style="opacity:0.4; font-size:0.85rem;">None identified</div>',
                    unsafe_allow_html=True
                )
        with col2:
            st.markdown("**📖 Further Reading**")
            if notes.further_reading:
                for resource in notes.further_reading:
                    st.markdown(f"• {resource}")
            else:
                st.markdown(
                    '<div style="opacity:0.4; font-size:0.85rem;">None identified</div>',
                    unsafe_allow_html=True
                )


# ─── Work Mode Renderer ───────────────────────────────────────────────────────

def render_work_brief(result: dict):
    """
    Render WorkBrief output — structured for professional use.
    Watch/Skip verdict prominent. Decisions as interactive checkboxes.
    """
    brief     = result.get("insights")
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

    if not brief:
        st.markdown('<div class="notify notify-error">No brief generated.</div>',
                    unsafe_allow_html=True)
        return

    # Metric row
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{proc_time:.1f}s</div><div class="lbl">Processed In</div></div>
        <div class="metric-box"><div class="val">{duration:.0f}m</div><div class="lbl">Video Length</div></div>
        <div class="metric-box"><div class="val">{len(brief.key_points)}</div><div class="lbl">Key Points</div></div>
        <div class="metric-box"><div class="val">{len(brief.tools_mentioned)}</div><div class="lbl">Tools</div></div>
        <div class="metric-box"><div class="val">{len(brief.decisions_to_make)}</div><div class="lbl">Decisions</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Watch / Skip verdict — most prominent element
    is_watch    = brief.watch_or_skip.lower().startswith("watch")
    verdict_bg  = "rgba(34,197,94,0.1)"  if is_watch else "rgba(239,68,68,0.1)"
    verdict_bdr = "rgba(34,197,94,0.3)"  if is_watch else "rgba(239,68,68,0.3)"
    verdict_clr = "#4ADE80"              if is_watch else "#F87171"
    verdict_ico = "🟢"                   if is_watch else "🔴"

    st.markdown(f"""
    <div style="background:{verdict_bg}; border:2px solid {verdict_bdr};
                border-radius:14px; padding:1.2rem 1.5rem; margin:1rem 0;">
        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase;
                    letter-spacing:0.1em; color:{verdict_clr}; margin-bottom:0.4rem;">
            {verdict_ico} Verdict
        </div>
        <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:600;
                    color:{verdict_clr}; line-height:1.6;">
            {brief.watch_or_skip}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # One-liner
    st.markdown(f"""
    <div style="font-style:italic; font-size:0.95rem; opacity:0.7;
                padding:0 0.5rem; margin-bottom:1.5rem; line-height:1.7;">
        "{brief.one_liner}"
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tabs = st.tabs(["💡 Key Points", "🛠️ Tools", "✅ Decisions", "🚀 Actions"])

    # ── Key Points ────────────────────────────────────────────────────────────
    with tabs[0]:
        if not brief.key_points:
            st.markdown('<div class="notify notify-info">No key points extracted.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="font-size:0.82rem; opacity:0.55; margin-bottom:1rem;">'
                'Insights that change how you or your team works.'
                '</div>',
                unsafe_allow_html=True
            )
            for point in brief.key_points:
                st.markdown(f"""
                <div class="task-row">
                    <div class="task-name">{point}</div>
                </div>
                """, unsafe_allow_html=True)

    # ── Tools ─────────────────────────────────────────────────────────────────
    with tabs[1]:
        if not brief.tools_mentioned:
            st.markdown(
                '<div class="notify notify-info">No specific tools mentioned in this video.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="font-size:0.82rem; opacity:0.55; margin-bottom:1rem;">'
                'Named tools, libraries, frameworks, and platforms from the video.'
                '</div>',
                unsafe_allow_html=True
            )
            # Render each tool as a code badge
            tools_html = "".join(
                f'<code style="background:rgba(96,165,250,0.12); '
                f'border:1px solid rgba(96,165,250,0.2); border-radius:6px; '
                f'padding:3px 10px; margin:3px; font-size:0.85rem; '
                f'color:#60A5FA; display:inline-block;">{tool}</code>'
                for tool in brief.tools_mentioned
            )
            st.markdown(
                f'<div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:0.5rem;">'
                f'{tools_html}</div>',
                unsafe_allow_html=True
            )

    # ── Decisions ─────────────────────────────────────────────────────────────
    with tabs[2]:
        if not brief.decisions_to_make:
            st.markdown(
                '<div class="notify notify-info">No specific decisions implied by this video.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="font-size:0.82rem; opacity:0.55; margin-bottom:1rem;">'
                'Tick these off as your team works through them.'
                '</div>',
                unsafe_allow_html=True
            )
            for i, decision in enumerate(brief.decisions_to_make):
                st.checkbox(decision, value=False, key=f"decision_{i}_{id(brief)}")

    # ── Next Actions ──────────────────────────────────────────────────────────
    with tabs[3]:
        if not brief.next_actions:
            st.markdown(
                '<div class="notify notify-info">No specific actions implied by this video.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="font-size:0.82rem; opacity:0.55; margin-bottom:1rem;">'
                'Specific, executable steps. Doable this week.'
                '</div>',
                unsafe_allow_html=True
            )
            for action in brief.next_actions:
                st.markdown(f"""
                <div class="task-row">
                    <div style="color:#60A5FA; flex:0.08; font-weight:700;">→</div>
                    <div class="task-name">{action}</div>
                </div>
                """, unsafe_allow_html=True)


# ─── Meeting Mode Renderer (unchanged) ───────────────────────────────────────

def render_meeting_result(result: dict):
    summary   = result.get("summary")
    tasks_obj = result.get("tasks")
    accuracy  = result.get("accuracy", 0)
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

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


# ─── Quick Mode Renderer (unchanged) ─────────────────────────────────────────

def render_youtube_result(result: dict):
    insights  = result.get("insights")
    tasks_obj = result.get("tasks")
    proc_time = result.get("processing_time", 0)
    duration  = result.get("duration", 0)

    task_count     = len(tasks_obj.items) if tasks_obj else 0
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


# ─── History Save ─────────────────────────────────────────────────────────────

def save_to_history(mode: str, title: str, result: dict):
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
    st.session_state.history.insert(0, entry)