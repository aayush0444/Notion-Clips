"""
SQL to run in Supabase SQL editor:

CREATE TABLE smart_watch_analyses (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  session_id text,
  video_id text NOT NULL,
  video_url text NOT NULL,
  video_title text,
  user_question text NOT NULL,
  verdict text CHECK (verdict IN ('watch', 'skim', 'skip')),
  confidence float,
  reason text,
  estimated_timestamp_range text,
  relevant_moments jsonb DEFAULT '[]',
  stage1_ms integer,
  stage2_ms integer,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE smart_watch_analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own analyses" ON smart_watch_analyses
FOR ALL USING (auth.uid() = user_id);
CREATE INDEX ON smart_watch_analyses(user_id, created_at DESC);
CREATE INDEX ON smart_watch_analyses(video_id);
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.supabase_client import (
    get_cached_transcript,
    list_smart_watch_analyses,
    list_analytics_events,
    get_session,
    save_cached_transcript,
    save_smart_watch_analysis,
    track_analytics_event,
)
from youtube_mode import extract_video_id, get_youtube_transcript

logger = logging.getLogger("notionclips.smart_watch")
router = APIRouter(prefix="/smart-watch", tags=["smart-watch"])

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-4o-mini"
GEMINI_MODEL = "gemini-2.0-flash"
PROMPT_VERSION = "smart-watch-v1"
QUICK_CHECK_WORD_BUDGET = 700


class SmartWatchQuickRequest(BaseModel):
    video_url: str
    user_question: str
    session_id: str
    transcript: Optional[str] = None


class SmartWatchQuickResult(BaseModel):
    verdict: str
    confidence: float
    reason: str
    estimated_timestamp_range: Optional[str]
    video_id: str
    cache_hit: bool
    stage1_ms: int
    prompt_version: str = PROMPT_VERSION


class SmartWatchDeepRequest(BaseModel):
    video_id: str
    user_question: str
    session_id: str
    verdict: str = "watch"


class SmartWatchMoment(BaseModel):
    timestamp_seconds: int
    timestamp_display: str
    quote: str
    relevance: str
    youtube_url: str


class SmartWatchDeepResult(BaseModel):
    relevant_moments: List[SmartWatchMoment]
    total_relevant_moments: int
    analysis_complete: bool
    stage2_ms: int
    skipped: Optional[bool] = None
    reason: Optional[str] = None
    prompt_version: str = PROMPT_VERSION


class SmartWatchHistoryRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    limit: int = 30
    mode: Optional[str] = None


class SmartWatchHistoryItem(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    video_id: str
    video_url: str
    video_title: Optional[str] = None
    user_question: str
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None
    estimated_timestamp_range: Optional[str] = None
    relevant_moments: List[Dict[str, Any]] = Field(default_factory=list)
    stage1_ms: Optional[int] = None
    stage2_ms: Optional[int] = None


class SmartWatchHistoryResponse(BaseModel):
    items: List[SmartWatchHistoryItem]


class SmartWatchAnalyticsRequest(BaseModel):
    session_id: str
    event_name: str
    user_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class SmartWatchDashboardRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None


class SmartWatchDashboardResponse(BaseModel):
    total_analyses: int
    watch_count: int
    skim_count: int
    skip_count: int
    avg_confidence: float
    timestamp_clicks: int
    timestamps_generated: int
    avg_stage1_ms: int
    avg_stage2_ms: int
    estimated_time_saved_minutes: float


class SearchResultVideoMeta(BaseModel):
    video_id: str
    title: str
    channel_name: Optional[str] = None
    duration: Optional[str] = None


class SearchResultVerdictRequest(BaseModel):
    search_query: str
    videos: List[SearchResultVideoMeta] = Field(default_factory=list)


class SearchResultVerdictItem(BaseModel):
    video_id: str
    verdict: str
    reason: str
    confidence: float = 0.5


class SearchResultVerdictResponse(BaseModel):
    items: List[SearchResultVerdictItem]
    stage_ms: int
    prompt_version: str = PROMPT_VERSION


def _safe_stage1_default(video_id: str, stage1_ms: int = 0) -> Dict[str, Any]:
    return {
        "verdict": "skim",
        "confidence": 0.5,
        "reason": "Analysis unavailable",
        "estimated_timestamp_range": None,
        "video_id": video_id,
        "cache_hit": False,
        "stage1_ms": stage1_ms,
    }


def _normalize_search_verdict(value: str) -> str:
    verdict = str(value or "").strip().lower()
    if verdict in {"watch", "skim", "skip"}:
        return verdict
    return "skim"


def _metadata_heuristic_verdict(search_query: str, video: Dict[str, Any]) -> Dict[str, Any]:
    query_tokens = {t for t in re.split(r"\W+", search_query.lower()) if len(t) > 2}
    title = str(video.get("title") or "").lower()
    channel = str(video.get("channel_name") or "").lower()
    haystack = f"{title} {channel}"
    overlap = sum(1 for token in query_tokens if token in haystack)
    if overlap >= 3:
        return {
            "verdict": "watch",
            "confidence": 0.75,
            "reason": "Title and channel strongly match your search intent.",
        }
    if overlap >= 1:
        return {
            "verdict": "skim",
            "confidence": 0.58,
            "reason": "Partially relevant by title keywords; verify focus before deep watching.",
        }
    return {
        "verdict": "skip",
        "confidence": 0.42,
        "reason": "Metadata appears weakly related to your search intent.",
    }


async def _run_search_result_batch_verdict(
    search_query: str,
    videos: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return [
            {
                "video_id": str(v.get("video_id") or ""),
                **_metadata_heuristic_verdict(search_query, v),
            }
            for v in videos
        ]

    system_prompt = """
You are ranking YouTube search results for learning relevance.
Given one search query (user intent) and up to 8 candidate videos with metadata,
return a verdict for each candidate.

Rules:
- Use ONLY metadata (title, channel, duration).
- Return exactly one of: watch, skim, skip.
- watch: highly relevant and likely worth full viewing.
- skim: somewhat relevant, probably selective viewing.
- skip: weakly relevant or off-intent.
- reason must be one short sentence.

Return ONLY valid JSON in this exact shape:
{
  "items": [
    {"video_id": "...", "verdict": "watch|skim|skip", "confidence": 0.0, "reason": "..."}
  ]
}
"""

    user_payload = {
        "search_query": search_query,
        "videos": videos,
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = _clean_json(content)
            raw_items = parsed.get("items") or []
            if not isinstance(raw_items, list):
                raise ValueError("Invalid items payload")

            by_id = {str(v.get("video_id") or ""): v for v in videos}
            out: List[Dict[str, Any]] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                video_id = str(item.get("video_id") or "").strip()
                if not video_id or video_id not in by_id:
                    continue
                confidence = float(item.get("confidence", 0.5))
                confidence = max(0.0, min(1.0, confidence))
                reason = str(item.get("reason") or "Metadata relevance estimate.").strip()
                if not reason:
                    reason = "Metadata relevance estimate."
                out.append(
                    {
                        "video_id": video_id,
                        "verdict": _normalize_search_verdict(item.get("verdict")),
                        "confidence": confidence,
                        "reason": reason[:180],
                    }
                )

            if not out:
                raise ValueError("No usable verdicts")

            seen = {o["video_id"] for o in out}
            for video in videos:
                video_id = str(video.get("video_id") or "")
                if not video_id or video_id in seen:
                    continue
                out.append({"video_id": video_id, **_metadata_heuristic_verdict(search_query, video)})

            return out
    except Exception as exc:
        logger.warning("Search result batch verdict failed, using heuristic fallback: %s", exc)
        return [
            {
                "video_id": str(v.get("video_id") or ""),
                **_metadata_heuristic_verdict(search_query, v),
            }
            for v in videos
        ]


def _clean_json(raw: str) -> Dict[str, Any]:
    content = raw.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).strip()
        content = re.sub(r"```$", "", content).strip()
    return json.loads(content)


def _extract_timestamped_sentences(transcript: str) -> List[Dict[str, Any]]:
    parts = re.split(r"(\[\d{2}:\d{2}\])", transcript)
    current_ts = 0
    out: List[Dict[str, Any]] = []

    for part in parts:
        if not part:
            continue
        marker = re.match(r"\[(\d{2}):(\d{2})\]", part)
        if marker:
            current_ts = int(marker.group(1)) * 60 + int(marker.group(2))
            continue

        for sentence in re.split(r"(?<=[.!?])\s+", part.strip()):
            clean = sentence.strip()
            if clean:
                out.append({"text": clean, "timestamp_seconds": current_ts})
    return out


def _format_mmss(seconds: int) -> str:
    m = max(0, seconds) // 60
    s = max(0, seconds) % 60
    return f"{m:02d}:{s:02d}"


def _first_quarter_text(transcript: str) -> str:
    timestamped = _extract_timestamped_sentences(transcript)
    if timestamped:
        end = max(1, int(len(timestamped) * 0.25))
        opening = timestamped[:end]
        lines = []
        for item in opening:
            ts = _format_mmss(int(item.get("timestamp_seconds", 0)))
            text = str(item.get("text", "")).strip()
            if text:
                lines.append(f"[{ts}] {text}")
        return "\n".join(lines)

    tokens = transcript.split()
    if not tokens:
        return ""
    end = max(1, int(len(tokens) * 0.25))
    return " ".join(tokens[:end])


def _fixed_budget_excerpt(transcript: str, word_budget: int = QUICK_CHECK_WORD_BUDGET) -> str:
    tokens = transcript.split()
    if not tokens:
        return ""
    safe_budget = max(600, min(800, int(word_budget)))
    return " ".join(tokens[:safe_budget])


async def _run_stage1_quick_check(
    user_question: str,
    video_title: str,
    transcript_opening: str,
    excerpt_label: str = "Transcript excerpt",
) -> Dict[str, Any]:
    system_prompt = """
You are a precise content analyst. You will be given the opening portion
of a YouTube video transcript and a user's learning question.

Your job is to determine:
1. Does this video likely address the user's question?
2. What is your confidence level?
3. Based on the opening, where do you estimate the answer appears?

You must respond ONLY in this exact JSON format with no other text:
{
  "verdict": "watch" | "skim" | "skip",
  "confidence": 0.0 to 1.0,
  "reason": "one sentence max — why this verdict",
  "estimated_timestamp_range": "e.g. 10:00-20:00 or null if skip"
}

Verdict definitions:
- watch: High confidence (>0.7) the video directly answers the question
- skim: Medium confidence (0.4-0.7), partial answer or tangentially related
- skip: Low confidence (<0.4), video unlikely to answer the question

Be strict. Do not give "watch" unless you are genuinely confident.
"""

    user_prompt = f"""
User question: {user_question}
Video title: {video_title}
{excerpt_label}:
{transcript_opening}
"""

    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return {"verdict": "skim", "confidence": 0.5, "reason": "Analysis unavailable", "estimated_timestamp_range": None}

    payload = {
        "model": OPENROUTER_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = _clean_json(content)
            verdict = str(parsed.get("verdict", "skim")).lower()
            if verdict not in {"watch", "skim", "skip"}:
                verdict = "skim"
            confidence = float(parsed.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))
            reason = str(parsed.get("reason", "Analysis unavailable")).strip() or "Analysis unavailable"
            ts_range = parsed.get("estimated_timestamp_range")
            ts_range = str(ts_range).strip() if isinstance(ts_range, str) and ts_range.strip() else None
            return {
                "verdict": verdict,
                "confidence": confidence,
                "reason": reason,
                "estimated_timestamp_range": ts_range,
            }
    except Exception as exc:
        logger.warning("Stage 1 quick-check failed: %s", exc)
        return {"verdict": "skim", "confidence": 0.5, "reason": "Analysis unavailable", "estimated_timestamp_range": None}


def _chunk_by_sentences(items: List[Dict[str, Any]], chunk_size: int = 30) -> List[List[Dict[str, Any]]]:
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def _format_chunk_with_timestamps(chunk: List[Dict[str, Any]]) -> str:
    lines = []
    for item in chunk:
        ts = _format_mmss(int(item.get("timestamp_seconds", 0)))
        text = str(item.get("text", "")).strip()
        if text:
            lines.append(f"[{ts}] {text}")
    return "\n".join(lines)


async def _analyze_chunk_with_gemini(user_question: str, chunk_text: str) -> List[Dict[str, Any]]:
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not key:
        return []

    system_prompt = """
You are a precise timestamp extractor. Given a portion of a YouTube
video transcript with timestamps and a user's question, identify
ONLY the moments where the video directly addresses the question.

Be extremely precise and conservative. Only return timestamps where
the answer is genuinely present — not where the topic is mentioned
in passing.

Respond ONLY in this exact JSON format:
{
  "relevant_moments": [
    {
      "timestamp_seconds": 842,
      "timestamp_display": "14:02",
      "quote": "exact 10-15 word quote from transcript at this moment",
      "relevance": "one sentence: exactly what question aspect this addresses"
    }
  ]
}

Return empty array if this chunk does not address the question.
"""
    user_prompt = f"""
User question: {user_question}

Transcript chunk (with timestamps):
{chunk_text}
"""
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0},
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = _clean_json(text)
            moments = parsed.get("relevant_moments") or []
            if not isinstance(moments, list):
                return []
            cleaned: List[Dict[str, Any]] = []
            for m in moments:
                if not isinstance(m, dict):
                    continue
                seconds = int(m.get("timestamp_seconds", 0))
                cleaned.append(
                    {
                        "timestamp_seconds": max(0, seconds),
                        "timestamp_display": str(m.get("timestamp_display", _format_mmss(seconds))),
                        "quote": str(m.get("quote", "")).strip(),
                        "relevance": str(m.get("relevance", "")).strip(),
                    }
                )
            return cleaned
    except Exception as exc:
        logger.warning("Stage 2 chunk analysis failed: %s", exc)
        return []


def _dedupe_and_rank(moments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not moments:
        return []
    ranked = sorted(moments, key=lambda x: int(x.get("timestamp_seconds", 0)))
    merged: List[Dict[str, Any]] = []
    for moment in ranked:
        ts = int(moment.get("timestamp_seconds", 0))
        if not merged:
            merged.append(moment)
            continue
        prev = merged[-1]
        prev_ts = int(prev.get("timestamp_seconds", 0))
        if abs(ts - prev_ts) <= 30:
            prev_score = len(str(prev.get("quote", ""))) + len(str(prev.get("relevance", "")))
            cur_score = len(str(moment.get("quote", ""))) + len(str(moment.get("relevance", "")))
            if cur_score > prev_score:
                merged[-1] = moment
        else:
            merged.append(moment)
    return merged[:5]


@router.post("/quick-check", response_model=SmartWatchQuickResult)
async def smart_watch_quick_check(payload: SmartWatchQuickRequest):
    stage1_start = time.perf_counter()
    video_url = payload.video_url.strip()
    question = payload.user_question.strip()
    if not video_url or not question:
        return JSONResponse(status_code=400, content={"error": "invalid_input", "message": "video_url and user_question are required"})

    video_id = extract_video_id(video_url)
    if not video_id:
        return JSONResponse(status_code=400, content={"error": "invalid_video_url", "message": "Could not extract video id"})

    cache_hit = False
    transcript: Optional[str] = (payload.transcript or "").strip() or None
    direct_transcript = bool(transcript)
    duration_minutes: float = 0.0

    if not transcript:
        try:
            cached = get_cached_transcript(video_id)
        except Exception as exc:
            logger.warning("Smart Watch cache read failed: %s", exc)
            cached = None

        if cached and cached.get("transcript"):
            transcript = str(cached.get("transcript", "")).strip()
            cache_hit = bool(transcript)
            try:
                duration_minutes = float(cached.get("duration_minutes") or 0.0)
            except (TypeError, ValueError):
                duration_minutes = 0.0

    if not transcript:
        try:
            transcript, duration_minutes = get_youtube_transcript(video_id)
        except Exception:
            return JSONResponse(
                status_code=422,
                content={"error": "transcript_unavailable", "message": "Could not fetch transcript for this video"},
            )
        try:
            save_cached_transcript(video_id, transcript, duration_minutes)
        except Exception as exc:
            logger.warning("Smart Watch transcript cache write failed: %s", exc)

    if direct_transcript:
        opening = _fixed_budget_excerpt(transcript, QUICK_CHECK_WORD_BUDGET)
        excerpt_label = "Transcript opening (fixed 700-word budget from extension)"
    else:
        opening = _first_quarter_text(transcript)
        excerpt_label = "Transcript opening (first 25%)"

    video_title = video_id
    stage1 = await _run_stage1_quick_check(question, video_title, opening, excerpt_label=excerpt_label)
    stage1_ms = int((time.perf_counter() - stage1_start) * 1000)
    out = _safe_stage1_default(video_id=video_id, stage1_ms=stage1_ms)
    out.update(stage1)
    out["video_id"] = video_id
    out["cache_hit"] = cache_hit
    out["stage1_ms"] = stage1_ms
    out["prompt_version"] = PROMPT_VERSION

    user_id = None
    try:
        session = get_session(payload.session_id)
        user_id = (session or {}).get("user_id")
    except Exception:
        user_id = None
    try:
        save_smart_watch_analysis(
            session_id=payload.session_id,
            video_id=video_id,
            video_url=video_url,
            user_question=question,
            verdict=out["verdict"],
            confidence=out["confidence"],
            reason=out["reason"],
            user_id=user_id,
            video_title=video_title,
            estimated_timestamp_range=out["estimated_timestamp_range"],
            relevant_moments=[],
            stage1_ms=stage1_ms,
        )
    except Exception as exc:
        logger.warning("Failed saving Smart Watch quick analysis: %s", exc)
    try:
        track_analytics_event(
            session_id=payload.session_id,
            user_id=user_id,
            event_name="smart_watch_quick_check",
            payload={
                "video_id": video_id,
                "verdict": out["verdict"],
                "confidence": out["confidence"],
                "cache_hit": cache_hit,
                "stage1_ms": stage1_ms,
                "prompt_version": PROMPT_VERSION,
            },
        )
    except Exception as exc:
        logger.warning("Failed tracking quick-check analytics: %s", exc)

    return SmartWatchQuickResult(**out)


@router.post("/search-verdicts", response_model=SearchResultVerdictResponse)
async def smart_watch_search_verdicts(payload: SearchResultVerdictRequest):
    stage_start = time.perf_counter()
    search_query = (payload.search_query or "").strip()
    if not search_query:
        return JSONResponse(status_code=400, content={"error": "invalid_input", "message": "search_query is required"})

    source_videos = payload.videos[:8]
    if not source_videos:
        return SearchResultVerdictResponse(items=[], stage_ms=0)

    videos: List[Dict[str, Any]] = []
    for v in source_videos:
        video_id = str(v.video_id or "").strip()
        title = str(v.title or "").strip()
        if not video_id or not title:
            continue
        videos.append(
            {
                "video_id": video_id,
                "title": title,
                "channel_name": (v.channel_name or "").strip(),
                "duration": (v.duration or "").strip(),
            }
        )

    if not videos:
        return JSONResponse(status_code=400, content={"error": "invalid_input", "message": "videos must contain video_id and title"})

    items = await _run_search_result_batch_verdict(search_query, videos)
    stage_ms = int((time.perf_counter() - stage_start) * 1000)

    normalized = [
        SearchResultVerdictItem(
            video_id=str(item.get("video_id") or ""),
            verdict=_normalize_search_verdict(item.get("verdict")),
            reason=str(item.get("reason") or "Metadata relevance estimate.").strip(),
            confidence=float(item.get("confidence", 0.5)),
        )
        for item in items
        if str(item.get("video_id") or "").strip()
    ]

    return SearchResultVerdictResponse(items=normalized, stage_ms=stage_ms)


@router.post("/deep-analysis", response_model=SmartWatchDeepResult)
async def smart_watch_deep_analysis(payload: SmartWatchDeepRequest):
    stage2_start = time.perf_counter()
    video_id = payload.video_id.strip()
    question = payload.user_question.strip()
    if not video_id or not question:
        return JSONResponse(status_code=400, content={"error": "invalid_input", "message": "video_id and user_question are required"})
    if payload.verdict.strip().lower() == "skip":
        return SmartWatchDeepResult(
            relevant_moments=[],
            total_relevant_moments=0,
            analysis_complete=False,
            stage2_ms=0,
            skipped=True,
            reason="Deep analysis skipped — video verdict was skip",
            prompt_version=PROMPT_VERSION,
        )

    try:
        cached = get_cached_transcript(video_id)
    except Exception as exc:
        logger.warning("Smart Watch cache read failed for deep analysis: %s", exc)
        cached = None

    transcript = str((cached or {}).get("transcript") or "").strip()
    if not transcript:
        return JSONResponse(
            status_code=422,
            content={"error": "transcript_unavailable", "message": "Could not fetch transcript for this video"},
        )

    items = _extract_timestamped_sentences(transcript)
    chunks = _chunk_by_sentences(items, 30)
    formatted_chunks = [_format_chunk_with_timestamps(chunk) for chunk in chunks if chunk]
    if not formatted_chunks:
        return SmartWatchDeepResult(
            relevant_moments=[],
            total_relevant_moments=0,
            analysis_complete=True,
            stage2_ms=int((time.perf_counter() - stage2_start) * 1000),
            prompt_version=PROMPT_VERSION,
        )

    tasks = [_analyze_chunk_with_gemini(question, ctext) for ctext in formatted_chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_moments: List[Dict[str, Any]] = []
    for result in results:
        if isinstance(result, Exception):
            continue
        all_moments.extend(result)

    deduped = _dedupe_and_rank(all_moments)
    with_urls = []
    for m in deduped:
        sec = int(m.get("timestamp_seconds", 0))
        with_urls.append(
            {
                "timestamp_seconds": sec,
                "timestamp_display": str(m.get("timestamp_display", _format_mmss(sec))),
                "quote": str(m.get("quote", "")),
                "relevance": str(m.get("relevance", "")),
                "youtube_url": f"https://youtube.com/watch?v={video_id}&t={sec}",
            }
        )

    stage2_ms = int((time.perf_counter() - stage2_start) * 1000)
    user_id = None
    try:
        session = get_session(payload.session_id)
        user_id = (session or {}).get("user_id")
    except Exception:
        user_id = None
    try:
        save_smart_watch_analysis(
            session_id=payload.session_id,
            video_id=video_id,
            video_url=f"https://youtube.com/watch?v={video_id}",
            user_question=question,
            reason="Deep analysis complete",
            user_id=user_id,
            video_title=video_id,
            relevant_moments=with_urls,
            stage2_ms=stage2_ms,
        )
    except Exception as exc:
        logger.warning("Failed saving Smart Watch deep analysis: %s", exc)
    try:
        track_analytics_event(
            session_id=payload.session_id,
            user_id=user_id,
            event_name="smart_watch_deep_analysis",
            payload={
                "video_id": video_id,
                "moments_found": len(with_urls),
                "stage2_ms": stage2_ms,
                "prompt_version": PROMPT_VERSION,
            },
        )
    except Exception as exc:
        logger.warning("Failed tracking deep-analysis analytics: %s", exc)

    return SmartWatchDeepResult(
        relevant_moments=[SmartWatchMoment(**m) for m in with_urls],
        total_relevant_moments=len(with_urls),
        analysis_complete=True,
        stage2_ms=stage2_ms,
        prompt_version=PROMPT_VERSION,
    )


@router.post("/history", response_model=SmartWatchHistoryResponse)
async def smart_watch_history(payload: SmartWatchHistoryRequest):
    session_id = payload.session_id.strip()
    if not session_id:
        return JSONResponse(status_code=400, content={"error": "invalid_input", "message": "session_id is required"})

    session = get_session(session_id) or {}
    session_user_id = session.get("user_id")

    requested_user_id = (payload.user_id or "").strip() or None
    if requested_user_id and session_user_id and requested_user_id != session_user_id:
        return JSONResponse(status_code=403, content={"error": "forbidden", "message": "Cannot access another user's history"})

    effective_user_id = requested_user_id or session_user_id or None

    try:
        rows = list_smart_watch_analyses(
            session_id=session_id,
            user_id=effective_user_id,
            limit=payload.limit,
        )
    except Exception as exc:
        logger.warning("Failed reading Smart Watch history: %s", exc)
        return SmartWatchHistoryResponse(items=[])

    mode_filter = (payload.mode or "").strip().lower()
    if mode_filter in {"study", "work", "quick"}:
        def infer_mode(row: Dict[str, Any]) -> str:
            verdict = str(row.get("verdict") or "").lower()
            if verdict in {"watch", "skim", "skip"}:
                return "quick"
            question = str(row.get("user_question") or "").lower()
            if "work" in question or "team" in question:
                return "work"
            return "study"
        rows = [r for r in rows if infer_mode(r) == mode_filter]

    items = [SmartWatchHistoryItem(**row) for row in rows]
    return SmartWatchHistoryResponse(items=items)


@router.post("/analytics")
async def smart_watch_analytics(payload: SmartWatchAnalyticsRequest):
    session_id = payload.session_id.strip()
    event_name = payload.event_name.strip()
    if not session_id or not event_name:
        return JSONResponse(status_code=400, content={"error": "invalid_input", "message": "session_id and event_name are required"})
    try:
        track_analytics_event(
            session_id=session_id,
            user_id=(payload.user_id or None),
            event_name=event_name,
            payload=payload.payload or {},
        )
    except Exception as exc:
        logger.warning("Failed tracking analytics event: %s", exc)
    return {"status": "ok"}


@router.post("/dashboard", response_model=SmartWatchDashboardResponse)
async def smart_watch_dashboard(payload: SmartWatchDashboardRequest):
    session_id = payload.session_id.strip()
    if not session_id:
        return JSONResponse(status_code=400, content={"error": "invalid_input", "message": "session_id is required"})

    session = get_session(session_id) or {}
    session_user_id = session.get("user_id")
    requested_user_id = (payload.user_id or "").strip() or None
    if requested_user_id and session_user_id and requested_user_id != session_user_id:
        return JSONResponse(status_code=403, content={"error": "forbidden", "message": "Cannot access another user's dashboard"})
    effective_user_id = requested_user_id or session_user_id or None

    try:
        analyses = list_smart_watch_analyses(session_id=session_id, user_id=effective_user_id, limit=100)
    except Exception:
        analyses = []
    try:
        events = list_analytics_events(session_id=session_id, user_id=effective_user_id, limit=300)
    except Exception:
        events = []

    verdicts = [str(a.get("verdict") or "").lower() for a in analyses]
    confidences = [float(a["confidence"]) for a in analyses if a.get("confidence") is not None]
    stage1 = [int(a["stage1_ms"]) for a in analyses if a.get("stage1_ms") is not None]
    stage2 = [int(a["stage2_ms"]) for a in analyses if a.get("stage2_ms") is not None]
    timestamps_generated = sum(len(a.get("relevant_moments") or []) for a in analyses)
    estimated_time_saved_minutes = 0.0

    duration_cache: Dict[str, float] = {}
    for analysis in analyses:
        video_id = str(analysis.get("video_id") or "").strip()
        if not video_id:
            continue
        if video_id not in duration_cache:
            try:
                cached_t = get_cached_transcript(video_id) or {}
                duration_cache[video_id] = float(cached_t.get("duration_minutes") or 0.0)
            except Exception:
                duration_cache[video_id] = 0.0

        duration_minutes = duration_cache.get(video_id, 0.0)
        if duration_minutes <= 0:
            continue
        verdict = str(analysis.get("verdict") or "").lower()
        if verdict == "skip":
            estimated_time_saved_minutes += duration_minutes
        elif verdict == "skim":
            estimated_time_saved_minutes += duration_minutes * 0.65

    timestamp_clicks = 0
    for ev in events:
        insights = ev.get("insights") or {}
        if insights.get("event_name") == "smart_watch_timestamp_clicked":
            timestamp_clicks += 1

    return SmartWatchDashboardResponse(
        total_analyses=len(analyses),
        watch_count=sum(1 for v in verdicts if v == "watch"),
        skim_count=sum(1 for v in verdicts if v == "skim"),
        skip_count=sum(1 for v in verdicts if v == "skip"),
        avg_confidence=round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
        timestamp_clicks=timestamp_clicks,
        timestamps_generated=timestamps_generated,
        avg_stage1_ms=int(sum(stage1) / len(stage1)) if stage1 else 0,
        avg_stage2_ms=int(sum(stage2) / len(stage2)) if stage2 else 0,
        estimated_time_saved_minutes=round(estimated_time_saved_minutes, 1),
    )

