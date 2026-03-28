# ⚡ NOTIONCLIPS - QUICK TESTING REFERENCE

Quick commands and API testing for immediate feature validation

---

## 🔧 BACKEND API TESTING (CURL COMMANDS)

### Setup
```bash
# Backend running on localhost:8000
BASE_URL="http://localhost:8000"

# YouTube transcript example
VIDEO_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Test 1: Study Mode Extraction
```bash
curl -X POST "$BASE_URL/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Your transcript text here...",
    "mode": "study",
    "source_url": "'$VIDEO_URL'",
    "questions": ["What is the main concept?", "What formulas are introduced?"]
  }' | jq .
```

**Expected Response:**
```json
{
  "title": "...",
  "core_concept": "...",
  "formula_sheet": [...],
  "key_facts": [...],
  "common_mistakes": [...],
  "self_test": [...],
  "prerequisites": [...],
  "further_reading": [...]
}
```

**✓ Signal it's working:**
- All fields present
- Formulas have variables defined
- Mistakes are non-obvious
- Questions are addressed in content

---

### Test 2: Work Mode Extraction
```bash
curl -X POST "$BASE_URL/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Your transcript text here...",
    "mode": "work",
    "source_url": "https://example.com/article",
    "questions": ["What decisions do we need to make?"]
  }' | jq .
```

**Expected Response:**
```json
{
  "title": "...",
  "one_liner": "...",
  "watch_or_skip": "Watch",
  "confidence": 85,
  "key_points": [...],
  "tools_mentioned": [...],
  "decisions_to_make": [...],
  "next_actions": [...]
}
```

**✓ Signal it's working:**
- Watch/Skip is clear with 0-100 confidence
- Key points are business-relevant
- Decisions are actionable
- Next actions have details

---

### Test 3: Quick Mode Extraction
```bash
curl -X POST "$BASE_URL/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Your transcript text here...",
    "mode": "quick",
    "source_url": "https://example.com/video"
  }' | jq .
```

**Expected Response:**
```json
{
  "title": "...",
  "summary": "...",
  "key_takeaways": [...],
  "topics_covered": [...],
  "action_items": [...]
}
```

**✓ Signal it's working:**
- Summary is 2-3 sentences
- Key takeaways are interesting (not obvious)
- Total JSON size < 5KB
- Fast response (< 30 seconds)

---

### Test 4: Synthesis Endpoint
```bash
# First, prepare session IDs from Supabase
SESSION_ID_1="uuid-from-extraction-1"
SESSION_ID_2="uuid-from-extraction-2"
SESSION_ID_3="uuid-from-extraction-3"

curl -X POST "$BASE_URL/synthesis" \
  -H "Content-Type: application/json" \
  -d '{
    "session_ids": ["'$SESSION_ID_1'", "'$SESSION_ID_2'", "'$SESSION_ID_3'"],
    "user_question": "How do these sources compare on topic X?"
  }' | jq .
```

**Expected Response:**
```json
{
  "common_themes": [
    {
      "theme": "..."
      "present_in_sources": [0, 1, 2]
    }
  ],
  "unique_insights": [
    {
      "insight": "...",
      "source_index": 0
    }
  ],
  "contradictions": [
    {
      "topic": "...",
      "source_positions": ["Source 1: ...", "Source 2: ..."]
    }
  ],
  "synthesis_summary": "...",
  "recommended_order": [0, 2, 1],
  "knowledge_gaps": ["topic1", "topic2"]
}
```

**✓ Signal it's working:**
- All 6 sections present
- Common themes are specific (not generic)
- Contradictions show actual disagreements
- Reading order is pedagogical
- Gaps are meaningful

---

### Test 5: Q&A Endpoint
```bash
curl -X POST "$BASE_URL/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is photosynthesis?",
    "transcript": "Your transcript text here...",
    "context_mode": "study"
  }' | jq .
```

**Expected Response:**
```json
{
  "answer": "...",
  "confidence": 0.85,
  "sources": ["timestamp1", "timestamp2"]
}
```

---

### Test 6: Export Markdown
```bash
curl -X GET "$BASE_URL/export/markdown?session_id=$SESSION_ID" \
  -H "Accept: text/markdown" \
  > export.md

cat export.md  # View content
```

**✓ Signal it's working:**
- File downloads successfully
- Content is markdown formatted (# headers, - lists)
- All sections present

---

## 🎯 FRONTEND MANUAL TESTING

### Quick Test Suite (5 minutes)
```
1. Study Mode:
   ✓ Paste YouTube link
   ✓ Add 2 questions
   ✓ Click Study mode
   ✓ Click Process
   ✓ Wait for results
   ✓ Verify formulas present
   ✓ Click "Save to Notion"

2. Work Mode:
   ✓ Paste article link
   ✓ Click Work mode
   ✓ Process
   ✓ Check one-liner is crisp
   ✓ Check Watch/Skip verdict

3. Quick Mode:
   ✓ Paste podcast/casual video
   ✓ Quick mode
   ✓ Process
   ✓ Verify reads in <3 min

4. Smart Watch:
   ✓ Enter focus question
   ✓ Get verdict (Watch/Skim/Skip)
   ✓ If "Watch", check timestamps

5. Synthesis:
   ✓ Go to Synthesis tab
   ✓ Select 2+sessions
   ✓ Click Synthesize
   ✓ Verify all 6 sections
   ✓ Export as Markdown

6. History:
   ✓ Check all past sessions appear
   ✓ Click past session
   ✓ Results load instantly

Total time: ~5 minutes for quick validation
```

---

## 🗄️ DATABASE TESTING (Supabase)

### Check Session Storage
```sql
-- View all sessions
SELECT id, title, extraction_type, created_at 
FROM sessions 
ORDER BY created_at DESC
LIMIT 10;

-- View latest extraction for a session
SELECT id, session_id, title, caching_key
FROM extractions
WHERE session_id = 'YOUR_SESSION_UUID'
ORDER BY created_at DESC
LIMIT 1;

-- Check cache entries
SELECT * FROM cache_entries
WHERE created_at > NOW() - INTERVAL '1 day'
ORDER BY created_at DESC;
```

---

## 📝 COMPREHENSIVE TEST CHECKLIST

### Before Production Release

#### Core Extraction (30 min)
- [ ] Study mode: Formulas are accurate
- [ ] Study mode: Self-tests are rigorous
- [ ] Work mode: Decisions are real choices
- [ ] Work mode: Watch/Skip verdicts make sense
- [ ] Quick mode: Reads in <3 minutes
- [ ] All modes: Include timestamps
- [ ] All modes: Address user questions

#### Question-First (10 min)
- [ ] Questions display in UI
- [ ] Same content + same questions = cached (instant)
- [ ] Same content + different questions = new extraction
- [ ] Results explicitly address questions

#### Smart Watch (10 min)
- [ ] Verdict is Watch/Skim/Skip
- [ ] Confidence 0-100
- [ ] Stage 2 shows relevant timestamps
- [ ] Different questions = different verdicts

#### Synthesis (15 min)
- [ ] Requires 2+ sessions
- [ ] Returns all 6 sections
- [ ] Common themes are specific
- [ ] Contradictions are real disagreements
- [ ] Reading order is logical
- [ ] Export (Text/MD/JSON) work

#### Exports (10 min)
- [ ] Markdown exports with formatting
- [ ] Text exports as plain text
- [ ] HTML exports as valid HTML
- [ ] All exports complete
- [ ] File sizes reasonable

#### Notion Integration (5 min)
- [ ] OAuth flow works
- [ ] Save button pushes to Notion
- [ ] Page created in workspace
- [ ] Content transferred correctly

#### UI/UX (10 min)
- [ ] No console errors
- [ ] Mode switching works smoothly
- [ ] Results display correctly
- [ ] Export buttons responsive
- [ ] Loading states show

#### Edge Cases (10 min)
- [ ] Synthesis with <2 sessions fails gracefully
- [ ] Invalid URLs show error
- [ ] Short content still extracts
- [ ] Very long content handled
- [ ] Network errors handled

**Total: ~90 minutes for comprehensive validation**

---

## 🐛 DEBUGGING QUICK COMMANDS

### Python Backend

**Check server is running:**
```bash
curl http://localhost:8000/health
# Should return {"status": "healthy"}
```

**Check Gemini API connection:**
```bash
python -c "
from gemini import test_gemini_connection
test_gemini_connection()
"
```

**Check Supabase connection:**
```bash
python -c "
from backend.supabase_client import get_supabase
client = get_supabase()
print('Connected:', client is not None)
"
```

**View Python syntax errors:**
```bash
python -m py_compile app.py gemini.py models.py backend/main.py
# No output = no syntax errors
```

### Frontend (React)

**Check for TypeScript errors:**
```bash
cd notionclip-web
npm run build
# Should complete with 0 errors
```

**Check for Next.js issues:**
```bash
cd notionclip-web
next lint
# Check for eslint warnings
```

**View browser console (Chrome DevTools):**
- F12 → Console tab
- Should show no red errors
- Yellow warnings are OK

---

## ✅ SIGN-OFF CHECKLIST

Once all tests pass:

```
FEATURE TESTING COMPLETE ✓

Study Mode:
  ✓ All 7 output sections present
  ✓ Formulas verified accurate
  ✓ Self-tests are rigorous
  ✓ Questions addressed
  ✓ Timestamps included

Work Mode:
  ✓ One-liner is crisp
  ✓ Watch/Skip verdict sensible
  ✓ Key points business-relevant
  ✓ Decisions are actionable
  ✓ Next actions complete
  ✓ Questions addressed

Quick Mode:
  ✓ Reads in <3 minutes
  ✓ Tone is conversational
  ✓ Takeaways interesting
  ✓ No generic statements

Smart Watch:
  ✓ Verdicts reasonable
  ✓ Stage 2 timestamps relevant
  ✓ Question-dependent

Question-First:
  ✓ Questions guide extraction
  ✓ Cache works correctly
  ✓ Different questions = different results

Timestamps:
  ✓ Format MM:SS or HH:MM:SS
  ✓ Descriptions match moments
  ✓ Within video duration

Synthesis:
  ✓ All 6 sections present
  ✓ Themes specific, not generic
  ✓ Contradictions real
  ✓ Reading order logical
  ✓ Gaps meaningful
  ✓ Exports work (3 formats)

Integration:
  ✓ Notion OAuth works
  ✓ Pages save successfully
  ✓ History panel updated
  ✓ Mode switching smooth

Error Handling:
  ✓ Invalid inputs caught
  ✓ Error messages clear
  ✓ User can recover

PRODUCTION STATUS: 🟢 READY
```

---

## 📞 QUICK REFERENCE

| Feature | API Endpoint | Test Command |
|---------|-------------|---------------|
| Study | POST /extract | `curl -X POST http://localhost:8000/extract` |
| Work | POST /extract | `curl -X POST http://localhost:8000/extract` |
| Quick | POST /extract | `curl -X POST http://localhost:8000/extract` |
| Synthesis | POST /synthesis | `curl -X POST http://localhost:8000/synthesis` |
| Q&A | POST /qa | `curl -X POST http://localhost:8000/qa` |
| Export | GET /export/markdown | `curl -X GET http://localhost:8000/export/markdown` |
| Smart Watch | (Frontend) | Manual testing |
| Questions | (Frontend) | Manual testing |
| Timestamps | (Frontend + data) | Manual verification |

---

**Use this reference during testing to quickly validate each feature. Estimated full testing time: 90-120 minutes for comprehensive validation.**
