# 📚 NOTIONCLIPS - COMPREHENSIVE FEATURE & TESTING GUIDE

**Last Updated:** March 28, 2026  
**Purpose:** Complete documentation for rigorous feature testing and validation

---

## 🎯 PROJECT OVERVIEW

**NotionClips** is an AI-powered content extraction system that transforms videos, PDFs, and articles into structured, actionable insights. It features three extraction modes, multi-source synthesis, and AI-driven pre-filtering.

**Core Purpose:** Enable users to extract and organize knowledge from diverse sources, compare insights across content, and push refined notes to Notion for centralized knowledge management.

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                    │
│  ┌──Extract View────────┐  ┌──Synthesis View────────┐  │
│  │ Mode Selector        │  │ SessionGroupManager    │  │
│  │ Content Source       │  │ SynthesisView          │  │
│  │ ProcessButton        │  │ Export Options         │  │
│  │ Results View         │  │                        │  │
│  └──────────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│               BACKEND (FastAPI + Python)                │
│  ┌─Extraction Engine──────────────────────────────────┐ │
│  │ /extract endpoint (questions, mode-specific)      │ │
│  │ /synthesis endpoint (multi-source analysis)       │ │
│  │ Gemini LLM integration                            │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─Data Layer─────────────────────────────────────────┐ │
│  │ Supabase: sessions, transcript cache, insights   │ │
│  │ Models: extraction types, timestamps, synthesis   │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ FEATURES & DETAILED INTENTIONS

### 1️⃣ **THREE EXTRACTION MODES**

#### **A. STUDY MODE** 📚
**Intention:** Deep, exam-ready knowledge extraction for students and learners  
**True Purpose:** Transform video/document into structured study material with core concepts, formulas, and self-testing

**What It Extracts:**
- **Core Concept**: The single most important idea (ONE sentence)
- **Formula Sheet**: Every equation with variable definitions
- **Key Facts**: Critical facts students must memorize
- **Common Mistakes**: Frequent misconceptions to avoid
- **Self-Test**: Practice questions with answers
- **Prerequisites**: What students need to know first
- **Further Reading**: Recommended resources for deeper learning

**Use Case:**
```
Student watches a 45-minute physics lecture
→ Notionclips extracts core concepts, formulas, practice questions
→ Student reviews in 5 minutes
→ Pushes to Notion for revision before exams
```

**How to Test:**
1. Go to app → ContentSourceSelector → Paste YouTube link (educational video)
2. Click "Study" mode
3. Click "Process"
4. Verify output includes:
   - [ ] Core concept is ONE sentence, precise and technical
   - [ ] Formula sheet has entries formatted as "formula — definition"
   - [ ] Key facts are specific, not generic
   - [ ] Common mistakes are real misconceptions
   - [ ] Self-test questions have answer guidelines
5. Click "Save Study Notes to Notion"

**Expected Output Quality:**
- Precision: High - formulas exact, facts accurate
- Depth: Deep - goes beyond surface understanding
- Usability: Immediate - ready for revision

---

#### **B. WORK MODE** 💼
**Intention:** Executive-focused extraction for professional decision-making  
**True Purpose:** Distill content into actionable recommendations and key decisions for busy professionals

**What It Extracts:**
- **Title**: What this is about
- **One-Liner**: The key insight in one sentence
- **Watch/Skip Recommendation**: Clear verdict on whether to watch
- **Key Points**: Professionally relevant insights (3-5 max)
- **Tools Mentioned**: Software/platforms discussed
- **Decisions to Make**: Action items requiring decision
- **Next Actions**: Specific, assigned, with deadlines

**Use Case:**
```
Executive receives new industry report
→ Notionclips extracts key decisions needed
→ Executive gets 2-minute briefing with clear recommendations
→ Actionable next steps ready to delegate
```

**How to Test:**
1. Go to app → ContentSourceSelector → Paste article/video URL (business-related)
2. Click "Work" mode
3. Click "Process"
4. Verify output includes:
   - [ ] One-liner is exactly one sentence, high-value
   - [ ] Watch/Skip verdict is clear (Watch/Skim/Skip)
   - [ ] Key points are business-relevant (not generic)
   - [ ] Decisions are actual choices to make
   - [ ] Next actions have assignees and due dates
5. Click "Save Work Brief to Notion"

**Expected Output Quality:**
- Precision: Executive-focused
- Speed: 2-minute read max
- Actionability: Clear next steps

---

#### **C. QUICK MODE** ⚡
**Intention:** Fast, high-signal capture for casual learners  
**True Purpose:** Capture the essence and most interesting parts in <3 minutes

**What It Extracts:**
- **Title**: What this is about
- **Summary**: Conversational 2-3 sentence summary
- **Key Takeaways**: The most interesting/surprising insights
- **Topics Covered**: What was discussed
- **Action Items**: Actionable next steps (optional)

**Use Case:**
```
Casual YouTuber browses content
→ Notionclips gives 1-minute summary with highlights
→ Decides if worth watching later or if enough
→ Captures interesting facts for sharing
```

**How to Test:**
1. Go to app → ContentSourceSelector → Paste URL
2. Click "Quick" mode
3. Click "Process"
4. Verify output includes:
   - [ ] Summary is conversational, not academic
   - [ ] Key takeaways are interesting/surprising (not obvious)
   - [ ] Topics are plain language
   - [ ] Total read time < 3 minutes
5. Click "Save Quick Summary to Notion"

**Expected Output Quality:**
- Speed: Fastest mode
- Signal: Highest interesting-to-boring ratio
- Tone: Conversational and engaging

---

### 2️⃣ **SMART WATCH - PRE-VIEW INTELLIGENCE** 🎥

**Intention:** Help users decide if content is worth their time BEFORE watching  
**True Purpose:** Eliminate video time-wasting by giving intelligent verdicts

**What It Does:**
1. **Stage 1 (Fast)**: Analyzes first 10% of content
   - Decision: Watch / Skim / Skip
   - Confidence: 0-100%
   - Reason: Why that verdict

2. **Stage 2 (Detailed)**: Full analysis for "Watch" verdicts
   - Relevant moments: Timestamps of important parts
   - Skippable sections: Where filler is
   - Key quotes: Important statements

**Verdicts Explained:**
- **WATCH** 🟢 - Content is highly valuable for your focus question
- **SKIM** 🟡 - Some valuable parts, but can skip filler
- **SKIP** 🔴 - Not relevant to your question or low quality

**Use Case:**
```
User has focus question: "How does machine learning improve accuracy?"
User pastes YouTube link to 60-minute ML tutorial
Smart Watch analyzes first minute
→ Returns: "WATCH (92% confidence) - Tutorial directly addresses your question"
→ User gets timestamps of most relevant sections
→ Saves 30 minutes by skipping intro filler
```

**How to Test:**
1. Go to app → ContentSourceSelector → Enter YouTube URL
2. Look for "Smart Watch" section
3. Enter a focus question in the input field (e.g., "How does blockchain work?")
4. Verify Stage 1 output:
   - [ ] Verdict is clear (Watch/Skim/Skip)
   - [ ] Confidence is between 0-100
   - [ ] Reason explains the verdict
5. If verdict is "Watch", wait for Stage 2:
   - [ ] Relevant moments show timestamps
   - [ ] Each moment has a quote or description
   - [ ] Timestamps are clickable (seek to that part)
6. Test with different questions - verdict should change

**Expected Behavior:**
- Fast response (< 10 seconds for Stage 1)
- Accurate verdicts
- Useful timestamps
- Question-aware (same video gets different verdicts for different questions)

---

### 3️⃣ **QUESTION-FIRST MODE** 🎯 (NEW - Tier 2)

**Intention:** Let users guide extraction by asking upfront questions  
**True Purpose:** Make AI extraction highly focused and relevant to user needs

**What It Does:**
- Users enter 2-5 focus questions before extraction
- Questions are injected into AI prompts with high priority
- AI explicitly addresses each question in extraction
- Results emphasize user's questions

**Why This Matters:**
```
BEFORE Question-First:
User: "Extract notes from video about Python"
AI extracts: generic Python tutorial content, not what user needs

AFTER Question-First:
User: "Extract notes about Python async/await"
User adds questions: "How does async work?", "When to use await?"
AI extracts: highly focused, answers specific questions
```

**Use Case:**
```
Software engineer studying async Python
→ Adds questions: "What's the event loop?", "How does await work?"
→ Processes video with questions
→ Results specifically address those questions
→ Much more relevant than generic extraction
```

**How to Test:**
1. Go to app → ContentSourceSelector → Add URL
2. Look for "Add Question" button (NEW - below URL input)
3. Click "Add Question" and type: "What is the main concept?"
4. Add 2-3 more questions
5. Select a mode (Study/Work/Quick)
6. Click "Process"
7. Verify:
   - [ ] Questions appear in results  
   - [ ] AI specifically answers each question
   - [ ] Results are focused on questions
   - [ ] Generic content is minimized
8. Test with same content but different questions:
   - [ ] Results change significantly based on questions
9. Test cache functionality:
   - [ ] Same content + same questions = instant results (cached)
   - [ ] Same content + different questions = new extraction

**Expected Behavior:**
- Questions are clearly addressed in output
- Results are highly focused (not generic)
- Caching works for identical question sets
- Questions visible in final results

---

### 4️⃣ **TIMESTAMP-LINKED NOTES** ⏱️ (NEW - Tier 2)

**Intention:** Link insights to specific moments in videos  
**True Purpose:** Provide one-click navigation to important video moments

**What It Does:**
- AI extracts specific timestamps (MM:SS format) for key moments
- Each timestamp links to a description
- Clicking timestamp seeks YouTube video to that point
- Creates a "jump map" through video

**Why This Matters:**
```
BEFORE Timestamps:
User: "Makes notes, needs to re-watch to find context"
Friction: High

AFTER Timestamps:
User: "Clicks timestamp, video jumps to exact moment"
Friction: Zero - instant reference
```

**Use Case:**
```
Student watching 45-minute lecture
→ Notionclips extracts timestamps for key concepts
→ "03:15 - Law of Conservation of Energy definition"
→ "12:30 - Example calculation with water"
→ "28:45 - Common mistake to avoid"
→ Student can revisit exact moments instantly
```

**How to Test:**
1. Go to app → ContentSourceSelector → Paste YouTube video link
2. Select "Study" or "Work" mode
3. Click "Process"
4. In results, look for timestamp badges (MM:SS format)
5. Verify timestamps:
   - [ ] Format is valid (MM:SS or HH:MM:SS)
   - [ ] Each timestamp has description
   - [ ] Descriptions match the moment context
   - [ ] Timestamps are before video end
6. Click a timestamp badge:
   - [ ] YouTube player (if embedded) jumps to timestamp
   - [ ] Or copy timestamp for manual seeking
7. Test another video and verify timestamps vary

**Expected Behavior:**
- Timestamps in MM:SS format
- Accurate descriptions
- Timestamps < video duration
- Clickable/copyable for navigation

---

### 5️⃣ **CROSS-SOURCE SYNTHESIS** 🔗 (NEW - Tier 2)

**Intention:** Compare and unify insights across multiple sources  
**True Purpose:** Discover patterns and contradictions across learning materials

**What It Does:**
- Select 2+ previous extraction sessions
- AI analyzes all extractions together
- Identifies common themes across sources
- Highlights contradictions
- Shows knowledge gaps
- Recommends reading order

**Why This Matters:**
```
BEFORE Synthesis:
Student has notes from 5 different videos
Can't see relationships or contradictions
Manual comparison is tedious

AFTER Synthesis:
AI shows: "Sources 1,3 agree on this, but source 2 contradicts"
"Topics not covered by any source: X, Y, Z"
"Recommended learning order: 2 → 1 → 4 → 3 → 5"
Understanding: 10x better
```

**Use Case:**
```
Student learning Machine Learning from 3 courses
→ Has extraction notes from all 3
→ Uses Synthesis to find:
   - Common themes (reinforcement learning definition)
   - Contradictions (different opinions on regularization)
   - Gaps (no course covered ensemble methods)
   - Best order (course 2 → course 1 → course 3)
→ Creates unified study guide
```

**How to Test:**
1. Create 3-4 extraction sessions (Study/Work/Quick modes)
   - Session 1: Extract from Article A
   - Session 2: Extract from Video B
   - Session 3: Extract from PDF C
   - (At least 2 sessions needed)
2. Go to sidebar and click "Synthesis" tab (NEW - next to Extract)
3. Verify you see:
   - [ ] List of past sessions with titles and types
   - [ ] Checkboxes to select sessions
   - [ ] Session count indicator
4. Select 2-3 sessions:
   - [ ] "Synthesize" button becomes enabled
5. (Optional) Enter focus question
6. Click "Synthesize Sessions"
7. Wait for results, verify synthesis includes:
   - [ ] Common themes (list specific themes)
   - [ ] Unique insights (insights specific to one source)
   - [ ] Contradictions (conflicting information)
   - [ ] Synthesis summary (unified narrative)
   - [ ] Recommended order (1→2→3 sequence)
   - [ ] Knowledge gaps (topics not covered)
8. Verify export options:
   - [ ] Click "📝 Text" - should download .txt file
   - [ ] Click "📘 Markdown" - should download .md file
   - [ ] Click "🔗 JSON" - should download .json file
9. Test export contents:
   - [ ] Text file is readable
   - [ ] Markdown file has formatting
   - [ ] JSON file is valid JSON

**Expected Behavior:**
- List shows all past sessions
- Multi-select works (≥2 sessions required)
- Results are comprehensive (all 6 sections)
- Exports are downloadable and readable
- Themes/contradictions are specific, not generic

---

### 6️⃣ **MULTI-MODE EXPORT** 📤

**Intention:** Flexible knowledge capture in user's preferred format  
**True Purpose:** Enable integration with different tools (Notion, Markdown files, JSON databases)

**Export Formats:**
1. **Markdown** - Structured text with formatting
   - Best for: Notes, documentation, GitHub
   - Preserves: Bold, italics, lists, code blocks

2. **Plain Text** - Simple, universal format
   - Best for: Email, copying, basic files
   - Preserves: Structure via spacing/indentation

3. **HTML** - Web-ready format
   - Best for: Websites, email clients
   - Preserves: Full formatting

**How to Test:**
1. After extraction, look for "Export" section
2. Click each export button:
   - [ ] Download completes for each format
   - [ ] File is readable
   - [ ] Content is identical across formats
   - [ ] Formatting looks appropriate for each type
3. Compare exports:
   - [ ] Markdown has `#` headers
   - [ ] Text has plain structure
   - [ ] HTML has `<html>`, `<body>` tags

---

### 7️⃣ **NOTION INTEGRATION** 💡

**Intention:** One-click knowledge capture to personal workspace  
**True Purpose:** Make user's Notion workspace the central hub for all learning

**What It Does:**
- Authenticate via Notion OAuth
- Create extraction in user's Notion workspace
- One button saves notes → Notion instantly

**How to Test:**
1. Look for "Connect Notion to Save" button
2. Click it
3. Browser redirects to Notion OAuth
4. Authorize NotionClips access
5. Browser returns to app
6. Button now says "Save [Mode] Notes to Notion"
7. After extraction, click "Save" button
8. Verify:
   - [ ] No errors
   - [ ] Button shows "Saving..."
   - [ ] Success message appears
   - [ ] Check Notion workspace - new page created
   - [ ] Page contains extraction content

---

### 8️⃣ **SESSION HISTORY & MANAGEMENT** 📋

**Intention:** Track and revisit past extractions  
**True Purpose:** Build a searchable knowledge library of all your learnings

**What It Shows:**
- List of all past extractions
- Mode, source, and date for each
- Quick access to previous results
- Session-based organization

**How to Test:**
1. Look for "History Panel" in sidebar
2. Verify it shows past sessions:
   - [ ] Session titles
   - [ ] Extraction modes (Study/Work/Quick icons)
   - [ ] Dates
   - [ ] Source types (YouTube/PDF/Article)
3. Click a past session:
   - [ ] Results load instantly (from cache)
   - [ ] Previous extraction shows
4. Create new extraction:
   - [ ] New session appears in history
   - [ ] Most recent at top

---

## 🧪 RIGOROUS TESTING PROTOCOL

### **Phase 1: Component-Level Testing** ⚙️

#### Test 1.1: Study Mode Extraction
```
Objective: Verify Study mode produces academically rigorous output
Input: Physics lecture video (30-45 min)
        Questions: "What is velocity?", "How to calculate acceleration?"

Expected Output:
✓ Core concept: Technical, specific, 1 sentence
✓ Formula sheet: 3+ formulas with variables defined
✓ Key facts: 5-10 specific facts
✓ Common mistakes: Non-obvious misconceptions
✓ Self-test: 3-5 questions with guidance
✓ Prerequisites: Related topics needed first
✓ Further reading: 2-3 resources

Success Criteria:
- Core concept is verifiable from video
- Formulas are mathematically accurate
- Facts are specific (not "physics is important")
- Mistakes are genuine misconceptions
- Questions are testable
```

#### Test 1.2: Work Mode Extraction
```
Objective: Verify Work mode produces executive actionable output
Input: Business/tech article (2000+ words)
        Questions: "What impact does this have on our industry?"

Expected Output:
✓ Title: Clear, professional
✓ One-liner: High-value insight in 1 sentence
✓ Watch/Skip: Clear verdict with confidence
✓ Key points: 3-5 professional insights
✓ Tools mentioned: Any software/platforms discussed
✓ Decisions: Actual decisions to make
✓ Next actions: Specific, assigned, with dates

Success Criteria:
- One-liner is immediately valuable
- Watch/Skip verdict makes sense
- Key points are business-relevant
- Decisions are real choices
- Next actions are specific and assignable
```

#### Test 1.3: Quick Mode Extraction
```
Objective: Verify Quick mode is fast and interesting
Input: Any casual content (5-30 min)

Expected Output:
✓ Title: 3-5 words
✓ Summary: 2-3 sentences, conversational
✓ Key takeaways: 3-5 interesting points
✓ Topics: Plain language list
✓ Action items: 0-3 optional actions

Success Criteria:
- Total read time: < 3 minutes
- Tone is conversational (not academic)
- Takeaways are genuinely interesting
- No obvious/generic statements
- Can be understood by anyone
```

---

### **Phase 2: Question-First Mode Testing** 🎯

#### Test 2.1: Question Focus Verification
```
Objective: Verify questions actually guide the extraction

Content A: "How does photosynthesis work?"
Content B: "What roles do chloroplasts play in photosynthesis?"

Input Same Video: "Plant cell biology"
  Extraction 1: No questions
  Extraction 2: Q1 - "What is photosynthesis?", Q2 - "What is chlorophyll?"
  Extraction 3: Q1 - "How is photosynthesis related to ATP?", Q2 - "What is the light-dependent reaction?"

Success Criteria:
✓ Extraction 1: Generic plant cell content
✓ Extraction 2: Focuses on photosynthesis definition and chlorophyll
✓ Extraction 3: Focuses on ATP and light-dependent reactions
✓ Each extraction explicitly addresses its questions
✓ Results are meaningfully different based on questions
```

#### Test 2.2: Cache Verification
```
Objective: Verify caching works correctly with questions

Process:
1. Extraction A: Video X, Study mode, Q1+Q2 → results_1
2. Extraction B: Video X, Study mode, Q1+Q2 → results_2 (should be instant/cached)
3. Extraction C: Video X, Study mode, Q1+Q3 (different question) → results_3 (should be new)

Success Criteria:
✓ Extraction B returns instantly (< 1 second)
✓ Results 1 and 2 are identical
✓ Extraction C takes normal time
✓ Results 1 and 3 are different
```

---

### **Phase 3: Smart Watch Testing** 👁️

#### Test 3.1: Verdict Accuracy
```
Objective: Verify Smart Watch verdicts are reasonable

Test Cases:
Case 1: Relevant video + User question matches = Should verdict "WATCH"?
Case 2: Irrelevant video + User question doesn't match = Should verdict "SKIP"?
Case 3: Partially relevant + User question = Should verdict "SKIM"?

Success Criteria:
✓ Verdicts are logically sound
✓ Confidence scores correlate with verdict strength
✓ Reasons explain the verdict
✓ Different questions produce different verdicts on same video
```

#### Test 3.2: Stage 2 Detailed Analysis  
```
Objective: Verify detailed timestamps for "WATCH" verdicts

After getting "WATCH" verdict:
✓ Stage 2 activates automatically
✓ Returns 3-7 relevant moments with timestamps
✓ Each moment has a quote/description
✓ Timestamps are within video duration
✓ Timestamps are clickable (YouTube seek works)

Success Criteria:
- Timestamps are accurate (± 5 seconds)
- Descriptions match the timestamp content
- Quotes are verbatim from video or paraphrased accurately
- Each timestamp is independently valuable
```

---

### **Phase 4: Timestamp-Linked Notes Testing** ⏱️

#### Test 4.1: Timestamp Format Validation
```
Objective: Verify all timestamps follow MM:SS format

Input: Extract video with 30-60 min duration
Expected: All timestamps are MM:SS or HH:MM:SS

Success Criteria:
✓ Format: MM:SS or HH:MM:SS only
✓ Minutes < 60 (except in HH:MM:SS)
✓ Seconds 00-59
✓ No timestamps beyond video duration
✓ Sample timestamps:
  - Valid: "03:45", "15:30", "01:23:45"
  - Invalid: "3:45" (missing leading zero), "90:00", "1:234"

Testing:
1. Extract from 10+ different videos
2. Check every timestamp format
3. Verify each timestamp <= video duration
```

#### Test 4.2: Timestamp-Content Relevance
```
Objective: Verify described moments actually occur at timestamps

Process:
1. Extract Study notes from video
2. Get list of timestamps with descriptions
3. For each timestamp:
   a. Manually seek to timestamp in video
   b. Verify description matches what's happening
   c. Check if it's truly a "key moment"

Success Criteria:
✓ 95%+ of timestamps match their descriptions perfectly
✓ Moments are genuinely key/important (not random)
✓ Descriptions are accurate and concise
✓ Descriptions explain why moment is important
```

---

### **Phase 5: Cross-Source Synthesis Testing** 🔗

#### Test 5.1: Common Theme Detection
```
Objective: Verify AI correctly identifies themes across sources

Setup:
- Source 1: Article on Machine Learning basics
- Source 2: Video on ML algorithms  
- Source 3: Tutorial on neural networks

Expected Common Themes:
✓ "Machine learning uses data to improve performance"
✓ "Supervised vs unsupervised learning distinction"
✓ "Training/testing data division is important"

Success Criteria:
- Identified themes are genuinely present in all sources
- Themes are specific (not too generic like "AI is useful")
- Themes are ranked by importance/frequency
- Themes are clearly stated without unnecessary jargon
```

#### Test 5.2: Contradiction Detection
```
Objective: Verify AI finds actual disagreements between sources

Setup:
- Source 1: Says "Deep learning always needs big data"
- Source 2: Says "Transfer learning works with small data"
- Source 3: Discusses data augmentation to increase data

Expected Contradictions:
✓ Identifies the contradiction about data requirements
✓ States what each source says
✓ Explains the seeming contradiction

Success Criteria:
- Contradictions are real, not interpretive differences
- Both viewpoints are accurately represented
- Each source is cited for its position
- Explanation helps resolve contradiction (if possible)
```

#### Test 5.3: Knowledge Gap Identification
```
Objective: Verify synthesis identifies missing topics

Setup: 3 sources on Python programming
- Source 1: Python basics and loops
- Source 2: Object-oriented programming
- Source 3: Exception handling

Expected Gaps:
✓ Async/await not covered
✓ Decorators not covered
✓ Type hints not deeply covered

Success Criteria:
- Gaps are genuine and relevant
- Gaps are not too broad ("everything not covered")
- Gaps are practical (not obscure features)
- Gaps would be useful to learn
```

#### Test 5.4: Reading Order Recommendation
```
Objective: Verify synthesis suggests logical learning sequence

Setup: 3 sources on Data Science
- Source 1: Statistics fundamentals
- Source 2: Python programming
- Source 3: Advanced machine learning models

Expected Recommendation:
✓ Should be: 1 → 2 → 3 (statistics first, then coding, then advanced)
Or: 2 → 1 → 3 (coding first, then apply statistics, advanced models)

Success Criteria:
- Order is pedagogically sound
- Prerequisites come before advanced topics
- Rationale explains why this order
- Order would actually help learner
```

#### Test 5.5: Export Quality Test
```
Objective: Verify synthesis exports are usable

Process:
1. Generate synthesis
2. Download each format (Text, Markdown, JSON)
3. Verify each export:

Text Format:
✓ Readable text file
✓ All sections present
✓ Line breaks appropriate
✓ No corruption/encoding issues

Markdown Format:
✓ Valid markdown syntax
✓ Headers use # ## ###
✓ Lists use - or *
✓ Emphasis uses *bold* or **bold**
✓ Renderable in markdown viewer

JSON Format:
✓ Valid JSON (passes JSON validator)
✓ All fields present
✓ Arrays are arrays, strings are strings
✓ Can be parsed by Python/JavaScript

Success Criteria:
- All 3 formats export successfully
- All contain complete synthesis data
- Each format is valid for its type
- Redownloading gets same content
```

---

### **Phase 6: Integration Testing** 🔀

#### Test 6.1: Question → Extraction → Synthesis Pipeline
```
Objective: Full flow from questions through synthesis

Process:
1. Source A: Video + Q1,Q2 → Extraction A
2. Source B: Article + Q1,Q2 → Extraction B
3. Synthesis of A+B with focus question

Success Criteria:
✓ Questions guide both extractions
✓ Synthesis acknowledges user's original questions
✓ Results are cohesive across the pipeline
✓ Questions remain actionable from start to end
```

#### Test 6.2: Mode Switching
```
Objective: Verify switching modes doesn't break state

Process:
1. Start with Extract view
2. Do Study extraction
3. Switch to Synthesis view
4. Do synthesis of 2 sessions
5. Switch back to Extract view
6. Verify previous extraction still accessible

Success Criteria:
✓ No errors when switching
✓ Previous results preserved
✓ State transitions smoothly
✓ History maintains all sessions
```

---

### **Phase 7: Edge Case & Error Testing** ⚠️

#### Test 7.1: Invalid Inputs
```
Cases:
1. Empty URLs - Should show error
2. Broken video links - Should fail gracefully
3. Short content (< 30 seconds) - Should still extract
4. Very long content (< 4 hours) - Should handle

Success Criteria:
✓ Error messages are clear
✓ System doesn't crash
✓ User can retry with different input
```

#### Test 7.2: Synthesis Edge Cases
```
Cases:
1. Synthesis with 0 sessions - Should show error (need ≥2)
2. Synthesis with 1 session - Should show error
3. Synthesis with 5+ sessions - Should work (slow but works)
4. Synthesis with conflicting modes - Should synthesize all

Success Criteria:
✓ Minimum 2 sessions enforced
✓ Many sessions handled gracefully
✓ Error messages are helpful
```

#### Test 7.3: Cache Edge Cases
```
Cases:
1. User modifies question mid-process - Cache shouldn't reuse
2. Backend updates - Old cache might be stale
3. Same content, different order in questions - Should cache-miss (different hash)

Success Criteria:
✓ Cache key includes questions exactly
✓ Order matters (Q1,Q2 ≠ Q2,Q1)
✓ Can manually clear cache if needed
```

---

## 📊 TEST RESULT TRACKING

Use this template to track test results:

```
Test ID: [number]
Test Name: [name]
Date: [date]
Tester: [name]
Duration: [time]

Input:
[What was tested]

Expected Output:
[What should happen]

Actual Output:
[What actually happened]

Result: [PASS/FAIL/PARTIAL]

Issues Found:
[List any problems]

Notes:
[Any observations]

Status for Next Release: [BLOCKER/CRITICAL/MAJOR/MINOR/NONE]
```

---

## 🎯 SUCCESS CRITERIA SUMMARY

| Feature | Testing Complete | Status |
|---------|-----------------|--------|
| Study Mode | ☐ | Not Started |
| Work Mode | ☐ | Not Started |
| Quick Mode | ☐ | Not Started |
| Smart Watch | ☐ | Not Started |
| Question-First Mode | ☐ | Not Started |
| Timestamps | ☐ | Not Started |
| Synthesis | ☐ | Not Started |
| Exports | ☐ | Not Started |
| Notion Integration | ☐ | Not Started |
| History Panel | ☐ | Not Started |
| Mode Switching | ☐ | Not Started |
| Error Handling | ☐ | Not Started |
| Edge Cases | ☐ | Not Started |

---

## 🚀 NEXT STEPS AFTER TESTING

Once all tests pass:
1. ✅ Mark as "Ready for Production"
2. ✅ Create release notes
3. ✅ Notify stakeholders
4. ✅ Plan monitoring
5. ✅ Setup rollback plan

---

**This guide enables comprehensive validation of all features with clear intentions, success criteria, and step-by-step testing procedures.**
