"""
SQL TO RUN IN SUPABASE SQL EDITOR BEFORE USING THIS FEATURE:

CREATE TABLE study_sessions (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  session_id text,
  learning_goal text NOT NULL,
  student_level text NOT NULL
    CHECK (student_level IN ('beginner','some_background','advanced')),
  sources jsonb DEFAULT '[]',
  knowledge_map jsonb,
  tutor_output jsonb,
  qa_history jsonb DEFAULT '[]',
  status text DEFAULT 'building'
    CHECK (status IN ('building','ready','complete')),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own study sessions"
ON study_sessions FOR ALL
USING (auth.uid() = user_id);

CREATE INDEX ON study_sessions(user_id, created_at DESC);

sources jsonb structure — array of objects:
[{
  "source_index": 0,
  "type": "youtube" | "pdf" | "article",
  "title": "string",
  "url_or_filename": "string",
  "extracted_text": "string",
  "extraction_status": "pending"|"done"|"failed"
}]

knowledge_map jsonb structure:
{
  "concepts": [
    {
      "concept_name": "string",
      "best_source_index": 0,
      "best_explanation": "string",
      "supporting_sources": [0, 1],
      "timestamp_or_page": "14:32 or p.7 or empty string"
    }
  ],
  "agreements": ["string"],
  "contradictions": [
    {
      "topic": "string",
      "source_a_index": 0,
      "source_a_says": "string",
      "source_b_index": 1,
      "source_b_says": "string",
      "resolution": "string or null"
    }
  ],
  "knowledge_gaps": ["string"]
}

tutor_output jsonb structure:
{
  "foundation": "string",
  "foundation_source_index": 0,
  "foundation_timestamp_or_page": "string",
  "core_teaching": "string",
  "core_citations": [
    {
      "source_index": 0,
      "timestamp_or_page": "string",
      "quote": "max 20 words"
    }
  ],
  "common_misconceptions": ["string"],
  "knowledge_check": [
    {
      "id": "uuid",
      "question": "string",
      "type": "recall"|"application"|"synthesis",
      "difficulty": "easy"|"medium"|"hard",
      "answered": false,
      "user_answer": null,
      "evaluation": null
    }
  ],
  "next_steps": ["string"]
}

qa_history jsonb structure — array of objects:
[{
  "question_id": "uuid",
  "question_text": "string",
  "user_answer": "string",
  "evaluation": {
    "correct": "true"|"false"|"partial",
    "feedback": "string",
    "misconception": "string or null",
    "correction": "string or null",
    "ready_to_advance": true/false,
    "cited_source_index": 0
  },
  "answered_at": "timestamp"
}]
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.content_ingestion import extract_text_from_pdf, extract_text_from_url
from backend.supabase_client import (
    append_qa_history,
    create_study_session,
    get_session,
    get_study_session,
    update_study_session,
    save_library_item,
)
from gemini import (
    ANSWER_EVALUATION_PROMPT,
    KNOWLEDGE_MAP_PROMPT,
    TUTOR_TEACHING_PROMPT,
    get_model,
)
from models import KnowledgeMap, QuestionEvaluation, TutorOutput
from push_to_notion import (
    _create_page_with_overflow,
    clean_page_id,
    get_headers,
    make_bullet,
    make_callout,
    make_heading,
    make_numbered,
    make_paragraph,
    make_toggle,
)
from youtube_mode import extract_video_id, get_youtube_transcript

logger = logging.getLogger("notionclips.study_session")
router = APIRouter(prefix="/study-session", tags=["study-session"])

ALLOWED_LEVELS = {"beginner", "some_background", "advanced"}
ALLOWED_SOURCE_TYPES = {"youtube", "pdf", "article"}


class StudySessionCreateRequest(BaseModel):
    learning_goal: str
    student_level: str
    sources: List[Dict[str, str]]
    session_id: str
    user_id: Optional[str] = None


class StudySessionBuildRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None


class AnswerRequest(BaseModel):
    question_id: str
    user_answer: str
    session_id: str
    user_id: Optional[str] = None


class PushNotionRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None


class StudySessionChatRequest(BaseModel):
    question: str
    chat_history: List[Dict[str, str]] = []
    session_id: str
    user_id: Optional[str] = None


def _safe_json_load(raw: str) -> Optional[dict]:
    if not raw:
        return None
    text = raw.strip()
    
    # Handle markdown code blocks
    if "```" in text:
        import re
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
        else:
            text = text.strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()
    
    # Identify boundaries for both objects and arrays
    brace_start = text.find("{")
    bracket_start = text.find("[")
    
    # Determine the actual start and end markers
    if brace_start != -1 and (bracket_start == -1 or brace_start < bracket_start):
        start_idx = brace_start
        end_idx = text.rfind("}")
    elif bracket_start != -1:
        start_idx = bracket_start
        end_idx = text.rfind("]")
    else:
        start_idx = -1
        end_idx = -1

    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx+1]

    # Final cleaning: remove any trailing text after the last brace/bracket
    if end_idx != -1:
        text = text[:end_idx+1]

    try:
        return json.loads(text)
    except Exception:
        # Attempt to repair unterminated JSON (common with Gemini)
        try:
            if text.startswith("{") and not text.endswith("}"):
                repaired = text + "}"
                return json.loads(repaired)
            if text.startswith("[") and not text.endswith("]"):
                repaired = text + "]"
                return json.loads(repaired)
        except Exception:
            pass

        # Last ditch: Regex for fields if it's a QuestionEvaluation
        try:
            result = {}
            # Extract "correct": "..."
            match_correct = re.search(r'"correct":\s*"([^"]+)"', text)
            if match_correct:
                result["correct"] = match_correct.group(1)
            
            # Extract "feedback": "..."
            match_feedback = re.search(r'"feedback":\s*"([^"]+)"', text)
            if match_feedback:
                result["feedback"] = match_feedback.group(1)
            
            if "correct" in result and "feedback" in result:
                return result
        except Exception:
            pass

        logger.error(f"JSON parse error: Raw text length: {len(text)}. Snippet: {text[:200]}")
        return None


async def _invoke_with_timeout(llm, prompt: str, timeout_s: int = 30):
    try:
        return await asyncio.wait_for(asyncio.to_thread(llm.invoke, prompt), timeout_s)
    except asyncio.TimeoutError:
        return None


def _ensure_access(session_row: dict, user_id: Optional[str]):
    stored_user_id = (session_row or {}).get("user_id")
    if stored_user_id:
        if not user_id or user_id != stored_user_id:
            raise HTTPException(status_code=403, detail="Forbidden")


def _default_knowledge_map() -> dict:
    return {
        "concepts": [],
        "agreements": [],
        "contradictions": [],
        "knowledge_gaps": ["Insufficient data to build a knowledge map."],
    }


def _default_tutor_output(learning_goal: str) -> dict:
    return {
        "foundation": learning_goal[:200],
        "foundation_source_index": 0,
        "foundation_timestamp_or_page": "",
        "core_teaching": "We could not assemble a full teaching plan yet.",
        "core_citations": [],
        "common_misconceptions": [],
        "knowledge_check": [],
        "next_steps": [],
    }


def _format_sources_for_prompt(sources: List[dict]) -> str:
    lines = []
    for source in sources:
        idx = source.get("source_index")
        s_type = source.get("type")
        title = source.get("title") or source.get("url_or_filename") or "Untitled"
        text = source.get("extracted_text") or ""
        lines.append(f'SOURCE {idx} [{s_type}] "{title}": {text}')
    return "\n".join(lines)


def _score_concept(question: str, concept: dict) -> int:
    q_tokens = set(question.lower().split())
    name = str(concept.get("concept_name") or "").lower().split()
    return sum(1 for tok in name if tok in q_tokens)


def _find_excerpt(text: str, phrase: str, window_words: int = 500) -> str:
    words = text.split()
    if not words:
        return ""
    joined = " ".join(words).lower()
    idx = joined.find(phrase.lower())
    if idx == -1:
        return " ".join(words[:window_words])
    before = max(0, joined[:idx].count(" ") - 50)
    after = min(len(words), before + window_words)
    return " ".join(words[before:after])


@router.post("/create")
async def create_session(payload: StudySessionCreateRequest):
    learning_goal = payload.learning_goal.strip()
    if len(learning_goal) < 10:
        raise HTTPException(status_code=400, detail="learning_goal must be at least 10 characters")
    if payload.student_level not in ALLOWED_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid student_level")
    if not payload.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    if not (2 <= len(payload.sources) <= 4):
        raise HTTPException(status_code=400, detail="Sources must be between 2 and 4")

    sources = []
    for idx, src in enumerate(payload.sources):
        s_type = (src.get("type") or "").strip().lower()
        url = (src.get("url") or "").strip()
        if s_type not in ALLOWED_SOURCE_TYPES:
            raise HTTPException(status_code=400, detail="Invalid source type")
        if not url:
            raise HTTPException(status_code=400, detail="Source url is required")
        sources.append({
            "source_index": idx,
            "type": s_type,
            "title": "",
            "url_or_filename": url,
            "extracted_text": "",
            "extraction_status": "pending",
        })

    study_session_id = create_study_session(
        user_id=payload.user_id,
        session_id=payload.session_id,
        learning_goal=learning_goal,
        student_level=payload.student_level,
        sources=sources,
    )
    return {"study_session_id": study_session_id, "status": "building"}


@router.post("/{study_session_id}/add-pdf")
async def add_pdf(study_session_id: str, file: UploadFile = File(...)):
    session = get_study_session(study_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail={"error": "file_too_large", "message": "PDF must be under 10MB"},
        )

    try:
        title, text = await asyncio.to_thread(extract_text_from_pdf, file_bytes)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={"error": "pdf_unreadable", "message": "Could not read this PDF. Try a text-based PDF."},
        )
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": "pdf_unreadable", "message": "Could not read this PDF. Try a text-based PDF."},
        )

    sources = list(session.get("sources") or [])
    pending_index = None
    if file.filename:
        for idx, source in enumerate(sources):
            if source.get("type") != "pdf":
                continue
            if source.get("extraction_status") != "pending":
                continue
            if source.get("url_or_filename") == file.filename:
                pending_index = idx
                break
    if pending_index is None:
        for idx, source in enumerate(sources):
            if source.get("type") != "pdf":
                continue
            if source.get("extraction_status") != "pending":
                continue
            pending_index = idx
            break

    if pending_index is None:
        source_index = len(sources)
        sources.append({
            "source_index": source_index,
            "type": "pdf",
            "title": title,
            "url_or_filename": file.filename or "document.pdf",
            "extracted_text": text,
            "extraction_status": "done",
        })
    else:
        existing = dict(sources[pending_index] or {})
        source_index = existing.get("source_index")
        if source_index is None:
            source_index = pending_index
        sources[pending_index] = {
            **existing,
            "source_index": source_index,
            "type": "pdf",
            "title": title,
            "url_or_filename": file.filename or existing.get("url_or_filename") or "document.pdf",
            "extracted_text": text,
            "extraction_status": "done",
        }
    update_study_session(study_session_id, {"sources": sources})

    return {"source_index": source_index, "title": title, "status": "added"}


@router.post("/{study_session_id}/build")
async def build_session(study_session_id: str, payload: StudySessionBuildRequest):
    logger.info(f"--- BUILDING SESSION {study_session_id} ---")
    session = get_study_session(study_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    _ensure_access(session, payload.user_id)

    sources = list(session.get("sources") or [])
    if len(sources) < 2:
        raise HTTPException(status_code=400, detail="At least two sources are required")

    async def process_source(source: dict) -> dict:
        s = dict(source)
        s_type = s.get("type")
        url = s.get("url_or_filename", "")
        if s_type == "pdf":
            if s.get("extracted_text"):
                s["extraction_status"] = "done"
            else:
                s["extraction_status"] = "failed"
            return s
        if s_type == "article":
            try:
                title, text = await asyncio.to_thread(extract_text_from_url, url)
                s["title"] = title
                s["extracted_text"] = text
                s["extraction_status"] = "done"
            except Exception:
                s["extraction_status"] = "failed"
            return s
        if s_type == "youtube":
            try:
                vid = extract_video_id(url)
                if not vid:
                    raise ValueError("Invalid YouTube URL")
                transcript, _ = await asyncio.to_thread(get_youtube_transcript, vid)
                s["title"] = s.get("title") or vid
                s["extracted_text"] = transcript
                s["extraction_status"] = "done"
            except Exception:
                s["extraction_status"] = "failed"
            return s
        s["extraction_status"] = "failed"
        return s

    sources = await asyncio.gather(*(process_source(s) for s in sources))
    update_study_session(study_session_id, {"sources": sources})

    successful_sources = [s for s in sources if s.get("extraction_status") == "done"]
    if len(successful_sources) < 2:
        try:
            update_study_session(study_session_id, {"status": "complete"})
        except Exception:
            logger.warning("Failed to mark session as failed")
        raise HTTPException(
            status_code=422,
            detail="Not enough sources could be processed to build a session",
        )

    source_list = _format_sources_for_prompt(successful_sources)
    
    # Bug 1 Fix: Explicitly log source lengths
    logger.info(f"Building knowledge map with sources: {[{'idx': s.get('source_index'), 'len': len(s.get('extracted_text', ''))} for s in successful_sources]}")
    for s in successful_sources:
        logger.info(f"Source {s.get('source_index')} preview: {s.get('extracted_text', '')[:200]}")

    llm = get_model()
    km_prompt = KNOWLEDGE_MAP_PROMPT.format(
        learning_goal=session.get("learning_goal", ""),
        student_level=session.get("student_level", ""),
        n=len(successful_sources),
        source_list=source_list,
    )
    km_response = await _invoke_with_timeout(llm, km_prompt, 120)
    km_data = None
    if not km_response:
        try:
            update_study_session(study_session_id, {"status": "complete"})
        except Exception:
            logger.warning("Failed to mark session as failed")
        raise HTTPException(status_code=500, detail={"error": "knowledge_map_failed", "message": "Failed to build knowledge map due to timeout or missing response."})
    km_raw = km_response.content if km_response else ""
    km_data = _safe_json_load(km_raw)
    
    if not km_data:
        logger.error(f"Failed to parse Knowledge Map JSON. Raw response: {km_raw[:500]}...")
        update_study_session(study_session_id, {"status": "complete"})
        raise HTTPException(status_code=500, detail={"error": "knowledge_map_failed", "message": "Knowledge map was empty or invalid JSON."})
    
    try:
        km_obj = KnowledgeMap(**km_data)
        knowledge_map = km_obj.model_dump()
    except Exception as e:
        logger.error(f"Pydantic Validation Error for Knowledge Map: {e}. Data: {km_data}")
        update_study_session(study_session_id, {"status": "complete"})
        raise HTTPException(status_code=500, detail={"error": "knowledge_map_failed", "message": f"Validation error: {str(e)}"})

    tutor_prompt = TUTOR_TEACHING_PROMPT.format(
        learning_goal=session.get("learning_goal", ""),
        student_level=session.get("student_level", ""),
        knowledge_map_json=json.dumps(knowledge_map, ensure_ascii=False),
        source_list=source_list,
    )
    
    # Bug 2 Fix: Wrap tutor output in try/except
    try:
        tutor_data = None
        tutor_response = await _invoke_with_timeout(llm, tutor_prompt, 120)
        if not tutor_response:
            raise ValueError("Timeout or empty response from LLM")
            
        tutor_raw = tutor_response.content
        tutor_data = _safe_json_load(tutor_raw)
        if not tutor_data:
            raise ValueError("Failed to parse tutor output JSON")
            
        tutor_obj = TutorOutput(**tutor_data)
        tutor_output = tutor_obj.model_dump()
    except Exception as e:
        logger.error(f"Tutor output validation failed: {e}. Data: {tutor_data}")
        update_study_session(study_session_id, {"status": "complete"})
        raise HTTPException(status_code=500, detail={"error": "tutor_output_failed", "message": f"Teaching plan validation failed: {str(e)}"})

    # Ensure knowledge_check questions have UUIDs
    seen_ids = set()
    for question in tutor_output.get("knowledge_check", []):
        qid = question.get("id") or str(uuid.uuid4())
        while qid in seen_ids:
            qid = str(uuid.uuid4())
        question["id"] = qid
        seen_ids.add(qid)

    update_study_session(
        study_session_id,
        {"knowledge_map": knowledge_map, "tutor_output": tutor_output, "status": "ready"},
    )
    
    # Save to unified library
    try:
        learning_goal = session.get("learning_goal", "Unknown learning goal")
        foundation = tutor_output.get("foundation", "")
        user_id = session.get("user_id")
        session_id_val = session.get("session_id", "")
        
        # Get notion_page_id if exists
        notion_page_id = session.get("notion_page_id")
        
        save_library_item(
            session_id=session_id_val,
            user_id=user_id,
            content_type="study_session",
            title=f"Learning: {learning_goal}",
            summary=foundation,
            content_data={
                "learning_goal": learning_goal,
                "student_level": session.get("student_level"),
                "concepts": knowledge_map.get("concepts", []),
                "knowledge_map": knowledge_map,
                "tutor_output": tutor_output,
                "sources": [
                    {"source_index": s.get("source_index"), "title": s.get("title"), "type": s.get("type")}
                    for s in sources
                ],
            },
            notion_page_id=notion_page_id,
        )
        logger.info(f"Saved study session to library: {learning_goal}")
    except Exception as exc:
        logger.warning(f"Failed to save study session to library: {exc}")

    return {
        "study_session_id": study_session_id,
        "status": "ready",
        "knowledge_map": knowledge_map,
        "tutor_output": tutor_output,
        "sources": [
            {"source_index": s.get("source_index"), "title": s.get("title"), "type": s.get("type")}
            for s in sources
        ],
    }


@router.get("/{study_session_id}")
async def get_session_status(study_session_id: str, user_id: Optional[str] = None):
    session = get_study_session(study_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    _ensure_access(session, user_id)
    return session


@router.post("/{study_session_id}/answer")
async def submit_answer(study_session_id: str, payload: AnswerRequest):
    session = get_study_session(study_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    _ensure_access(session, payload.user_id)

    tutor_output = session.get("tutor_output") or {}
    knowledge_map = session.get("knowledge_map") or {}
    questions = list(tutor_output.get("knowledge_check") or [])
    sources = list(session.get("sources") or [])

    target = next((q for q in questions if q.get("id") == payload.question_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Question not found")

    concepts = knowledge_map.get("concepts") or []
    best_concept = max(concepts, key=lambda c: _score_concept(target.get("question", ""), c), default=None)
    source_index = (best_concept or {}).get("best_source_index", 0)
    source = next((s for s in sources if s.get("source_index") == source_index), None) or {}
    source_text = source.get("extracted_text") or ""
    excerpt = _find_excerpt(source_text, (best_concept or {}).get("concept_name", ""), 500)

    eval_prompt = ANSWER_EVALUATION_PROMPT.format(
        learning_goal=session.get("learning_goal", ""),
        difficulty=target.get("difficulty", ""),
        type=target.get("type", ""),
        question=target.get("question", ""),
        user_answer=payload.user_answer,
        relevant_source_content=excerpt,
    )
    eval_llm = get_model()
    eval_response = await _invoke_with_timeout(eval_llm, eval_prompt, 30)
    eval_raw = eval_response.content if eval_response else ""
    eval_data = _safe_json_load(eval_raw)
    if not eval_data:
        eval_data = {
            "correct": "partial",
            "feedback": "We could not fully evaluate this answer yet.",
            "misconception": None,
            "correction": None,
            "ready_to_advance": False,
            "cited_source_index": source_index,
        }
    try:
        evaluation = QuestionEvaluation(**eval_data).dict()
    except Exception:
        evaluation = {
            "correct": "partial",
            "feedback": "We could not fully evaluate this answer yet.",
            "misconception": None,
            "correction": None,
            "ready_to_advance": False,
            "cited_source_index": source_index,
        }

    for question in questions:
        if question.get("id") == payload.question_id:
            question["answered"] = True
            question["user_answer"] = payload.user_answer
            question["evaluation"] = evaluation

    tutor_output["knowledge_check"] = questions
    update_study_session(study_session_id, {"tutor_output": tutor_output})

    qa_entry = {
        "question_id": payload.question_id,
        "question_text": target.get("question"),
        "user_answer": payload.user_answer,
        "evaluation": evaluation,
        "answered_at": datetime.now(timezone.utc).isoformat(),
    }
    append_qa_history(study_session_id, qa_entry)

    return {"evaluation": evaluation, "question_id": payload.question_id, "session_updated": True}


@router.post("/{study_session_id}/push-notion")
async def push_session_to_notion(study_session_id: str, payload: PushNotionRequest):
    session = get_study_session(study_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    _ensure_access(session, payload.user_id)

    session_row = get_session(payload.session_id)
    token = (session_row or {}).get("notion_token")
    page_id = (
        (session_row or {}).get("study_page_id")
        or (session_row or {}).get("notion_page_id")
        or os.getenv("NOTION_PAGE_ID")
    )
    if not token or not page_id:
        raise HTTPException(status_code=400, detail="Notion credentials are required")

    knowledge_map = session.get("knowledge_map") or {}
    tutor_output = session.get("tutor_output") or {}
    sources = session.get("sources") or []

    def _source_title(idx: int) -> str:
        source = next((s for s in sources if s.get("source_index") == idx), None) or {}
        return source.get("title") or source.get("url_or_filename") or f"Source {idx}"

    blocks = [
        make_callout(session.get("learning_goal", ""), "🎯", "blue_background"),
        make_heading("Foundation"),
        make_paragraph(tutor_output.get("foundation", "")),
        make_paragraph(
            f"Best explained in: {_source_title(tutor_output.get('foundation_source_index', 0))} "
            f"at {tutor_output.get('foundation_timestamp_or_page', '')}",
            italic=True,
            color="gray",
        ),
        make_heading("Core Teaching"),
        make_paragraph(tutor_output.get("core_teaching", "")),
        make_heading("Sources Used"),
    ]

    for citation in tutor_output.get("core_citations", []):
        title = _source_title(citation.get("source_index", 0))
        blocks.append(
            make_bullet(
                f"{title} [{citation.get('timestamp_or_page', '')}] — {citation.get('quote', '')}"
            )
        )

    blocks.append(make_heading("Where Sources Agree"))
    for item in knowledge_map.get("agreements", []):
        blocks.append(make_bullet(item))

    contradictions = knowledge_map.get("contradictions") or []
    if contradictions:
        blocks.append(make_heading("⚠️ Where Sources Disagree"))
        for c in contradictions:
            blocks.append(
                make_callout(
                    f"{c.get('topic', '')}: {_source_title(c.get('source_a_index', 0))} says {c.get('source_a_says', '')} "
                    f"while {_source_title(c.get('source_b_index', 0))} says {c.get('source_b_says', '')}",
                    "⚠️",
                    "yellow_background",
                )
            )

    blocks.append(make_heading("Common Misconceptions"))
    for item in tutor_output.get("common_misconceptions", []):
        blocks.append(make_bullet(item))

    blocks.append(make_heading("Knowledge Check"))
    for q in tutor_output.get("knowledge_check", []):
        if q.get("answered"):
            answer = q.get("user_answer", "")
            evaluation = (q.get("evaluation") or {}).get("feedback", "")
            misconception = (q.get("evaluation") or {}).get("misconception")
            correction = (q.get("evaluation") or {}).get("correction")
            children = [
                make_paragraph(f"Your answer: {answer}"),
                make_paragraph(f"Evaluation: {evaluation}"),
            ]
            if misconception:
                children.append(make_paragraph(f"⚠️ Misconception: {misconception}"))
            if correction:
                children.append(make_paragraph(f"✓ Correction: {correction}"))
            blocks.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": q.get("question", "")[:2000]}}],
                    "children": children,
                },
            })
        else:
            blocks.append(make_toggle(q.get("question", ""), "Not yet answered"))

    blocks.append(make_heading("Knowledge Gaps"))
    for gap in knowledge_map.get("knowledge_gaps", []):
        blocks.append(make_bullet(gap))

    blocks.append(make_heading("Next Steps"))
    for step in tutor_output.get("next_steps", []):
        blocks.append(make_numbered(step))

    payload = {
        "parent": {"type": "page_id", "page_id": clean_page_id(page_id)},
        "icon": {"type": "emoji", "emoji": "🎓"},
        "properties": {
            "title": {"title": [{"text": {"content": f"🎓 Study Session — {session.get('learning_goal', '')[:60]}"}}]}
        },
        "children": blocks[:90],
    }
    page_id = _create_page_with_overflow(page_id, payload, blocks[90:], token)
    notion_url = f"https://www.notion.so/{clean_page_id(page_id)}"
    return {"status": "ok", "notion_url": notion_url}


@router.post("/{study_session_id}/chat")
async def study_session_chat(study_session_id: str, payload: StudySessionChatRequest):
    session = get_study_session(study_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")
    _ensure_access(session, payload.user_id)

    sources = session.get("sources") or []
    successful_sources = [s for s in sources if s.get("extraction_status") == "done"]
    if not successful_sources:
        raise HTTPException(status_code=400, detail="No processed sources found for chat.")

    # Combine transcripts for context
    context = _format_sources_for_prompt(successful_sources)
    learning_goal = session.get("learning_goal", "")

    prompt = f"""You are an expert tutor helping a student with their learning goal: "{learning_goal}".
You have several sources provided below. Answer the student's question accurately based on these sources.
If the sources contradict, explain the different viewpoints.
If the answer isn't in the sources, say you don't know based on these specific materials.

SOURCES:
{context}

CHAT HISTORY:
{json.dumps(payload.chat_history, ensure_ascii=False)}

STUDENT QUESTION: {payload.question}
ANSWER:"""

    llm = get_model()
    try:
        response = await asyncio.to_thread(llm.invoke, prompt)
        answer = response.content
    except Exception as e:
        logger.exception("Study session chat failed")
        raise HTTPException(status_code=502, detail=str(e))

    return {"answer": answer}

