import os
import re
import logging
import requests
import streamlit as st
from dotenv import load_dotenv
from typing import Union, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from models import (
    ActionItemList, MeetingSummary, VideoInsights,
    StudyNotes, WorkBrief, _ChunkExtract
)
from backend.supabase_client import get_session

load_dotenv()

logger = logging.getLogger("notionclips.gemini")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL    = "openai/gpt-4o-mini"


# ─── Model Provider ───────────────────────────────────────────────────────────

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


# ─── Video Length Scaling ─────────────────────────────────────────────────────
#
# This is the core fix for the "2-hour video gets 5 points" problem.
# Output depth scales with content length. No artificial caps.

def _get_length_profile(word_count: int) -> dict:
    """
    Returns expected output depth based on transcript word count.
    ~130 words/minute of speech, so:
      2000 words  ≈ 15 min
      6000 words  ≈ 45 min
      10000 words ≈ 75 min
      16000 words ≈ 2 hours
    """
    if word_count < 2000:
        return {
            "category":      "short",
            "label":         "short (~15 min)",
            "key_facts":     "5 to 10",
            "self_test":     "3 to 4",
            "key_points":    "4 to 7",
        }
    elif word_count < 6000:
        return {
            "category":      "medium",
            "label":         "medium (~45 min)",
            "key_facts":     "12 to 20",
            "self_test":     "5 to 7",
            "key_points":    "8 to 14",
        }
    elif word_count < 10000:
        return {
            "category":      "long",
            "label":         "long (~75 min)",
            "key_facts":     "20 to 32",
            "self_test":     "7 to 10",
            "key_points":    "12 to 20",
        }
    else:
        return {
            "category":      "very_long",
            "label":         "very long (2h+)",
            "key_facts":     "30 to 50",
            "self_test":     "10 to 14",
            "key_points":    "18 to 28",
        }


CHUNK_SIZE_WORDS = 4000    # words per chunk for long video processing
CHUNK_OVERLAP    = 200     # overlap between chunks to avoid missing context
CHUNKING_THRESHOLD = 8000  # word count above which chunking is used


# ─── Chunk Processing ─────────────────────────────────────────────────────────

def _split_into_chunks(transcript: str) -> List[str]:
    """Split a long transcript into overlapping chunks."""
    words = transcript.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE_WORDS, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start = end - CHUNK_OVERLAP  # overlap
    return chunks


def _extract_chunk(chunk_text: str, chunk_label: str, mode: str) -> _ChunkExtract:
    """Extract raw facts from a single transcript chunk."""
    llm = get_model().with_structured_output(_ChunkExtract)

    if mode == "study":
        prompt = f"""
You are extracting raw content from section "{chunk_label}" of a longer video transcript.

Your ONLY job is to pull out what is explicitly in this section.
Do NOT add external knowledge. Do NOT infer. Do NOT fill gaps.
If something is not explicitly stated in this text, do not include it.

Extract:
- facts: Every specific technical statement, definition, number, condition, limit.
  Include approximate timestamps like (≈12:30) where identifiable from [MM:SS] markers.
  Be precise — "a·sinθ = nλ is the condition for destructive interference" not "diffraction is explained".
- formulas: Every equation or mathematical relationship. Format: "formula — variable definitions"
- mistakes: Only if the speaker explicitly warns about errors or common misconceptions.
- potential_questions: Statements in this section that could become exam questions.
- tools: Leave empty for study content.
- key_insights: Leave empty for study content.

TRANSCRIPT SECTION:
{chunk_text}
"""
    elif mode == "work":
        prompt = f"""
You are extracting raw content from section "{chunk_label}" of a longer professional video transcript.

Do NOT add external knowledge. Do NOT infer. Only what is explicitly stated.

Extract:
- facts: Leave empty.
- formulas: Leave empty.
- mistakes: Anti-patterns or warnings explicitly mentioned.
- potential_questions: Decisions or open questions raised in this section.
- tools: Every named tool, library, framework, platform, company mentioned. Exact names only.
- key_insights: Insights that change how a professional works. Include specific numbers/benchmarks if mentioned.

TRANSCRIPT SECTION:
{chunk_text}
"""
    else:  # quick
        prompt = f"""
Extract the most interesting and surprising facts from this transcript section.
Only include what is explicitly stated. Do not add external knowledge.

- facts: Interesting or surprising statements.
- formulas: Any equations mentioned.
- mistakes: Any warnings or corrections.
- potential_questions: Leave empty.
- tools: Named tools or technologies mentioned.
- key_insights: The most noteworthy insights.

TRANSCRIPT SECTION:
{chunk_text}
"""
    return llm.invoke(prompt)


def _synthesize_study_notes(
    chunk_results: List[_ChunkExtract],
    profile: dict,
    transcript_opening: str,
    has_timestamps: bool = False
) -> StudyNotes:
    """Synthesize chunk extractions into a final StudyNotes object."""

    all_facts      = [f for c in chunk_results for f in c.facts]
    all_formulas   = [f for c in chunk_results for f in c.formulas]
    all_mistakes   = [m for c in chunk_results for m in c.mistakes]
    all_questions  = [q for c in chunk_results for q in c.potential_questions]

    raw = f"""
OPENING OF VIDEO (first ~500 words for title/concept context):
{transcript_opening[:2500]}

ALL EXTRACTED FACTS ({len(all_facts)} items across all sections):
{chr(10).join(f'• {f}' for f in all_facts)}

ALL FORMULAS ({len(all_formulas)} items):
{chr(10).join(f'• {f}' for f in all_formulas)}

ALL WARNINGS / COMMON MISTAKES ({len(all_mistakes)} items):
{chr(10).join(f'• {m}' for m in all_mistakes)}

ALL POTENTIAL QUESTIONS ({len(all_questions)} items):
{chr(10).join(f'• {q}' for q in all_questions)}
"""

    llm = get_model().with_structured_output(StudyNotes)
    prompt = f"""
You are synthesizing raw extracted data from a {profile['label']} video into structured study notes.

The data was extracted from the video in chunks to ensure nothing was missed.
Your job: organise it into a coherent, accurate, genuinely useful study resource.

CRITICAL RULES — follow these exactly:
1. ONLY use information from the extracted data above. Do NOT add external knowledge.
2. Remove duplicates — if the same fact appears multiple times, keep the most precise version.
3. Do NOT invent formulas, facts, or questions not present in the extracted data.
4. core_concept: ONE sentence — the single most important idea from the entire video.
5. formula_sheet: Include EVERY formula found. Format: "formula — what each variable means in full".
6. key_facts: For a {profile['label']} video, extract {profile['key_facts']} facts.
   Each must be a complete, precise, standalone technical statement.
   {('Include (≈MM:SS) timestamps — e.g. (≈08:30) — where [MM:SS] markers appear next to facts.' if has_timestamps else 'Do NOT add any timestamps — this transcript has no timing data. Invented timestamps destroy user trust.')}
7. self_test: Generate {profile['self_test']} exam-style questions answerable from the extracted facts.
   Mix: definition, calculation, conceptual, application. Questions only — no answers.
8. common_mistakes: Identify 2-4 errors students commonly make about the SPECIFIC
   concepts taught in this video. Two sources are valid:
   (a) Anything explicitly warned about in the extracted data.
   (b) Errors that naturally arise from the specific content taught — e.g. if the video
       teaches centripetal acceleration points inward, a natural mistake is thinking it
       points outward (centrifugal force confusion).
   Be specific to THIS content. Generic advice like "study more carefully" is not valid.
   Do NOT return an empty list unless the video is purely motivational with zero technical content.
9. prerequisites: Be specific — name the exact concept, not a general field.
10. further_reading: Only if genuinely implied by the content. Chapter + book + author minimum.

{raw}
"""
    return llm.invoke(prompt)


def _synthesize_work_brief(
    chunk_results: List[_ChunkExtract],
    profile: dict,
    transcript_opening: str,
    has_timestamps: bool = False
) -> WorkBrief:
    """Synthesize chunk extractions into a final WorkBrief object."""

    all_insights = [i for c in chunk_results for i in c.key_insights]
    all_tools    = list(set(t for c in chunk_results for t in c.tools))
    all_decisions = [d for c in chunk_results for d in c.potential_questions]
    all_mistakes  = [m for c in chunk_results for m in c.mistakes]

    raw = f"""
OPENING OF VIDEO (for title/context):
{transcript_opening[:2500]}

ALL KEY INSIGHTS ({len(all_insights)} items):
{chr(10).join(f'• {i}' for i in all_insights)}

ALL TOOLS MENTIONED:
{', '.join(all_tools) if all_tools else 'None identified'}

ALL DECISIONS / OPEN QUESTIONS ({len(all_decisions)} items):
{chr(10).join(f'• {d}' for d in all_decisions)}

ALL WARNINGS / ANTI-PATTERNS ({len(all_mistakes)} items):
{chr(10).join(f'• {m}' for m in all_mistakes)}
"""

    llm = get_model().with_structured_output(WorkBrief)
    prompt = f"""
You are synthesizing raw extracted data from a {profile['label']} professional video into a work brief.

CRITICAL RULES:
1. ONLY use information from the extracted data. Do NOT add external knowledge.
2. watch_or_skip: MUST follow this exact format:
   "Watch — [one sentence reason why it is worth watching]"
   or
   "Skip — [one sentence reason why it is not worth the time]".
   The reason must be about professional value, not a description of what happens in the video.
   Good: "Watch — practical framework for evaluating AI automation tools with real cost tradeoffs included."
   Bad: "Watch — the section at 6:00 shows building an automation."
3. key_points: For a {profile['label']} video, provide {profile['key_points']} points.
   Each must say what it means for how someone works, not just what was said.
   Include specific numbers or benchmarks where present.
4. tools_mentioned: Exact names only. No descriptions.
5. decisions_to_make: Specific, team-relevant decisions. Not generic advice.
6. next_actions: Doable this week. Specific enough to execute immediately.
   "Read X at URL" or "Run Y command" — not "learn more about Z".

{raw}
"""
    return llm.invoke(prompt)


# ─── Single-Pass Extraction ───────────────────────────────────────────────────

def _extract_single_pass_study(
    transcript: str,
    profile: dict,
    has_timestamps: bool = False
) -> StudyNotes:
    """Single-pass study extraction for short/medium videos."""
    llm = get_model().with_structured_output(StudyNotes)

    prompt = f"""
You are an expert note-taker watching a {profile['label']} video.
Your job: produce study notes so precise and complete that a student can revise
from them without watching the video — while also knowing exactly where to go back
in the video if they need more context.

THIS IS A {profile['label'].upper()} VIDEO. Scale your output accordingly.

ABSOLUTE RULES — violating these makes the output useless:
1. ONLY include what is explicitly stated in the transcript.
   Do NOT add external knowledge. Do NOT fill gaps. Do NOT infer.
   If you are not certain something was said, leave it out.
2. key_facts: Extract {profile['key_facts']} facts for this length of video.
   Each fact must be precise, complete, and standalone.
   {('Include (≈MM:SS) timestamp where a nearby [MM:SS] marker exists in the transcript — e.g. (≈08:30).' if has_timestamps else 'Do NOT add any timestamps — this transcript has no timing data. Inventing them is hallucination.')}
   "The condition for destructive interference is a·sinθ = nλ (≈08:30)" is good.
   "The speaker discusses diffraction" is useless — never do this.
3. formula_sheet: Include EVERY formula mentioned. Define EVERY variable.
   "a·sinθ = nλ — a is slit width in metres, θ is angle from centre,
   n is any non-zero integer, λ is wavelength" is correct.
   Empty list is only acceptable if the video genuinely has no formulas.
4. self_test: {profile['self_test']} questions. Must be answerable from transcript alone.
   Mix definition, calculation, conceptual, and application questions.
5. core_concept: ONE sentence maximum. The single most important idea.
6. common_mistakes: Identify 2-4 errors students commonly make about the SPECIFIC
   concepts taught in this video. Two sources are valid:
   (a) Anything the speaker explicitly warns about or corrects.
   (b) Errors that naturally arise from the specific content — e.g. if the video
       teaches that a·sinθ = nλ gives MINIMA, a natural mistake is thinking it gives maxima.
   Be specific to THIS content. Generic study advice is not valid.
   Do NOT return an empty list unless the video has zero technical content.
7. further_reading: Chapter + book + author. Empty list if nothing implied.

VIDEO TRANSCRIPT:
{transcript}
"""
    return llm.invoke(prompt)


def _extract_single_pass_work(
    transcript: str,
    profile: dict,
    has_timestamps: bool = False
) -> WorkBrief:
    """Single-pass work extraction for short/medium videos."""
    llm = get_model().with_structured_output(WorkBrief)

    prompt = f"""
You are a senior professional who just watched this {profile['label']} video
so your colleagues don't have to. Produce a brief they can read in 2 minutes
and know exactly whether to watch it and what to do about it.

THIS IS A {profile['label'].upper()} VIDEO. Scale output accordingly.

ABSOLUTE RULES:
1. ONLY include what is explicitly stated in the transcript.
   Do NOT add knowledge the video didn't cover. Do NOT fill gaps.
2. watch_or_skip: MUST follow this exact format:
   "Watch — [one sentence reason why it is worth watching]"
   or
   "Skip — [one sentence reason why it is not worth the time]".
   The reason must be about professional value, not a play-by-play of video sections or timestamps.
   Good: "Watch — practical framework for evaluating AI automation tools with real cost tradeoffs included."
   Bad: "Watch — the section at 6:00 shows building an automation."
3. key_points: {profile['key_points']} points for this video length.
   Focus on what changes how the viewer works. Include specific numbers and benchmarks.
4. tools_mentioned: Exact names only — no descriptions in this field.
5. decisions_to_make: Real decisions implied by the content. Be specific.
   "Evaluate Redis as caching layer" is good. "Consider caching" is useless.
6. next_actions: Executable this week. Name the tool, write the command,
   give the URL. "brew install redis" is good. "Learn more" is useless.
   Return empty list if nothing is genuinely actionable.

VIDEO TRANSCRIPT:
{transcript}
"""
    return llm.invoke(prompt)


def _extract_single_pass_quick(
    transcript: str,
    profile: dict,
    sections: dict
) -> VideoInsights:
    """Single-pass quick mode extraction."""
    llm = get_model().with_structured_output(VideoInsights)

    sections_instruction = []
    if not sections.get("summary", True):
        sections_instruction.append("- summary: return empty string ''")
    if not sections.get("key_takeaways", True):
        sections_instruction.append("- key_takeaways: return empty list []")
    if not sections.get("topics", True):
        sections_instruction.append("- topics_covered: return empty list []")
    if not sections.get("action_items", True):
        sections_instruction.append("- action_items: return empty list []")

    disabled_note = ("\nUser disabled these sections — return empty for them:\n" +
                     "\n".join(sections_instruction)) if sections_instruction else ""

    prompt = f"""
You are a brilliant, well-informed friend who just watched this {profile['label']} video.
Explain it to someone who has 2 minutes and zero patience.

THIS IS A {profile['label'].upper()} VIDEO.
key_takeaways: scale to video length — {profile['key_facts']} items is appropriate.
Do not cap at 7 if the video is long.

Rules:
1. Only include what is explicitly in the transcript. No external knowledge.
2. Conversational tone — not academic, not bullet-pointed corporate speak.
3. key_takeaways: the things that make someone go "oh I didn't know that."
   Not obvious filler. Not generic observations.
4. action_items: only if genuinely actionable. Empty list if nothing to do.
{disabled_note}

VIDEO TRANSCRIPT:
{transcript}
"""
    return llm.invoke(prompt)


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def extract_video_insights(
    transcript: str,
    mode: str = "study",
    sections: dict = None,
    duration_minutes: float = 0
) -> Union[StudyNotes, WorkBrief, VideoInsights]:
    """
    Extract insights from a YouTube transcript.

    Automatically scales output depth to video length.
    Uses chunked processing for long videos (>8000 words) to prevent
    truncation and hallucination.

    Args:
        transcript:        full transcript text (with [MM:SS] timestamp markers if available)
        mode:              "study" | "work" | "quick"
        sections:          dict of which sections to include (used for quick mode only)
        duration_minutes:  video duration in minutes (for metadata, not used in logic)

    Returns:
        StudyNotes for mode="study"
        WorkBrief  for mode="work"
        VideoInsights for mode="quick"
    """
    if sections is None:
        sections = {
            "summary": True, "key_takeaways": True,
            "topics": True, "action_items": True
        }

    word_count = len(transcript.split())
    profile    = _get_length_profile(word_count)

    # Detect whether real [MM:SS] timestamp markers are embedded.
    # These are only present when the scraping method succeeded.
    # This flag is passed into prompts — if False, AI is explicitly told
    # NOT to add timestamps, preventing hallucinated (≈12:30) on every fact.
    has_timestamps = bool(re.search(r'\[\d{2}:\d{2}\]', transcript))

    # Short/medium videos — single pass (fast, sufficient)
    if word_count <= CHUNKING_THRESHOLD:
        if mode == "study":
            return _extract_single_pass_study(transcript, profile, has_timestamps)
        elif mode == "work":
            return _extract_single_pass_work(transcript, profile, has_timestamps)
        else:
            return _extract_single_pass_quick(transcript, profile, sections)

    # Long videos — chunked extraction then synthesis
    # This prevents hallucination from transcript compression
    chunks = _split_into_chunks(transcript)
    chunk_results = []

    for i, chunk in enumerate(chunks):
        label = f"Section {i+1} of {len(chunks)}"
        result = _extract_chunk(chunk, label, mode)
        chunk_results.append(result)

    # Use first ~500 words as opening context for title generation
    transcript_opening = " ".join(transcript.split()[:500])

    if mode == "study":
        return _synthesize_study_notes(chunk_results, profile, transcript_opening, has_timestamps)
    elif mode == "work":
        return _synthesize_work_brief(chunk_results, profile, transcript_opening, has_timestamps)
    else:
        # For quick mode on long videos, synthesize into VideoInsights
        all_facts = [f for c in chunk_results for f in c.facts + c.key_insights]
        synthesized_text = (
            f"VIDEO OPENING: {transcript_opening}\n\n"
            f"KEY POINTS FROM ALL SECTIONS:\n" +
            "\n".join(f"• {f}" for f in all_facts[:60])
        )
        return _extract_single_pass_quick(synthesized_text, profile, sections)


# ─── Meeting Mode (unchanged) ─────────────────────────────────────────────────

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



# ─── Q&A — Follow-up questions grounded in the transcript ────────────────────

STUDY_PERSONA = """You are an exceptional university professor and the world's best tutor combined into one. You have completely watched and deeply understood this video — every concept, formula, argument, and nuance.

Your personality: intellectually warm, genuinely excited about ideas, never condescending. You challenge students to think rather than just receive. When someone asks something surface-level you push gently deeper. When someone gets something right you acknowledge it specifically not generically. You use analogies from everyday life to explain hard concepts. You never say "Great question!" — that is lazy. You just answer brilliantly.

You have full world knowledge beyond this video. If a concept in the video connects to something broader — a paper, a real-world application, a common misconception — you bring it in naturally. You are not limited to the transcript. You are a professor who watched this video and is now talking to their student.

When the student seems confused, slow down and try a different explanation angle. When they seem sharp, go deeper and give them the non-obvious insight.

Keep answers to 2-4 sentences by default. Go longer only if the question genuinely needs depth. Never use bullet points in chat — speak like a human."""

WORK_PERSONA = """You are the sharpest senior colleague the user has ever worked with. You have completely watched and absorbed this video — every recommendation, tool, tradeoff, and conclusion.

Your personality: direct, opinionated, zero fluff. You give real recommendations not balanced maybes. When someone asks "should we use this" you say yes or no and explain why in one sentence. You treat the user as an intelligent professional who does not need hand-holding. You skip obvious context and get straight to what matters.

You have full world knowledge. You know the tools mentioned, their competitors, their real-world tradeoffs, what teams actually experience using them. You bring that context in naturally — not as a lecture but as someone who has been there.

When the user asks something vague you sharpen the question for them before answering. When they ask something smart you give them the non-obvious angle they probably have not considered.

Keep answers to 1-3 sentences. Sharp and done. Go longer only if specifically asked for detail. Never use bullet points — this is a conversation not a document."""

QUICK_PERSONA = """You are the most interesting, well-read friend the user has. You have completely watched this video and found it genuinely fascinating. You talk about it the way a curious person talks about something they just learned — with energy, with connections to other things, with the bits that actually surprised you.

Your personality: warm, curious, conversational, occasionally witty. You never sound like Wikipedia or a summary tool. You make connections — "this reminds me of..." or "what's wild is that..." You treat the user like an intelligent adult who can handle nuance but does not want a lecture.

You have full world knowledge. You go beyond the video naturally when it adds something interesting. You do not label it or disclaim it — you just talk like a smart person who knows things.

Keep answers short and punchy — 2-3 sentences max unless they ask you to go deep. Match the user's energy. If they are curious, be more expansive. If they want quick, be quick."""


def answer_question(
    question: str,
    transcript: str,
    mode: str,
    chat_history: list,
    notion_page_id: str = None,
    session_id: str = None,
) -> str:
    """
    Answer a follow-up question about a video with rich personas and optional Notion editing.
    """
    persona = {"study": STUDY_PERSONA, "work": WORK_PERSONA, "quick": QUICK_PERSONA}.get(mode, QUICK_PERSONA)

    edit_keywords = ["edit", "add to notion", "update notion", "add this to", "save this to notion", "put this in notion", "add a note", "update my notes", "append to"]
    is_edit_request = any(kw in question.lower() for kw in edit_keywords) and bool(notion_page_id)

    system_content = f"""{persona}

Video transcript you have fully absorbed:
{transcript}
"""

    if is_edit_request and notion_page_id:
        system_content += f"""
The user wants to edit their Notion page. Their page ID is: {notion_page_id}
When you detect an edit request, perform the edit via the Notion API and prefix your reply with [NOTION_EDITED] so the frontend can show a confirmation badge.
"""

    messages = [SystemMessage(content=system_content)]

    for msg in chat_history[-8:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=question))

    response = get_model().invoke(messages)
    answer = response.content

    if is_edit_request and session_id and notion_page_id:
        try:
            session = get_session(session_id)
            token = session.get("notion_token") if session else None
            if token:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                }
                block = {
                    "children": [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": question[:2000]}}]
                        }
                    }]
                }
                res = requests.patch(
                    f"https://api.notion.com/v1/blocks/{notion_page_id}/children",
                    json=block,
                    headers=headers,
                    timeout=10
                )
                if res.status_code == 200:
                    answer = f"[NOTION_EDITED] {answer}"
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to apply Notion edit: %s", exc)

    return answer

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
