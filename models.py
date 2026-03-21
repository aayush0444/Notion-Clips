from pydantic import BaseModel, Field
from typing import List


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
    summary: str              = Field(description="3-4 sentence executive summary of what was discussed")
    key_decisions: List[str]  = Field(description="Key decisions made, up to 5 points")
    next_steps: List[str]     = Field(description="Next steps agreed upon, up to 5 points")


# ─── YouTube Quick Mode ───────────────────────────────────────────────────────
# Used only for Quick mode — kept exactly as-is.

class VideoInsights(BaseModel):
    title: str                = Field(description="Short title describing what this video is about")
    summary: str              = Field(description="3-4 sentence summary of the video content")
    key_takeaways: List[str]  = Field(description="Most important points from the video, up to 7")
    topics_covered: List[str] = Field(description="Main topics or sections covered, up to 5")
    action_items: List[str]   = Field(description="Things the viewer should do or look into after watching, up to 5")


# ─── YouTube Study Mode ───────────────────────────────────────────────────────
# For lectures, tutorials, courses — anything a student would watch.
# Every field is designed around active recall and exam preparation.

class StudyNotes(BaseModel):
    title: str = Field(
        description="Short title describing what this video teaches"
    )
    core_concept: str = Field(
        description=(
            "ONE sentence. The single most important idea to memorise from this video. "
            "Not a summary — the distilled essence. Must be precise and complete. "
            "Example: 'Single slit diffraction produces a central bright maximum flanked "
            "by dark fringes at positions given by a·sinθ = nλ, where a is slit width "
            "and n is the order of the minimum.'"
        )
    )
    formula_sheet: List[str] = Field(
        description=(
            "Each entry is a formula followed by a plain-English definition of EVERY variable. "
            "Format: 'formula — variable1 = meaning, variable2 = meaning, ...'. "
            "Example: 'a·sinθ = nλ — a = slit width, θ = angle of minima from centre, "
            "n = integer order (1, 2, 3...), λ = wavelength of light'. "
            "If the video contains no formulas or equations, return an empty list."
        )
    )
    key_facts: List[str] = Field(
        description=(
            "Precise, complete, standalone technical statements. "
            "Each fact must be specific enough to appear on an exam. "
            "Must include numbers, conditions, limits, or relationships where the video mentions them. "
            "NOT vague: 'diffraction is important'. "
            "YES: 'The central maximum is twice as wide as all other maxima. "
            "Its half-width is θ = λ/a radians.' Up to 10 facts."
        )
    )
    common_mistakes: List[str] = Field(
        description=(
            "Things students typically get wrong about THIS specific topic. "
            "Draw from: (1) mistakes the speaker explicitly warns against, "
            "(2) common confusions that arise from the content covered. "
            "Be specific to the subject — not generic study advice like 'read carefully'. "
            "Example: 'Applying the double-slit maxima formula (d·sinθ = nλ) to single slit — "
            "single slit uses the same letters but the condition gives MINIMA, not maxima.' "
            "Up to 5 mistakes."
        )
    )
    self_test: List[str] = Field(
        description=(
            "3 to 5 exam-style questions generated from the video content. "
            "Must be answerable using only what was covered in the video. "
            "Mix types: at least one definition, one calculation or derivation, one conceptual. "
            "Write only the question — no answers in this field. "
            "Example questions: "
            "'State the condition for destructive interference in single slit diffraction.', "
            "'A slit of width 0.1mm is illuminated by 600nm light. Find the angle of the first minimum.', "
            "'Why does the central maximum have twice the angular width of secondary maxima?'"
        )
    )
    prerequisites: List[str] = Field(
        description=(
            "Concepts you must understand before this video makes sense. "
            "Be specific — name the concept precisely. "
            "'Huygens' Principle' not 'wave theory'. "
            "'Superposition of waves' not 'wave basics'. Up to 5 prerequisites."
        )
    )
    further_reading: List[str] = Field(
        description=(
            "Specific resources for deeper study. "
            "Minimum format: 'Chapter/Section number, Book Title by Author'. "
            "If the speaker recommends something specific, use that exactly. "
            "If not, recommend the standard textbook for this subject at university level. "
            "Example: 'Chapter 36, University Physics by Young & Freedman', "
            "'Chapter 10, Optics by Eugene Hecht'. Up to 4 resources."
        )
    )


# ─── YouTube Work Mode ────────────────────────────────────────────────────────
# For tech talks, industry videos, conference presentations.
# Every field is designed around professional applicability.

class WorkBrief(BaseModel):
    title: str = Field(
        description="Short title describing what this video covers professionally"
    )
    one_liner: str = Field(
        description=(
            "One sentence. Slack-message ready. "
            "Format: 'This video covers [topic] and is relevant if your team is [context].' "
            "Example: 'This video covers Redis caching patterns and is relevant if your team "
            "is dealing with API rate limits or session storage at scale.'"
        )
    )
    watch_or_skip: str = Field(
        description=(
            "Start with exactly 'Watch' or 'Skip', then a colon, then one sentence reason. "
            "If recommending Watch: reference a specific timestamp or section if possible. "
            "Example Watch: 'Watch: the rate limiting implementation (14:00–22:00) directly "
            "applies to any team running a public API.' "
            "Example Skip: 'Skip: covers fundamentals your team likely knows — "
            "no new tools or patterns introduced beyond what is in the official docs.'"
        )
    )
    key_points: List[str] = Field(
        description=(
            "What changes how you or your team works — applicability first, information second. "
            "Each point must answer the implicit question: 'So what? What do I do differently?' "
            "Include specific metrics, comparisons, or recommendations the speaker makes. "
            "Example: 'Redis outperforms Memcached on persistence and Pub/Sub, "
            "but Memcached is faster for simple key-value at very high throughput — "
            "the speaker recommends Redis as the default unless you are above 1M req/min.' "
            "NOT: 'Redis is a caching solution.' Up to 7 points."
        )
    )
    tools_mentioned: List[str] = Field(
        description=(
            "Every named tool, library, framework, platform, SaaS product, or company mentioned. "
            "Exact names only — no descriptions in this field, just the name. "
            "Examples: 'Redis', 'LangChain', 'Supabase', 'Vercel', 'Railway', 'Pinecone'. "
            "These become searchable reference tags."
        )
    )
    decisions_to_make: List[str] = Field(
        description=(
            "Specific decisions the viewer's team should consider or evaluate after watching. "
            "Must be concrete and tied to the video content — not generic. "
            "Format: 'Evaluate whether to [action] given [context from video].' "
            "Example: 'Evaluate whether to add Redis as a caching layer before the next "
            "backend release — the video shows a 4x latency reduction on read-heavy endpoints.' "
            "NOT: 'Consider caching strategies.' Up to 5 decisions."
        )
    )
    next_actions: List[str] = Field(
        description=(
            "Specific, doable-today actions. Include enough detail to execute immediately. "
            "Name the tool, write the command, state the URL, specify the search term. "
            "Examples: "
            "'Install Redis locally: brew install redis && redis-server', "
            "'Read the LangChain caching docs: python.langchain.com/docs/modules/model_io/llms/llm_caching', "
            "'Search: redis vs memcached 2024 benchmark to find recent performance comparisons'. "
            "NOT: 'Learn more about caching.' Up to 6 actions."
        )
    )