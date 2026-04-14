<p align="center">
  <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi" />
  <img src="https://img.shields.io/badge/Gemini-1.5_Pro-4285F4?style=flat-square&logo=google" />
  <img src="https://img.shields.io/badge/Notion-API-000000?style=flat-square&logo=notion" />
  <img src="https://img.shields.io/badge/Supabase-Auth-3ECF8E?style=flat-square&logo=supabase" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" />
</p>

<h1 align="center">🧠 NotionClip</h1>
<p align="center"><strong>Watch less. Know more.</strong></p>
<p align="center">
  An AI-powered knowledge extraction engine that turns YouTube videos into structured, timestamped Notion pages — in seconds.
</p>

<p align="center">
  <a href="https://notionclip.vercel.app">Live App</a> ·
  <a href="https://notion-clips.onrender.com/docs">API Docs</a> ·
  <a href="#getting-started">Getting Started</a> ·
  <a href="#architecture">Architecture</a>
</p>

---

## The Problem

Most people watch a 45-minute YouTube video, absorb maybe 20% of it, and have nothing to show for it the next day. Existing tools either give you a flat summary (no structure, no context) or a wall of text you'll never revisit.

NotionClip solves this by treating every video as a **knowledge source** — extracting structured insights based on your intent, timestamping every key moment, and pushing everything into a Notion database that actually gets used.

---

## How It Works

```
YouTube URL  →  Transcript Fetch  →  Gemini AI Extraction  →  Structured Notion Page
```

1. Paste a YouTube URL (or upload a PDF / article)
2. Choose your mode — **Study**, **Work**, or **Quick**
3. NotionClip fetches the transcript, runs Gemini extraction, and pushes a rich Notion page
4. Your master `NotionClip` database gains a new row with two child pages: AI Notes and Your Notes

---

## Modes

Each mode runs a different Gemini prompt chain optimized for that use case.

### 📚 Study Mode
For lectures, courses, and educational content.

Extracts: core concept · formula sheet · key facts · self-test questions · common mistakes · prerequisites · further reading · timestamped moments

### 💼 Work Mode
For demos, industry talks, and professional content.

Extracts: Watch/Skip verdict · one-liner · key points · tools mentioned · decisions to make · next actions · timestamped moments

### ⚡ Quick Mode
For fast browsing, news, and short-form content.

Extracts: summary · key takeaways · topics covered · action items · timestamped moments

---

## Key Features

**🎯 Smart Watch**
Pre-watch AI verdict — Watch, Skip, or Selective — with reasoning and what you'd miss if you skip. Decide before you commit the time.

**⏱ Timestamp Moments**
Auto-detected key moments from the AI output, each linked to the exact second in the YouTube video. Click to jump directly.

**🗄 Notion Database**
Auto-creates a master `NotionClip` database in your workspace with Mode, Source, Status, Tags, Smart Watch Verdict, and Date Added properties. Each entry has structured child pages — not just a flat export.

**🔗 Cross-Source Synthesis**
Combine insights from multiple videos into a single unified analysis. Useful for research, comparison, and building a complete picture across sources.

**📄 Multi-Source Support**
YouTube videos, PDFs, and articles — all fed through the same extraction pipeline.

**📥 Markdown Export**
Download any analysis as a structured `.md` file for offline use.

---

## Notion Structure

Every push creates this structure in your workspace:

```
🧠 NotionClip  (master database)
└── Row: Video Title
    │   Properties: Mode · Source · Link · Summary · Verdict · Status · Tags · Date
    │
    ├── 🧠 AI Notes
    │       Video header + bookmark
    │       AI Summary callout
    │       Mode-specific structured output
    │         (formulas / key facts / self-test / action items / etc.)
    │       Timestamp moments with clickable links
    │
    └── ✍️ Your Notes
            Personal thinking space
            Sections for reactions, connections, and follow-up questions
```

The database has three filtered views — Study, Work, Quick — so your library stays organized automatically.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Vercel)                   │
│   Next.js 14 · TypeScript · Tailwind · Supabase JS      │
└────────────────────────┬────────────────────────────────┘
                         │ REST
┌────────────────────────▼────────────────────────────────┐
│                     Backend (Render)                     │
│              FastAPI · Python · LangChain                │
│                                                          │
│   /transcript    →  YouTube oEmbed + Supadata fallback  │
│   /extract       →  Gemini 1.5 Pro extraction           │
│   /push          →  Notion API database + page write    │
│   /verdict       →  Smart Watch pre-analysis            │
│   /synthesis     →  Multi-source Gemini synthesis       │
│   /qa            →  Transcript Q&A                      │
└──────┬──────────────────────────┬───────────────────────┘
       │                          │
┌──────▼──────┐          ┌────────▼────────┐
│  Supabase   │          │   Notion API    │
│  Auth       │          │   Databases     │
│  Sessions   │          │   Pages         │
│  Cache      │          │   OAuth         │
└─────────────┘          └─────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| AI | Google Gemini 1.5 Pro via LangChain |
| Auth | Supabase (Google OAuth) |
| Database | Supabase (sessions, transcript cache, insight cache) |
| Notion | Notion API v2022-06-28, OAuth 2.0 |
| Deployment | Vercel (frontend), Render (backend) |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transcript` | Fetch and cache YouTube transcript |
| `POST` | `/extract` | Run Gemini extraction on transcript |
| `POST` | `/extract/pdf` | Extract from uploaded PDF |
| `POST` | `/extract/article` | Extract from article URL |
| `POST` | `/push` | Push insights to Notion master database |
| `POST` | `/notion/timestamp-notes` | Push timestamp notes to existing Notion entry |
| `GET` | `/export/markdown` | Export session insights as Markdown |
| `POST` | `/qa` | Q&A against transcript with chat history |
| `POST` | `/verdict` | Smart Watch pre-watch verdict |
| `POST` | `/synthesis` | Cross-source synthesis across sessions |
| `GET` | `/health` | Health check |

Full interactive docs at `https://notion-clips.onrender.com/docs`.

---

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase project
- Google Gemini API key
- Notion integration with OAuth configured

### Backend

```bash
git clone https://github.com/aayush0444/notionclip
cd notionclip/backend

pip install -r requirements.txt

cp .env.example .env
# Fill in your keys

uvicorn main:app --reload
# API running at http://localhost:8000
```

### Frontend

```bash
cd web

npm install

cp .env.local.example .env.local
# Fill in your keys

npm run dev
# App running at http://localhost:3000
```

---

## Environment Variables

### Backend (`.env`)

```env
GEMINI_API_KEY=
NOTION_CLIENT_ID=
NOTION_CLIENT_SECRET=
NOTION_REDIRECT_URI=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPADATA_API_KEY=
```

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=https://notion-clips.onrender.com
NEXT_PUBLIC_NOTION_CLIENT_ID=
```

---

## Project Structure

```
notionclip/
├── web/                        # Next.js frontend
│   └── src/
│       ├── app/                # App router pages
│       ├── components/         # UI components (modes, export, smart watch)
│       └── lib/                # Store, types, API client
│
├── backend/                    # FastAPI backend
│   ├── main.py                 # API entrypoint + all endpoints
│   ├── push_to_notion.py       # Notion database + page management
│   ├── gemini.py               # AI extraction via LangChain + Gemini
│   ├── models.py               # Pydantic models
│   ├── youtube_mode.py         # Transcript fetching + video ID parsing
│   ├── notion_oauth.py         # OAuth 2.0 flow
│   ├── smart_watch.py          # Pre-watch verdict router
│   └── supabase_client.py      # Session and cache management
│
├── landing/                    # Marketing landing page
└── extension/                  # Chrome extension (in progress)
```

---

## Comparison

| Feature | NotionClip | Snippo | NoteGPT | NotebookLM |
|---------|-----------|--------|---------|------------|
| Structured AI extraction | ✅ Mode-specific | ❌ | ⚠️ Generic | ❌ |
| Notion integration | ✅ Deep (DB + child pages) | ❌ | ❌ | ❌ |
| Timestamped moments | ✅ Clickable links | ❌ | ❌ | ❌ |
| Watch/Skip verdict | ✅ | ❌ | ❌ | ❌ |
| Cross-source synthesis | ✅ | ❌ | ❌ | ✅ |
| PDF + Article support | ✅ | ❌ | ⚠️ | ✅ |
| Study mode (formulas, Q&A) | ✅ | ❌ | ❌ | ❌ |
| Open source | ✅ | ❌ | ❌ | ❌ |

---

## Roadmap

- [x] YouTube extraction — Study / Work / Quick modes
- [x] Notion OAuth + master database with child pages
- [x] Smart Watch pre-watch verdict
- [x] Timestamp moments with clickable YouTube links
- [x] Cross-source synthesis across multiple sessions
- [x] PDF and article extraction
- [x] Markdown export
- [ ] Chrome extension (in progress)
- [ ] Saved filtered views per mode in Notion
- [ ] Multi-language transcript support
- [ ] Mobile app

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

```bash
# Fork the repo, then:
git checkout -b feature/your-feature-name
git commit -m "feat: description of change"
git push origin feature/your-feature-name
# Open a pull request
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built by <a href="https://aayushkumarportfolio.vercel.app">Aayush Kumar</a> · IIT Jammu · 2025<br/>
  <a href="https://linkedin.com/in/aayush-kumar-redhu-965285371">LinkedIn</a> ·
  <a href="https://github.com/aayush0444">GitHub</a>
</p>