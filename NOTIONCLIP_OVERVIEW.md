# NotionClip: Technical & Feature Overview

## Table of Contents
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Core Architecture](#core-architecture)
- [Primary Features](#primary-features)
- [Backend Design & API](#backend-design--api)
- [Frontend Design & User Flow](#frontend-design--user-flow)
- [Notion, Supabase, and Gemini Integrations](#notion-supabase-and-gemini-integrations)
- [Design Rationale](#design-rationale)
- [Unique Algorithms & Implementation Details](#unique-algorithms--implementation-details)

---

## Project Structure

```
NotionClip/
├── app.py                  # Streamlit UI entrypoint (legacy/alt UI)
├── backend/                # FastAPI backend (core logic, API, integrations)
│   ├── main.py             # API entrypoint, all endpoints
│   ├── content_ingestion.py# PDF/article ingestion
│   ├── export_utils.py     # Markdown export helpers
│   ├── gemini.py           # AI extraction, Gemini/LangChain logic
│   ├── models.py           # Pydantic models
│   ├── notion_oauth.py     # Notion OAuth2 flow
│   ├── push_to_notion.py   # Notion API push logic
│   ├── smart_watch.py      # Pre-watch verdicts, timestamping
│   ├── study_session.py    # Multi-source study session logic
│   ├── supabase_client.py  # Supabase session/cache helpers
│   ├── unified_library.py  # Unified library API
│   └── youtube_mode.py     # YouTube transcript fetch/parsing
├── notionclip-web/         # Next.js 14 frontend (main user UI)
│   ├── src/app/            # App router pages
│   ├── src/components/     # UI components (modes, export, smart watch)
│   └── src/lib/            # Store, types, API client
├── pages_ui/               # Streamlit UI pages (legacy/alt UI)
│   └── *.py                # Home, YouTube, History, Settings, etc.
├── CREATE_LIBRARY_TABLE.sql# Supabase schema for unified library
├── requirements.txt        # Python dependencies
├── config.toml, secrets.toml # Config files
└── README.md               # Project overview
```

## Tech Stack
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend:** FastAPI (Python 3.11+)
- **AI:** Google Gemini 1.5 Pro (via LangChain)
- **Auth/DB:** Supabase (OAuth, session, cache, unified library)
- **Notion:** Notion API v2022-06-28, OAuth 2.0
- **Deployment:** Vercel (frontend), Render (backend)

## Core Architecture
- **Frontend** (notionclip-web):
  - Next.js app for user interaction, library management, and export.
  - Communicates with backend via REST API.
- **Backend** (backend/):
  - FastAPI app exposes endpoints for transcript extraction, AI processing, Notion push, and library management.
  - Handles all integrations (Notion, Supabase, Gemini).
- **Unified Library:**
  - All user content (YouTube, study sessions, smart watch verdicts) is stored in a single Supabase table for easy retrieval and search.

## Primary Features
### 1. YouTube to Notion Extraction
- Paste a YouTube URL, select a mode (Study, Work, Quick).
- Backend fetches transcript, runs openrouter extraction using free models, and pushes structured notes to Notion.
- Each Notion entry includes AI Notes (summary, key facts, timestamped moments) and a personal notes page.

### 2. Multi-Mode Extraction
- **Study Mode:** For lectures/courses. Extracts core concepts, formulas, key facts, self-test questions, mistakes, prerequisites, further reading, and timestamped moments.
- **Work Mode:** For professional content. Extracts verdict (watch/skip), one-liner, key points, tools, decisions, next actions, timestamped moments.
- **Quick Mode:** For fast browsing. Extracts summary, key takeaways, topics, action items, timestamped moments.

### 3. Smart Watch (Pre-Watch Verdict)
- AI predicts if a video is worth watching, skimming, or skipping, with reasoning and what you’d miss if you skip.
- Timestamped key moments are auto-detected and linked to video seconds.

### 4. Unified Library
- All processed content is stored in a Supabase table (`user_library`), supporting search, filtering, and export.
- Each entry is tagged by mode, source, and type.

### 5. Study Sessions (Multi-Source Learning)
- Users can create a study session with multiple sources (YouTube, PDF, article).
- AI builds a knowledge map, finds agreements/contradictions, and generates a teaching plan.
- Q&A and knowledge checks are supported for active learning.

### 6. Export & Markdown Download
- Any analysis can be exported as a structured Markdown file.
- Notion pushes create a master database with filtered views for each mode.

## Backend Design & API
- **Endpoints:** `/transcript`, `/extract`, `/push`, `/qa`, `/verdict`, `/library`, `/study-session`, etc.
- **Transcript Fetching:** YouTube transcript is fetched, cached in Supabase, and used for downstream extraction.
- **AI Extraction:** Gemini (via LangChain) processes transcript, output is cached for speed and cost.
- **Notion Push:** Structured notes are pushed to a Notion database, with child pages for AI and user notes.
- **Library API:** All user content is stored and retrievable via `/library` endpoints.
- **Study Session API:** Multi-source sessions, knowledge map, tutor output, and Q&A are managed here.

## Frontend Design & User Flow
- **Minimal Friction:** Paste a URL, select mode, process, review, and export to Notion in a few clicks.
- **Modes:** Users can switch between Study, Work, and Quick modes for tailored extraction.
- **Session Management:** History and library views allow users to revisit and re-export any processed content.
- **Settings:** Users connect Notion and AI keys via a guided UI.

## Notion, Supabase, and Gemini Integrations
- **Notion:**
  - OAuth2 flow for secure workspace access.
  - Master database auto-created with structured properties and filtered views.
  - Each entry has AI Notes and Your Notes as child pages.
- **Supabase:**
  - Auth (Google OAuth), session management, transcript/insight caching, and unified library storage.
  - Row-level security and user-specific data isolation.
- **Gemini:**
  - Used for all AI extraction, summarization, and Q&A.
  - Chunking and scaling logic ensures deep extraction for long videos.

## Design Rationale
- **Structured Knowledge:** Unlike flat clippers, NotionClip creates rich, structured Notion pages for real learning and review.
- **Unified Library:** All content types are stored in a single, searchable table for easy access and export.
- **AI-First:** Gemini is used for deep extraction, not just summarization, enabling advanced features like Smart Watch and knowledge maps.
- **User-Centric Flow:** Minimal setup, fast processing, and one-click export keep users in flow.

## Unique Algorithms & Implementation Details
- **Transcript Chunking:** Long videos are split into overlapping chunks for deep, scalable AI extraction.
- **Smart Watch Verdict:** AI model predicts watch/skim/skip verdicts before user commits time, with confidence and timestamped highlights.
- **Knowledge Map (Study Sessions):** AI builds a concept map across multiple sources, finds agreements/contradictions, and generates a teaching plan.
- **Supabase Caching:** All transcripts and insights are cached for speed and cost efficiency.
- **Notion Push Logic:** Robust handling of Notion API, including fallback for page/database creation and child page management.

---

> **Note:**
> - The browser extension and cross-synthesis features are not included in this overview as they are not implemented or not working.
> - This document is based on a full codebase review as of April 2026.
