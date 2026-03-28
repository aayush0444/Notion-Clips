# Integration Guide: Adding Synthesis Mode to App

This guide shows how to integrate the new Synthesis feature into the main app UI.

## Option 1: Add Synthesis Tab (Recommended)

### Step 1: Update ModeSelector to Include Synthesis Toggle

Modify `notionclip-web/src/components/app/ModeSelector.tsx`:

```tsx
import { useState } from 'react'

export function ModeSelector() {
  const { mode, setMode } = useAppStore()
  const [viewMode, setViewMode] = useState<'extract' | 'synthesis'>('extract')
  
  if (viewMode === 'synthesis') {
    return <SynthesisToggle onBack={() => setViewMode('extract')} />
  }
  
  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setViewMode('extract')}
          className="px-3 py-2 rounded-lg bg-blue-500/20 text-blue-200 border border-blue-500/35 text-sm font-medium"
        >
          Extract
        </button>
        <button
          onClick={() => setViewMode('synthesis')}
          className="px-3 py-2 rounded-lg bg-white/10 text-white/50 hover:bg-white/15 text-sm font-medium"
        >
          Synthesis
        </button>
      </div>
      
      {/* Existing mode selector code */}
    </div>
  )
}

function SynthesisToggle({ onBack }: { onBack: () => void }) {
  return (
    <div>
      <button onClick={onBack} className="text-sm text-blue-400 hover:text-blue-300 mb-4">
        ← Back to Extract
      </button>
      <div className="text-sm text-white/40">Synthesis mode selected</div>
    </div>
  )
}
```

### Step 2: Update App Page Layout

Modify `notionclip-web/src/app/app/page.tsx` to show SynthesisMode when appropriate:

```tsx
import { SynthesisMode } from '@/components/app/SynthesisMode'

export default function AppPage() {
  const { results, mode, sourceType } = useAppStore()
  const [viewMode, setViewMode] = useState<'extract' | 'synthesis'>('extract')
  
  // ... existing code ...
  
  const showSynthesis = sourceType !== "study_session" && viewMode === 'synthesis'
  const showExtract = sourceType !== "study_session" && viewMode === 'extract'
  
  return (
    <div className="min-h-screen text-white relative overflow-hidden">
      <Navbar />
      
      <div ref={containerRef} className="pt-16 h-[calc(100vh-0px)] flex relative z-[1]">
        <aside className="...">
          <div className="flex-1 space-y-6">
            {showSynthesis ? (
              <SynthesisToggle onModeChange={setViewMode} />
            ) : (
              <>
                <ContentSourceSelector />
                <ModeSelector />
                <ProcessButton ... />
              </>
            )}
            
            <MetricStrip />
            <HistoryPanel />
            
            {/* Notion save button */}
          </div>
        </aside>
        
        <section className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-8 py-10">
            <AnimatePresence mode="wait">
              {showSynthesis ? (
                <motion.div key="synthesis" className="...">
                  <SynthesisMode />
                </motion.div>
              ) : (
                // Existing extract mode content
              )}
            </AnimatePresence>
          </div>
        </section>
      </div>
    </div>
  )
}
```

---

## Option 2: Add Synthesis to HistoryPanel

### Modify HistoryPanel to Include Synthesis Shortcut

In `notionclip-web/src/components/HistoryPanel.tsx`:

```tsx
export function HistoryPanel() {
  const [showSynthesis, setShowSynthesis] = useState(false)
  
  if (showSynthesis) {
    return <SynthesisMode />
  }
  
  return (
    <div>
      <button
        onClick={() => setShowSynthesis(true)}
        className="w-full px-4 py-2 rounded-lg bg-purple-500/20 text-purple-200 hover:bg-purple-500/30 transition text-sm font-medium mb-4"
      >
        🔗 Synthesize Sessions
      </button>
      
      {/* Existing history content */}
    </div>
  )
}
```

---

## Option 3: Floating Action Button

Add a floating button to quickly access synthesis:

```tsx
export function SynthesisFloatingButton() {
  const [open, setOpen] = useState(false)
  
  if (open) {
    return (
      <div className="fixed bottom-6 right-6 z-[200] w-96 h-96 bg-white rounded-lg shadow-2xl">
        <button
          onClick={() => setOpen(false)}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-xl"
        >
          ✕
        </button>
        <div className="p-8">
          <SynthesisMode />
        </div>
      </div>
    )
  }
  
  return (
    <button
      onClick={() => setOpen(true)}
      className="fixed bottom-6 right-6 z-[200] w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold text-2xl hover:shadow-lg transition"
      title="Synthesis Mode"
    >
      🔗
    </button>
  )
}
```

---

## Using the Components

### SessionGroupManager (Select Sessions)
```tsx
import { SessionGroupManager } from '@/components/app/SessionGroupManager'

<SessionGroupManager
  onSynthesisRequest={(sessionIds, userQuestion) => {
    // Handle synthesis request
  }}
  isLoading={false}
/>
```

### SynthesisView (Display Results)
```tsx
import { SynthesisView } from '@/components/SynthesisView'
import { SynthesisAnalysis } from '@/lib/types'

const analysis: SynthesisAnalysis = {
  common_themes: ['Theme 1', 'Theme 2'],
  unique_insights: ['Insight 1'],
  contradictions: ['Contradiction 1'],
  synthesis_summary: 'Overall summary...',
  recommended_order: [0, 1],
  knowledge_gaps: ['Gap 1']
}

<SynthesisView
  analysis={analysis}
  sourcesCount={2}
  onClose={() => {
    // Handle close
  }}
/>
```

### Full SynthesisMode (All-in-one)
```tsx
import { SynthesisMode } from '@/components/app/SynthesisMode'

<SynthesisMode />
```

---

## API Usage

### Call Synthesis from Any Component
```tsx
import { api } from '@/lib/api'
import { SynthesisResponse } from '@/lib/types'

const handleSynthesize = async () => {
  try {
    const result: SynthesisResponse = await api.synthesiseSessions(
      ['session-id-1', 'session-id-2'],
      'Optional focus question'
    )
    
    console.log('Common themes:', result.analysis.common_themes)
    console.log('Contradictions:', result.analysis.contradictions)
    console.log('Synthesis summary:', result.analysis.synthesis_summary)
  } catch (error) {
    console.error('Synthesis failed:', error)
  }
}
```

---

## Store Integration

### Access Synthesis State

Update `notionclip-web/src/lib/store.tsx` to include synthesis state:

```tsx
export type AppStore = {
  // ... existing fields ...
  
  // Synthesis
  synthesisResults: SynthesisAnalysis | null
  setSynthesisResults: (results: SynthesisAnalysis | null) => void
  
  synthesisSourcesCount: number
  setSynthesisSourcesCount: (count: number) => void
}

// In create function:
synthesisResults: null,
setSynthesisResults: (results) => set({ synthesisResults: results }),

synthesisSourcesCount: 0,
setSynthesisSourcesCount: (count) => set({ synthesisSourcesCount: count }),
```

### Use in Components
```tsx
const { synthesisResults, setSynthesisResults } = useAppStore()

// Display results
if (synthesisResults) {
  <SynthesisView
    analysis={synthesisResults}
    sourcesCount={synthesisSourcesCount}
  />
}
```

---

## Environment Setup

Ensure your `.env.local` includes:

```env
NEXT_PUBLIC_API_URL=https://notion-clips-production.up.railway.app
NEXT_PUBLIC_BACKEND_URL=https://notion-clips-production.up.railway.app
```

---

## Testing the Integration

1. **Test Session Selection:**
   - Create 2+ extraction sessions
   - In Synthesis mode, verify sessions load from localStorage
   - Test checkbox selection

2. **Test Synthesis API:**
   - Select sessions
   - Click Synthesize
   - Verify API call to `/synthesis` endpoint
   - Check response includes common_themes, contradictions, etc.

3. **Test User Question:**
   - Enter optional user question
   - Verify it's passed to backend
   - Check if synthesis focuses on the question

4. **Test Export:**
   - Click Text/Markdown/JSON export buttons
   - Verify files download correctly

5. **Test Error Handling:**
   - Try synthesis with <2 sessions (should show error)
   - Test network failure handling
   - Verify error message displays

---

## Common Issues

### Components Not Found
Ensure import paths are correct:
```tsx
// ✅ Correct
import { SynthesisMode } from '@/components/app/SynthesisMode'

// ❌ Wrong
import { SynthesisMode } from '../app/SynthesisMode'
```

### API Endpoint Not Working
Check that backend is running:
```bash
# Terminal
python backend/main.py

# Or via Railway
# Deploy backend and verify /synthesis endpoint is accessible
```

### Types Not Matching
Ensure `SynthesisResponse` interface matches backend:
```python
# backend/main.py
class SynthesisResponse(BaseModel):
    analysis: SynthesisAnalysis
    sources_count: int
    synthesis_cache_used: bool

# Frontend should match
interface SynthesisResponse {
  analysis: SynthesisAnalysis
  sources_count: number
  synthesis_cache_used: boolean
}
```

### Sessions Not Loading
Check localStorage:
```typescript
// Debug in browser console
localStorage.getItem('notionclips_sessions')
```

---

## Next Steps

1. Choose integration option (Tab, HistoryPanel, or FAB)
2. Implement chosen option
3. Test with 2+ sample sessions
4. Deploy to production
5. Gather user feedback
6. Iterate on UX based on usage patterns

---

For questions or issues, refer to the main FEATURE_COMPLETION_REPORT.md
