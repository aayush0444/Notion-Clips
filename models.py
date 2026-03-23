from pydantic import BaseModel, Field
from typing import List, Optional


# ─── Shared ───────────────────────────────────────────────────────────────────

class ActionItem(BaseModel):
    task: str     = Field(description="The specific action item or task")
    assignee: str = Field(description="Person responsible, or 'Team' if unclear")
    due_date: str = Field(description="Due date as YYYY-MM-DD, or 'TBD'")
    priority: str = Field(description="High, Medium, or Low")

class ActionItemList(BaseModel):
    items: List[ActionItem]


# ─── Meeting Mode ─────────────────────────────────────────────────────────────

class MeetingSummary(BaseModel):
    title: str                = Field(description="Short meeting title, max 8 words")
    summary: str              = Field(description="3-4 sentence executive summary")
    key_decisions: List[str]  = Field(description="Key decisions made")
    next_steps: List[str]     = Field(description="Next steps agreed upon")


# ─── YouTube Quick Mode (unchanged) ──────────────────────────────────────────

class VideoInsights(BaseModel):
    title: str                = Field(description="Short title describing what this video is about")
    summary: str              = Field(description="2-3 sentence summary — conversational, not academic")
    key_takeaways: List[str]  = Field(description="The most interesting or surprising things worth knowing. Scale count to video length — do not cap artificially.")
    topics_covered: List[str] = Field(description="Main topics covered in plain language")
    action_items: List[str]   = Field(description="Things worth doing after watching. Empty list if nothing actionable.")


# ─── YouTube Study Mode ───────────────────────────────────────────────────────

class StudyNotes(BaseModel):
    title: str = Field(
        description="Precise title of what this video teaches"
    )
    core_concept: str = Field(
        description=(
            "ONE sentence. The single most important idea to memorise from this entire video. "
            "Not a summary — the distilled essence. Must be precise and technical if the content is technical. "
            "Example: 'Single slit diffraction produces intensity minima at positions where a·sinθ = nλ, "
            "where a is slit width, n is an integer, and λ is wavelength.'"
        )
    )
    formula_sheet: List[str] = Field(
        description=(
            "Every mathematical formula, equation, or quantitative relationship mentioned in the video. "
            "Format each entry as: 'formula — plain English definition of EVERY variable'. "
            "Example: 'a·sinθ = nλ — a is slit width in metres, θ is the angle of the minima from centre, "
            "n is any non-zero integer, λ is the wavelength of light'. "
            "If no formulas in the video, return empty list. Do NOT invent formulas."
        )
    )
    key_facts: List[str] = Field(
        description=(
            "Every specific, precise, standalone technical statement from the video. "
            "SCALE THIS TO VIDEO LENGTH — a 10-minute video might have 5-8 facts, "
            "a 30-minute video 12-20 facts, a 60-minute video 20-30 facts, a 2-hour video 30-45 facts. "
            "Each fact must: contain the actual information (not 'the speaker discusses X'), "
            "include numbers/conditions/limits where mentioned, be complete as a standalone statement. "
            "Include approximate timestamp where identifiable, formatted as (≈MM:SS). "
            "Example: 'The first minimum in single slit diffraction occurs at θ = λ/a (≈08:30)'. "
            "ONLY include what is explicitly stated in the transcript. Never infer or add external knowledge."
        )
    )
    common_mistakes: List[str] = Field(
        description=(
            "Errors, misconceptions, or confusions that students or practitioners commonly make "
            "about the topics covered in this video, as explicitly mentioned by the speaker OR "
            "as naturally arising from the specific content taught. "
            "Be specific to THIS content, not generic study advice. "
            "Example: 'Confusing the minima condition (a·sinθ = nλ) with the maxima condition — "
            "the formula gives DARK fringes, not bright ones'. "
            "If the video contains no warnings or difficult-to-distinguish concepts, return empty list."
        )
    )
    self_test: List[str] = Field(
        description=(
            "Exam-style questions generated from the video content. "
            "SCALE TO VIDEO LENGTH — 3 questions for short videos, up to 10-12 for 2-hour lectures. "
            "Every question must be answerable solely from the video content. "
            "Mix question types: definition ('What is...'), calculation ('Calculate the angle where...'), "
            "conceptual ('Explain why intensity decreases...'), application ('A slit of width 0.1mm...'). "
            "Write just the question — no answers in this field."
        )
    )
    prerequisites: List[str] = Field(
        description=(
            "Specific concepts the viewer must already understand for this video to make sense. "
            "Be precise: 'Huygens' Principle — every point on a wavefront acts as a source of secondary wavelets' "
            "not just 'wave theory'. List only genuine prerequisites, not general background."
        )
    )
    further_reading: List[str] = Field(
        description=(
            "Specific resources for going deeper. Minimum: chapter number + book title + author. "
            "If the speaker recommends something specific, use that exactly. "
            "Example: 'Chapter 10, Introduction to Electrodynamics by Griffiths — covers wave optics in full'. "
            "Do not suggest vague resources like 'search online for more'. "
            "If no specific resources were mentioned and none are naturally implied, return empty list."
        )
    )


# ─── YouTube Work Mode ────────────────────────────────────────────────────────

class WorkBrief(BaseModel):
    title: str = Field(
        description="Short, precise title of what this video covers professionally"
    )
    one_liner: str = Field(
        description=(
            "One sentence. Slack-message ready. What this video covers and why a professional would care. "
            "Example: 'Deep dive into Redis caching strategies with benchmarks comparing write-through "
            "vs write-behind — relevant if your team is scaling read-heavy APIs.'"
        )
    )
    watch_or_skip: str = Field(
        description=(
            "Must follow EXACTLY one of these formats: "
            "'Watch — [one sentence reason why it is worth watching]' "
            "or 'Skip — [one sentence reason why it is not worth the time]'. "
            "Reason must focus on professional value (decision quality, frameworks, tradeoffs, applicability), "
            "not a description of video sections or timestamps. "
            "Correct example: 'Watch — practical framework for evaluating AI automation tools with real cost tradeoffs included.' "
            "Wrong example: 'Watch — the section at 6:00 shows building an automation.'"
        )
    )
    key_points: List[str] = Field(
        description=(
            "Insights that change how you or your team works. APPLICABILITY FIRST. "
            "Not what was said — what it means for how you build, decide, or operate. "
            "SCALE TO VIDEO LENGTH — 5 points for a 15-min talk, up to 20 for a 2-hour deep dive. "
            "Include specific numbers, benchmarks, or comparisons where mentioned. "
            "Example: 'Redis outperforms Memcached by 3x on persistence-heavy workloads but "
            "Memcached is faster for simple key-value reads under 100ms latency requirements.' "
            "ONLY include what is explicitly stated. Never add external knowledge."
        )
    )
    tools_mentioned: List[str] = Field(
        description=(
            "Every named tool, library, framework, platform, company, or service mentioned. "
            "Exact names only — no descriptions in this field. "
            "Example: ['Redis', 'Memcached', 'LangChain', 'Supabase', 'Vercel', 'Cloudflare Workers']"
        )
    )
    decisions_to_make: List[str] = Field(
        description=(
            "Specific decisions the viewer's team should now consider, prompted by this video. "
            "Must be concrete and team-specific, not generic. "
            "Example: 'Evaluate whether adding Redis as a caching layer before the next backend "
            "release would reduce database load below the 70% threshold mentioned'. "
            "NOT: 'Consider caching strategies for your application'. "
            "Only include if a genuine decision is implied by the content."
        )
    )
    next_actions: List[str] = Field(
        description=(
            "Specific, executable actions. Name the tool, write the command, state the step. "
            "Must be doable in the next few days, not vague goals. "
            "Example: 'Install Redis locally: brew install redis && redis-server'. "
            "Example: 'Read the LangChain caching docs — python.langchain.com/docs/modules/model_io/llms/llm_caching'. "
            "NOT: 'Learn more about caching'. NOT: 'Research this topic further'. "
            "If nothing is genuinely actionable from this video, return empty list."
        )
    )


# ─── Internal — Chunked Processing ───────────────────────────────────────────
# Used internally by gemini.py for long video processing.
# Not exposed to the rest of the app.

class _ChunkExtract(BaseModel):
    """Raw extraction from one chunk of a long transcript."""
    facts: List[str] = Field(
        description="Specific technical statements, definitions, numbers, conditions from this section"
    )
    formulas: List[str] = Field(
        description="Mathematical formulas or equations with variable definitions. Empty list if none."
    )
    mistakes: List[str] = Field(
        description="Errors or misconceptions explicitly mentioned. Empty list if none."
    )
    potential_questions: List[str] = Field(
        description="Things from this section that could be exam or interview questions"
    )
    tools: List[str] = Field(
        description="Named tools, libraries, frameworks mentioned. Empty list if none or not applicable."
    )
    key_insights: List[str] = Field(
        description="For work mode: insights that change how a professional works"
    )
