import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from models import ActionItemList, MeetingSummary, VideoInsights

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


# ─── YouTube Mode — Mode-aware extraction ────────────────────────────────────
#
# mode can be: "study" | "work" | "quick"
# sections is a dict of which sections to include in the prompt
#
# Mode changes the PROMPT sent to AI — different tone, depth, length
# Sections changes WHAT is extracted — user controls output fields

MODE_PROMPTS = {
    "study": {
        "persona": """You are a subject-matter expert and rigorous note-taker.
Your job is to extract knowledge from this video as if you are preparing
revision notes for a student who will be examined on this content.

Rules you must follow:
- Preserve ALL technical terms, named concepts, formulas, and proper nouns exactly as mentioned
- If the speaker defines something, capture that definition precisely
- If numbers, dates, measurements, or statistics are mentioned, include them
- Identify cause-effect relationships and explain them clearly
- Do NOT simplify technical content — the student needs accuracy, not dumbing down
- If the video builds on prior knowledge, mention what prerequisite concepts are assumed""",

        "summary": """Write a 4-5 sentence technical summary that captures:
(1) what the video is specifically about,
(2) the core mechanism, argument, or process explained,
(3) the key conclusion or result.
Do not be vague. Be precise. Include technical terms.""",

        "takeaways": """Extract up to 10 key learning points.
Each point must be a complete, standalone piece of knowledge —
not a vague observation like 'diffraction is important' but
a precise statement like 'Bragg diffraction occurs when nλ = 2d·sinθ,
where d is interplanar spacing and θ is the glancing angle.'
If equations, conditions, or constraints were mentioned, include them.""",

        "topics": """List up to 6 topics or subtopics covered in order of appearance.
Label them as a structured outline — these should reflect the actual
intellectual structure of the video, not generic categories.""",

        "action_items": """List up to 5 specific follow-up actions for a student:
- papers or textbooks to read
- problems to solve or experiments to try
- related concepts to look up
- things to memorise or derive yourself
Be specific — 'Read Chapter 3 of Kittel' is better than 'Read more about diffraction'.""",
    },

    "work": {
        "persona": """You are a senior professional who watched this video so your colleagues don't have to.
Your job is to extract everything someone needs to apply this content at work —
whether that's a developer learning a new tool, a designer watching a talk,
a founder understanding a market, or a team lead evaluating a technology.

Rules you must follow:
- Focus on what is APPLICABLE, not what is interesting
- Distinguish between what is opinion vs what is evidence-based
- If tools, frameworks, libraries, companies, or methods are mentioned by name — capture them
- If the speaker makes a recommendation, capture it with their reasoning
- Skip historical context and filler — only include what changes how someone works""",

        "summary": """Write a 3-sentence brief as if you are sending a Slack message to your team:
(1) what this video covers and why it's relevant,
(2) the single most important thing to know,
(3) whether the team should watch it or just read these notes.""",

        "takeaways": """Extract up to 7 insights that are directly applicable at work.
Each insight should answer: 'So what? What do I do differently because of this?'
Include specific tools, metrics, methods, or frameworks mentioned.
If the speaker compared options or gave a recommendation, include it.""",

        "topics": """List up to 5 topics covered, framed as professional categories
e.g. 'Performance optimisation', 'Team structure', 'Cost tradeoffs' —
not generic labels. These should help a colleague decide which section is relevant to them.""",

        "action_items": """List up to 6 concrete next steps a professional should take after watching.
These must be specific and immediately actionable:
- tools to try or install
- processes to change
- decisions to make
- things to research further with specific search terms
- people or companies to look up
Vague actions like 'think about this' are not allowed.""",
    },

    "quick": {
        "persona": """You are a brilliant friend who just watched this video and is explaining it to someone
who has 60 seconds and zero patience. You know everything but speak simply.
No jargon unless absolutely necessary. No filler. No 'in conclusion'.
Write like a human, not a robot. The person reading this should feel like
they can confidently talk about this video at dinner tonight.""",

        "summary": """Write 2-3 sentences max. Cover: what it's about, the most surprising or interesting thing,
and the one thing worth remembering. Make it conversational and engaging — not a Wikipedia intro.""",

        "takeaways": """Give exactly 3-5 things worth knowing.
Make each one genuinely interesting or surprising — not obvious filler.
These should be the things that make someone go 'oh I didn't know that'.
Write each as a punchy, complete thought.""",

        "topics": """List 2-3 topics only. Keep labels short and plain — what a normal person would say,
not an academic category.""",

        "action_items": """Only include this if the video genuinely had something worth doing.
1-2 actions max. If there's nothing actionable, return an empty list —
do NOT make up generic actions just to fill the field.""",
    },
}

DEFAULT_SECTIONS = {
    "summary":      True,
    "key_takeaways": True,
    "topics":       True,
    "action_items": True,
}


def extract_video_insights(
    transcript: str,
    mode: str = "study",
    sections: dict = None
) -> VideoInsights:
    """
    Extract insights from a YouTube transcript.

    Args:
        transcript: raw transcript text
        mode: "study" | "work" | "quick" — changes AI tone and depth
        sections: dict of which fields to extract
                  e.g. {"summary": True, "key_takeaways": True, "topics": False, "action_items": False}
    """
    if sections is None:
        sections = DEFAULT_SECTIONS.copy()

    m = MODE_PROMPTS.get(mode, MODE_PROMPTS["study"])

    # Build the instruction list based on which sections are enabled
    instructions = [f"- A short title describing what the video is about (always required)"]

    if sections.get("summary", True):
        instructions.append(f"- Summary: {m['summary']}")
    else:
        instructions.append("- summary: return an empty string ''")

    if sections.get("key_takeaways", True):
        instructions.append(f"- Key takeaways: {m['takeaways']}")
    else:
        instructions.append("- key_takeaways: return an empty list []")

    if sections.get("topics", True):
        instructions.append(f"- Topics covered: {m['topics']}")
    else:
        instructions.append("- topics_covered: return an empty list []")

    if sections.get("action_items", True):
        instructions.append(f"- Action items: {m['action_items']}")
    else:
        instructions.append("- action_items: return an empty list []")

    instructions_text = "\n    ".join(instructions)

    prompt = f"""
    {m['persona']}

    Someone doesn't have time to watch this video — give them what they need.

    Provide:
    {instructions_text}

    VIDEO TRANSCRIPT:
    {transcript}
    """

    structured_llm = get_model().with_structured_output(VideoInsights)
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