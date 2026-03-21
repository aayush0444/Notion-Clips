import os
from typing import Union
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from models import ActionItemList, MeetingSummary, VideoInsights, StudyNotes, WorkBrief

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL    = "openai/gpt-4o-mini"


def get_openrouter_key():
    user_key = os.getenv("OPENROUTER_API_KEY")
    if user_key:
        return user_key
    try:
        app_key = st.secrets.get("OPENROUTER_API_KEY", "")
        if app_key:
            return app_key
    except Exception:
        pass
    return None


def get_google_key():
    user_key = os.getenv("GOOGLE_API_KEY")
    if user_key:
        return user_key
    try:
        return st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        return None


def get_model():
    or_key = get_openrouter_key()
    if or_key:
        return ChatOpenAI(
            model=OPENROUTER_MODEL,
            api_key=or_key,
            base_url=OPENROUTER_BASE_URL,
            temperature=0
        )
    g_key = get_google_key()
    if g_key:
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    raise ValueError(
        "No AI key found. Please add your key in Settings."
    )


# ─── Meeting Mode ─────────────────────────────────────────────────────────────

def extract_tasks(transcript: str) -> ActionItemList:
    structured_llm = get_model().with_structured_output(ActionItemList)
    prompt = f"""
    You are an expert meeting analyst.
    Extract ALL action items and tasks from this transcript.
    For each task identify:
    - The specific task to be done
    - Who is responsible (use "Team" if unclear)
    - Due date in YYYY-MM-DD format, or "TBD"
    - Priority: High (urgent), Medium (important), Low (nice to have)
    TRANSCRIPT:
    {transcript}
    """
    return structured_llm.invoke(prompt)


def extract_meeting_summary(transcript: str) -> MeetingSummary:
    structured_llm = get_model().with_structured_output(MeetingSummary)
    prompt = f"""
    You are an expert meeting analyst.
    Analyze this meeting transcript and provide:
    - A concise meeting title (max 8 words)
    - An executive summary (3-4 sentences: what was discussed and decided)
    - Key decisions made (up to 5)
    - Clear next steps agreed upon (up to 5)
    TRANSCRIPT:
    {transcript}
    """
    return structured_llm.invoke(prompt)


# ─── YouTube Mode — Mode-aware prompts ───────────────────────────────────────
#
# Each mode has a completely different persona, output expectation, and depth.
# The prompts are written to match the Pydantic model fields exactly.
# Study → StudyNotes, Work → WorkBrief, Quick → VideoInsights

STUDY_PROMPT = """
You are a senior university lecturer and expert note-taker who has just watched this video.
Your job is to produce study notes that are ACTUALLY USEFUL for a student who will be
EXAMINED on this material. Not notes they will passively read — notes they will study from.

STRICT RULES:
1. core_concept: Write ONE sentence that captures the single most important idea.
   This is what the student writes on their hand before an exam. Be precise.
   Bad: "This video covers diffraction." Good: "Single slit diffraction produces
   a central maximum at θ=0 and dark fringes where a·sinθ = nλ, with n = 1,2,3..."

2. formula_sheet: For EVERY formula, equation, or mathematical relationship in the video,
   write it out AND define EVERY variable in plain English.
   Format: "formula — variable = meaning, variable = meaning"
   If there are no formulas, return an empty list — do NOT invent formulas.

3. key_facts: These must be specific enough to appear word-for-word on an exam.
   Include: numbers, ratios, conditions, exceptions, limits mentioned in the video.
   Bad: "The central maximum is the brightest." 
   Good: "The central maximum has twice the angular width of all secondary maxima,
   with half-width θ ≈ λ/a for small angles."

4. common_mistakes: What do students actually get wrong on exams about THIS topic?
   Include mistakes the speaker warns against AND well-known confusions in this subject.
   Be specific — not generic study advice.
   Bad: "Read the question carefully."
   Good: "Applying d·sinθ = nλ (double slit MAXIMA) to single slit — the same letters
   appear but single slit minima use a·sinθ = nλ."

5. self_test: Write questions a professor would put on an exam from THIS video's content.
   Include: at least one definition, one calculation/derivation, one conceptual.
   Write ONLY the question — no answers. The student must attempt them first.

6. prerequisites: Name concepts precisely. "Huygens' Principle" not "wave theory."
   Only include what is genuinely needed to understand this specific video.

7. further_reading: Minimum format is "Chapter N, Book Title by Author."
   Use standard university-level textbooks for this subject.

VIDEO TRANSCRIPT:
{transcript}
"""

WORK_PROMPT = """
You are a senior professional who watched this video so your team doesn't have to.
Your job is to extract everything needed to decide: should the team watch this?
And if they do, what do they actually DO differently afterward?

STRICT RULES:
1. one_liner: One sentence. Slack-ready. "This covers X and is relevant if your team does Y."
   Someone must be able to forward this to their manager and have it make sense.

2. watch_or_skip: Begin with exactly "Watch" or "Skip" then a colon then one reason.
   If Watch: reference a specific section, timestamp, or use case.
   If Skip: explain what the viewer already knows that makes this redundant.

3. key_points: Each point must answer "So what? What changes about how we work?"
   Include the speaker's actual recommendations, benchmarks, and named comparisons.
   If they said "X is 4x faster than Y at Z workloads" — write that exactly.
   NOT: "The speaker discussed performance." YES: "Redis showed 4x lower latency
   than Postgres for session reads in the benchmark at 10k concurrent users."

4. tools_mentioned: Exact names only. No descriptions. No sentences.
   "Redis", "LangChain", "Railway". These are searchable tags.

5. decisions_to_make: Concrete decisions tied to this video's content.
   Format: "Evaluate whether to [do X] given [evidence from video]."
   These should be things a team lead could put in a Notion task today.

6. next_actions: Enough detail to execute right now.
   Include commands, URLs, search terms, specific chapter/doc references.
   "brew install redis && redis-server" not "try Redis."

VIDEO TRANSCRIPT:
{transcript}
"""

QUICK_PROMPT = """
You are a brilliant friend who just watched this video and is explaining it to someone
who has 60 seconds and zero patience. You know everything but speak simply.
No jargon unless absolutely necessary. No filler. No "in conclusion."
Write like a human, not a robot. The person reading this should feel like
they can confidently talk about this video at dinner tonight.

Provide:
- A short conversational title
- 2-3 sentence summary: what it's about, the most surprising thing, the one thing to remember
- 3-5 genuinely interesting takeaways (not obvious filler)
- 2-3 topic labels (plain language, not academic categories)
- 0-2 action items — only if the video genuinely had something worth doing

VIDEO TRANSCRIPT:
{transcript}
"""

DEFAULT_SECTIONS = {
    "summary":       True,
    "key_takeaways": True,
    "topics":        True,
    "action_items":  True,
}


def extract_video_insights(
    transcript: str,
    mode: str = "study",
    sections: dict = None
) -> Union[StudyNotes, WorkBrief, VideoInsights]:
    """
    Extract insights from a YouTube transcript.

    Args:
        transcript: raw transcript text
        mode: "study" | "work" | "quick" — determines output Pydantic model and AI prompt
        sections: only used for Quick mode (legacy sections dict) — ignored for Study/Work

    Returns:
        StudyNotes  if mode == "study"
        WorkBrief   if mode == "work"
        VideoInsights if mode == "quick"
    """
    if sections is None:
        sections = DEFAULT_SECTIONS.copy()

    if mode == "study":
        structured_llm = get_model().with_structured_output(StudyNotes)
        prompt = STUDY_PROMPT.format(transcript=transcript)
        return structured_llm.invoke(prompt)

    elif mode == "work":
        structured_llm = get_model().with_structured_output(WorkBrief)
        prompt = WORK_PROMPT.format(transcript=transcript)
        return structured_llm.invoke(prompt)

    else:
        # Quick mode — uses VideoInsights, same as before
        # sections dict controls which fields the AI is asked to fill
        structured_llm = get_model().with_structured_output(VideoInsights)

        instructions = ["- A short title describing what the video is about (always required)"]

        if sections.get("summary", True):
            instructions.append("- Summary: 2-3 sentences max. What it's about, "
                                 "the most surprising thing, the one thing worth remembering. "
                                 "Conversational tone.")
        else:
            instructions.append("- summary: return empty string ''")

        if sections.get("key_takeaways", True):
            instructions.append("- Key takeaways: exactly 3-5 genuinely interesting points. "
                                 "Not obvious filler. Punchy, complete thoughts.")
        else:
            instructions.append("- key_takeaways: return empty list []")

        if sections.get("topics", True):
            instructions.append("- Topics covered: 2-3 plain-language topic labels only.")
        else:
            instructions.append("- topics_covered: return empty list []")

        if sections.get("action_items", True):
            instructions.append("- Action items: 0-2 only if genuinely actionable. "
                                 "If nothing is worth doing, return empty list.")
        else:
            instructions.append("- action_items: return empty list []")

        instructions_text = "\n    ".join(instructions)

        prompt = f"""
{QUICK_PROMPT.format(transcript="")}

Provide:
{instructions_text}

VIDEO TRANSCRIPT:
{transcript}
"""
        return structured_llm.invoke(prompt)


# ─── Utilities ────────────────────────────────────────────────────────────────

def deduplicate_tasks(task_data: ActionItemList) -> ActionItemList:
    seen = set()
    unique = []
    for item in task_data.items:
        fingerprint = (item.task.lower().strip(), item.assignee.lower().strip())
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(item)
    task_data.items = unique
    return task_data


def calculate_accuracy(task_list: ActionItemList) -> float:
    if not task_list.items:
        return 0.0
    scores = []
    for item in task_list.items:
        score = 0
        if item.task and len(item.task.split()) >= 3:   score += 40
        if item.assignee and item.assignee != "Team":   score += 25
        if item.due_date and item.due_date != "TBD":    score += 20
        if item.priority in ("High", "Medium", "Low"):  score += 15
        scores.append(score)
    return round(sum(scores) / len(scores), 1)