from pydantic import BaseModel, Field, field_validator, model_validator, AliasChoices
from typing import List, Optional, Any
import re


# ─── Shared ───────────────────────────────────────────────────────────────────

class ActionItem(BaseModel):
    task: str     = Field(description="The specific action item or task", min_length=1, max_length=500)
    assignee: str = Field(description="Person responsible, or 'Team' if unclear", min_length=1, max_length=100)
    due_date: str = Field(description="Due date as YYYY-MM-DD, or 'TBD'", max_length=50)
    priority: str = Field(description="High, Medium, or Low")

    @field_validator('priority')
    @classmethod
    def priority_valid(cls, v: str) -> str:
        """Ensure priority is one of the allowed values."""
        v = v.strip()
        if v not in ('High', 'high', 'Medium', 'medium', 'Low', 'low'):
            raise ValueError("Priority must be 'High', 'Medium', or 'Low'.")
        return v.capitalize()

    @field_validator('due_date')
    @classmethod
    def due_date_format(cls, v: str) -> str:
        """Ensure due_date is YYYY-MM-DD or TBD."""
        v = v.strip()
        if v.upper() == 'TBD':
            return 'TBD'
        if re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            return v
        raise ValueError("Due date must be YYYY-MM-DD format or 'TBD'.")


class TimestampMoment(BaseModel):
    """Links a specific moment in a video to an insight."""
    moment: str = Field(description="Timestamp in MM:SS format, e.g. '03:45'", max_length=10)
    description: str = Field(description="What the insight is at this moment", min_length=1, max_length=500)

    @field_validator('moment')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Ensure moment is in MM:SS or HH:MM:SS format."""
        v = v.strip()
        if not re.match(r'^(\d{1,2}:)?\d{1,2}:\d{2}$', v):
            raise ValueError("Timestamp must be in MM:SS or HH:MM:SS format.")
        return v


class ActionItemList(BaseModel):
    items: List[ActionItem]


# ─── Meeting Mode ─────────────────────────────────────────────────────────────

class MeetingSummary(BaseModel):
    title: str                = Field(description="Short meeting title, max 8 words", min_length=1, max_length=80)
    summary: str              = Field(description="3-4 sentence executive summary", min_length=10, max_length=500)
    key_decisions: List[str]  = Field(description="Key decisions made", default_factory=list)
    next_steps: List[str]     = Field(description="Next steps agreed upon", default_factory=list)

    @field_validator('title')
    @classmethod
    def title_word_count(cls, v: str) -> str:
        """Ensure title is max 8 words."""
        v = v.strip()
        word_count = len(v.split())
        if word_count > 8:
            raise ValueError("Meeting title must be 8 words or fewer.")
        return v

    @field_validator('key_decisions', 'next_steps')
    @classmethod
    def validate_decision_items(cls, v: List[str]) -> List[str]:
        """Clean decisions/steps."""
        return [item.strip() for item in v if item.strip()]


# ─── YouTube Quick Mode (unchanged) ──────────────────────────────────────────

class VideoInsights(BaseModel):
    title: str                = Field(description="Short title describing what this video is about", min_length=1, max_length=200)
    summary: str              = Field(description="2-3 sentence summary — conversational, not academic", min_length=10, max_length=500)
    key_takeaways: List[str]  = Field(description="The most interesting or surprising things worth knowing. Scale count to video length — do not cap artificially.", min_length=1)
    topics_covered: List[str] = Field(description="Main topics covered in plain language", min_length=1)
    action_items: List[str]   = Field(description="Things worth doing after watching. Empty list if nothing actionable.", default_factory=list)
    moments: List[TimestampMoment] = Field(
        description="Timestamp-linked moments in the video for key insights (if video timestamps available).",
        default_factory=list
    )

    @field_validator('title')
    @classmethod
    def title_not_generic(cls, v: str) -> str:
        """Reject overly generic titles."""
        if v.lower() in ('video', 'video summary', 'notes', 'summary', 'untitled'):
            raise ValueError('Title is too generic. Provide a specific, descriptive title.')
        return v.strip()

    @field_validator('summary')
    @classmethod
    def summary_has_content(cls, v: str) -> str:
        """Ensure summary has meaningful content."""
        if len(v.split()) < 5:
            raise ValueError('Summary must be at least 5 words.')
        return v.strip()

    @field_validator('key_takeaways')
    @classmethod
    def validate_key_takeaways(cls, v: List[str]) -> List[str]:
        """Ensure key_takeaways are not empty and don't contain only whitespace."""
        cleaned = [item.strip() for item in v if item.strip()]
        if not cleaned:
            raise ValueError('At least one meaningful key takeaway is required.')
        return cleaned

    @field_validator('topics_covered')
    @classmethod
    def validate_topics(cls, v: List[str]) -> List[str]:
        """Ensure topics are not empty."""
        cleaned = [item.strip() for item in v if item.strip()]
        if not cleaned:
            raise ValueError('At least one topic must be covered.')
        return cleaned

    @field_validator('action_items')
    @classmethod
    def validate_action_items(cls, v: List[str]) -> List[str]:
        """Clean up action items, allow empty."""
        return [item.strip() for item in v if item.strip()]


# ─── YouTube Study Mode ───────────────────────────────────────────────────────

class StudyNotes(BaseModel):
    title: str = Field(
        description="Precise title of what this video teaches", min_length=1, max_length=200
    )
    core_concept: str = Field(
        description=(
            "ONE sentence. The single most important idea to memorise from this entire video. "
            "Not a summary — the distilled essence. Must be precise and technical if the content is technical. "
            "Example: 'Single slit diffraction produces intensity minima at positions where a·sinθ = nλ, "
            "where a is slit width, n is an integer, and λ is wavelength.'"
        ), min_length=10, max_length=500
    )
    formula_sheet: List[str] = Field(
        description=(
            "Every mathematical formula, equation, or quantitative relationship mentioned in the video. "
            "Format each entry as: 'formula — plain English definition of EVERY variable'. "
            "Example: 'a·sinθ = nλ — a is slit width in metres, θ is the angle of the minima from centre, "
            "n is any non-zero integer, λ is the wavelength of light'. "
            "If no formulas in the video, return empty list. Do NOT invent formulas."
        ), default_factory=list
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
        ), min_length=1
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
        ), default_factory=list
    )
    self_test: List[str] = Field(
        description=(
            "Exam-style questions generated from the video content. "
            "SCALE TO VIDEO LENGTH — 3 questions for short videos, up to 10-12 for 2-hour lectures. "
            "Every question must be answerable solely from the video content. "
            "Mix question types: definition ('What is...'), calculation ('Calculate the angle where...'), "
            "conceptual ('Explain why intensity decreases...'), application ('A slit of width 0.1mm...'). "
            "Write just the question — no answers in this field."
        ), default_factory=list
    )
    prerequisites: List[str] = Field(
        description=(
            "Specific concepts the viewer must already understand for this video to make sense. "
            "Be precise: 'Huygens' Principle — every point on a wavefront acts as a source of secondary wavelets' "
            "not just 'wave theory'. List only genuine prerequisites, not general background."
        ), default_factory=list
    )
    further_reading: List[str] = Field(
        description=(
            "Specific resources for going deeper. Minimum: chapter number + book title + author. "
            "If the speaker recommends something specific, use that exactly. "
            "Example: 'Chapter 10, Introduction to Electrodynamics by Griffiths — covers wave optics in full'. "
            "Do not suggest vague resources like 'search online for more'. "
            "If no specific resources were mentioned and none are naturally implied, return empty list."
        ), default_factory=list
    )
    moments: List[TimestampMoment] = Field(
        description="Timestamp-linked moments for key facts and concepts (if video timestamps available).",
        default_factory=list
    )

    @field_validator('title')
    @classmethod
    def title_specificity(cls, v: str) -> str:
        """Ensure title is specific, not generic."""
        if v.lower() in ('study notes', 'notes', 'summary', 'video summary', 'untitled'):
            raise ValueError('Title must be specific to the content, not generic.')
        return v.strip()

    @field_validator('core_concept')
    @classmethod
    def core_concept_one_sentence(cls, v: str) -> str:
        """Check that core_concept is approximately one sentence."""
        v = v.strip()
        sentences = [s.strip() for s in re.split(r'[.!?]+', v) if s.strip()]
        if len(sentences) > 2:
            raise ValueError('Core concept must be ONE sentence maximum.')
        if len(v.split()) < 5:
            raise ValueError('Core concept must be at least 5 words.')
        return v

    @field_validator('formula_sheet')
    @classmethod
    def validate_formula_sheet(cls, v: List[str]) -> List[str]:
        """Clean formula sheet, ensure formulas contain '—' separator or '='."""
        cleaned = []
        for formula in v:
            formula = formula.strip()
            if formula and ('—' in formula or '=' in formula):
                cleaned.append(formula)
        return cleaned

    @field_validator('key_facts')
    @classmethod
    def validate_key_facts(cls, v: List[str]) -> List[str]:
        """Ensure facts are specific and not empty."""
        cleaned = [f.strip() for f in v if f.strip()]
        if not cleaned:
            raise ValueError('At least one key fact is required.')
        return cleaned

    @field_validator('common_mistakes')
    @classmethod
    def validate_mistakes(cls, v: List[str]) -> List[str]:
        """Clean up mistakes list."""
        return [m.strip() for m in v if m.strip()]

    @field_validator('self_test')
    @classmethod
    def validate_self_test(cls, v: List[str]) -> List[str]:
        """Ensure questions end with '?' and are not empty."""
        cleaned = []
        for q in v:
            q = q.strip()
            if q:
                if not q.endswith('?'):
                    q = q + '?'
                cleaned.append(q)
        return cleaned

    @field_validator('prerequisites')
    @classmethod
    def validate_prerequisites(cls, v: List[str]) -> List[str]:
        """Clean prerequisites list."""
        return [p.strip() for p in v if p.strip()]

    @field_validator('further_reading')
    @classmethod
    def validate_further_reading(cls, v: List[str]) -> List[str]:
        """Ensure resources follow expected format (contain book/chapter/link info)."""
        cleaned = []
        for resource in v:
            resource = resource.strip()
            if resource and ('Chapter' in resource or 'http' in resource or 'docs' in resource or 'Book:' in resource):
                cleaned.append(resource)
        return cleaned


# ─── YouTube Work Mode ────────────────────────────────────────────────────────

class WorkBrief(BaseModel):
    title: str = Field(
        description="Short, precise title of what this video covers professionally", min_length=1, max_length=200
    )
    one_liner: str = Field(
        description=(
            "One sentence. Slack-message ready. What this video covers and why a professional would care. "
            "Example: 'Deep dive into Redis caching strategies with benchmarks comparing write-through "
            "vs write-behind — relevant if your team is scaling read-heavy APIs.'"
        ), min_length=10, max_length=300
    )
    recommendation: str = Field(
        alias="watch_or_skip",
        description=(
            "Must follow EXACTLY one of these formats: "
            "'Watch — [one sentence reason why it is worth watching]' "
            "or 'Skip — [one sentence reason why it is not worth the time]'. "
            "Reason must focus on professional value (decision quality, frameworks, tradeoffs, applicability), "
            "not a description of video sections or timestamps. "
            "Correct example: 'Watch — practical framework for evaluating AI automation tools with real cost tradeoffs included.' "
            "Wrong example: 'Watch — the section at 6:00 shows building an automation.'"
        ), min_length=5, max_length=400
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
        ), min_length=1
    )
    tools_mentioned: List[str] = Field(
        description=(
            "Every named tool, library, framework, platform, company, or service mentioned. "
            "Exact names only — no descriptions in this field. "
            "Example: ['Redis', 'Memcached', 'LangChain', 'Supabase', 'Vercel', 'Cloudflare Workers']"
        ), default_factory=list
    )
    decisions_to_make: List[str] = Field(
        description=(
            "Specific decisions the viewer's team should now consider, prompted by this video. "
            "Must be concrete and team-specific, not generic. "
            "Example: 'Evaluate whether adding Redis as a caching layer before the next backend "
            "release would reduce database load below the 70% threshold mentioned'. "
            "NOT: 'Consider caching strategies for your application'. "
            "Only include if a genuine decision is implied by the content."
        ), default_factory=list
    )
    next_actions: List[str] = Field(
        description=(
            "Specific, executable actions. Name the tool, write the command, state the step. "
            "Must be doable in the next few days, not vague goals. "
            "Example: 'Install Redis locally: brew install redis && redis-server'. "
            "Example: 'Read the LangChain caching docs — python.langchain.com/docs/modules/model_io/llms/llm_caching'. "
            "NOT: 'Learn more about caching'. NOT: 'Research this topic further'. "
            "If nothing is genuinely actionable from this video, return empty list."
        ), default_factory=list
    )
    moments: List[TimestampMoment] = Field(
        description="Timestamp-linked moments for key decisions and actions (if video timestamps available).",
        default_factory=list
    )

    @field_validator('title')
    @classmethod
    def title_specificity(cls, v: str) -> str:
        """Ensure title is specific and professional."""
        if v.lower() in ('work brief', 'brief', 'notes', 'summary', 'video summary'):
            raise ValueError('Title must be specific to the video content.')
        return v.strip()

    @field_validator('one_liner')
    @classmethod
    def one_liner_professionalism(cls, v: str) -> str:
        """Ensure one_liner is professional and focused on value."""
        v = v.strip()
        if 'watch this' in v.lower() or 'check this out' in v.lower():
            raise ValueError('One-liner should focus on professional value, not casual language.')
        return v

    @field_validator('recommendation')
    @classmethod
    def recommendation_format(cls, v: str) -> str:
        """Ensure recommendation starts with Watch/Skip/Skim."""
        v = v.strip()
        if not any(v.lower().startswith(prefix) for prefix in ('watch', 'skip', 'skim')):
            raise ValueError("Recommendation must start with 'Watch', 'Skip', or 'Skim' followed by ' — ' and reason.")
        if ' — ' not in v:
            raise ValueError("Recommendation format must be 'Watch/Skip/Skim — reason'. Use ' — ' as separator.")
        return v

    @field_validator('key_points')
    @classmethod
    def validate_key_points(cls, v: List[str]) -> List[str]:
        """Ensure key points are actionable, not generic."""
        cleaned = []
        for point in v:
            point = point.strip()
            if point and len(point.split()) > 3:  # Ensure meaningful content
                if not point.lower().startswith(('key point:', 'point:')):
                    cleaned.append(point)
        if not cleaned:
            raise ValueError('At least one meaningful key point is required.')
        return cleaned

    @field_validator('tools_mentioned')
    @classmethod
    def validate_tools(cls, v: List[str]) -> List[str]:
        """Ensure tool names are exact and not descriptions."""
        cleaned = []
        for tool in v:
            tool = tool.strip()
            if tool and len(tool) > 1 and not tool.lower().endswith(('is', 'was', 'for', 'with')):
                cleaned.append(tool)
        return cleaned

    @field_validator('decisions_to_make')
    @classmethod
    def validate_decisions(cls, v: List[str]) -> List[str]:
        """Clean decisions, ensure they're specific."""
        cleaned = []
        for decision in v:
            decision = decision.strip()
            if decision and len(decision.split()) > 4:
                cleaned.append(decision)
        return cleaned

    @field_validator('next_actions')
    @classmethod
    def validate_next_actions(cls, v: List[str]) -> List[str]:
        """Ensure actions are specific and actionable."""
        cleaned = []
        for action in v:
            action = action.strip()
            if action and len(action.split()) > 3:
                if not action.lower().startswith(('learn', 'research', 'study')):
                    cleaned.append(action)
        return cleaned

    @property
    def watch_or_skip(self) -> str:
        """Backward-compatible accessor for older callers."""
        return self.recommendation

    model_config = {"populate_by_name": True}


# ─── Study Session Mode ───────────────────────────────────────────────────────

class SourceCitation(BaseModel):
    source_index: int
    timestamp_or_page: str
    quote: str


class ConceptMapping(BaseModel):
    concept_name: str = Field(validation_alias=AliasChoices('concept_name', 'name'))
    best_source_index: int = Field(validation_alias=AliasChoices('best_source_index', 'best_source', 'source_index'))
    best_explanation: str = Field(validation_alias=AliasChoices('best_explanation', 'explanation'))
    supporting_sources: List[int] = Field(default_factory=list)
    timestamp_or_page: str = Field(validation_alias=AliasChoices('timestamp_or_page', 'location', 'timestamp'))

    @field_validator('best_source_index', mode='before')
    @classmethod
    def parse_source_index(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Match "SOURCE 1" or just "1"
            match = re.search(r'\d+', v)
            if match:
                return int(match.group())
        return 0


class SourceContradiction(BaseModel):
    topic: str = Field(validation_alias=AliasChoices('topic', 'concept'))
    source_a_index: int = Field(validation_alias=AliasChoices('source_a_index', 'source_a', 'source_A'))
    source_a_says: str = Field(validation_alias=AliasChoices('source_a_says', 'statement_a', 'statement_A'))
    source_b_index: int = Field(validation_alias=AliasChoices('source_b_index', 'source_b', 'source_B'))
    source_b_says: str = Field(validation_alias=AliasChoices('source_b_says', 'statement_b', 'statement_B'))
    resolution: Optional[str] = Field(default=None, validation_alias=AliasChoices('resolution', 'more_accurate'))

    @field_validator('source_a_index', 'source_b_index', mode='before')
    @classmethod
    def parse_index(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            match = re.search(r'\d+', v)
            if match:
                return int(match.group())
        return 0


class KnowledgeMap(BaseModel):
    concepts: List[ConceptMapping] = Field(default_factory=list)
    agreements: List[str] = Field(default_factory=list)
    contradictions: List[SourceContradiction] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list)


class KnowledgeCheckQuestion(BaseModel):
    id: Optional[str] = None
    question: str
    type: str
    difficulty: str
    answered: bool = False
    user_answer: Optional[str] = None
    evaluation: Optional[dict] = None


class TutorOutput(BaseModel):
    foundation: str
    foundation_source_index: int = Field(validation_alias=AliasChoices('foundation_source_index', 'foundation_source', 'source_index'))
    foundation_timestamp_or_page: str = Field(validation_alias=AliasChoices('foundation_timestamp_or_page', 'location', 'timestamp'))
    core_teaching: str
    core_citations: List[SourceCitation] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)
    knowledge_check: List[KnowledgeCheckQuestion] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)

    @field_validator('foundation_source_index', mode='before')
    @classmethod
    def parse_foundation_index(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            match = re.search(r'\d+', v)
            if match:
                return int(match.group())
        return 0


class QuestionEvaluation(BaseModel):
    correct: str = Field(validation_alias=AliasChoices('correct', 'status', 'result'))
    
    @field_validator('correct', mode='before')
    @classmethod
    def validate_correctness(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "partial"
        v = v.lower().strip()
        if v in ("true", "correct", "yes", "right"):
            return "true"
        if "partially" in v or "partial" in v:
            return "partial"
        if v in ("false", "incorrect", "no", "wrong"):
            return "false"
        # Fallback for longer phrases like "The answer is correct"
        if "incorrect" in v: return "false"
        if "correct" in v: return "true"
        return "partial"
    feedback: str
    misconception: Optional[str] = None
    correction: Optional[str] = None
    ready_to_advance: bool = Field(default=True)
    cited_source_index: int = Field(validation_alias=AliasChoices('cited_source_index', 'source_index', 'source'))

    @field_validator('cited_source_index', mode='before')
    @classmethod
    def parse_cited_index(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            match = re.search(r'\d+', v)
            if match:
                return int(match.group())
        return 0


# ─── Cross-Source Synthesis ───────────────────────────────────────────────────

class SourceSummary(BaseModel):
    """Summary of one source in a synthesis."""
    source_id: str = Field(description="Session ID or source identifier", min_length=1, max_length=500)
    source_title: str = Field(description="Title or name of the source", min_length=1, max_length=300)
    source_type: str = Field(description="youtube, pdf, article, or meeting", min_length=1, max_length=50)
    key_points: List[str] = Field(description="3-5 most important takeaways from this source", min_length=1)


class ConceptComparison(BaseModel):
    """How a concept is treated across sources."""
    concept: str = Field(description="The concept being compared", min_length=1, max_length=500)
    source_treatments: List[str] = Field(
        description="How each source treats this concept - indexed by source",
        min_length=1
    )
    consensus: Optional[str] = Field(
        description="What all sources agree on, if anything",
        default=None
    )
    differences: Optional[List[str]] = Field(
        description="Key differences in treatment across sources",
        default=None
    )


class SynthesisAnalysis(BaseModel):
    """Unified analysis across multiple sources."""
    common_themes: List[str] = Field(
        description="Themes or concepts that appear across 2+ sources",
        min_length=1
    )
    unique_insights: List[str] = Field(
        description="Insights unique to individual sources",
        default_factory=list
    )
    contradictions: List[str] = Field(
        description="Places where sources disagree or have conflicting information",
        default_factory=list
    )
    synthesis_summary: str = Field(
        description="2-3 paragraph synthesis combining all sources into unified analysis",
        min_length=20,
        max_length=2000
    )
    recommended_order: List[int] = Field(
        description="Recommended reading/watching order for sources (by index)",
        default_factory=list
    )
    knowledge_gaps: List[str] = Field(
        description="Topics relevant to user's question not covered by any source",
        default_factory=list
    )


# ─── Before-You-Watch Verdict ────────────────────────────────────────────────

class PreWatchVerdict(BaseModel):
    verdict: str = Field(
        description="One of: Watch, Skim, or Skip", min_length=3, max_length=20
    )
    why: str = Field(
        description="2-3 sentence explanation focused on value for the selected mode/user goal", min_length=10, max_length=300
    )
    best_for: str = Field(
        description="Who should watch this video (specific user type/use case)", min_length=5, max_length=150
    )
    relevant_moments: List[str] = Field(
        description=(
            "3-6 high-signal moments to jump to. Format: 'MM:SS — what is covered'. "
            "If no timestamps exist in transcript, return an empty list."
        ), default_factory=list
    )
    what_youll_miss_if_skip: str = Field(
        description="One sentence: the key thing user would miss by skipping", min_length=5, max_length=200
    )

    @field_validator('verdict')
    @classmethod
    def verdict_valid(cls, v: str) -> str:
        """Ensure verdict is one of the allowed values."""
        v = v.strip().capitalize()
        if v not in ('Watch', 'Skim', 'Skip'):
            raise ValueError("Verdict must be 'Watch', 'Skim', or 'Skip'.")
        return v

    @field_validator('relevant_moments')
    @classmethod
    def validate_moments(cls, v: List[str]) -> List[str]:
        """Ensure moments follow MM:SS — description format."""
        cleaned = []
        for moment in v:
            moment = moment.strip()
            if moment and ' — ' in moment:
                cleaned.append(moment)
        return cleaned


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
