export type Mode = 'study' | 'work' | 'quick'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  notionEdited?: boolean
}

export interface StudyInsights {
  title: string
  core_concept: string
  formula_sheet: string[]
  key_facts: string[]
  common_mistakes: string[]
  self_test: string[]
  prerequisites: string[]
  further_reading: string[]
}

export interface WorkInsights {
  title: string
  one_liner: string
  recommendation?: string
  watch_or_skip?: string
  key_points: string[]
  tools_mentioned: string[]
  decisions_to_make: string[]
  next_actions: string[]
}
export interface ExportMarkdownResponse {
  markdown: string
  filename: string
}

export interface QuickInsights {
  title: string
  summary: string
  key_takeaways: string[]
  topics_covered: string[]
  action_items: string[]
}

export type Insights = StudyInsights | WorkInsights | QuickInsights

export interface TranscriptResponse {
  transcript: string
  duration_minutes: number
  cache_hit?: boolean
  fetch_ms?: number
}

export interface ExtractResponse {
  mode: Mode
  word_count: number
  duration_minutes?: number | null
  insights: Insights
  source_text?: string
  cache_hit?: boolean
}

export interface PushResponse {
  status: 'ok'
  page_id: string | null
}

export interface VerdictResponse {
  verdict: "Watch" | "Skim" | "Skip" | string
  why: string
  best_for: string
  relevant_moments: string[]
  what_youll_miss_if_skip: string
}

export interface SmartWatchQuickResult {
  verdict: 'watch' | 'skim' | 'skip'
  confidence: number
  reason: string
  estimated_timestamp_range: string | null
  video_id: string
  cache_hit: boolean
  stage1_ms: number
  prompt_version?: string
}

export interface SmartWatchMoment {
  timestamp_seconds: number
  timestamp_display: string
  quote: string
  relevance: string
  youtube_url: string
}

export interface SmartWatchDeepResult {
  relevant_moments: SmartWatchMoment[]
  total_relevant_moments: number
  analysis_complete: boolean
  stage2_ms: number
  skipped?: boolean
  reason?: string
  prompt_version?: string
}

export interface SmartWatchHistoryItem {
  id?: string
  created_at?: string
  session_id?: string
  user_id?: string | null
  video_id: string
  video_url: string
  video_title?: string | null
  user_question: string
  verdict?: 'watch' | 'skim' | 'skip' | string | null
  confidence?: number | null
  reason?: string | null
  estimated_timestamp_range?: string | null
  relevant_moments?: SmartWatchMoment[]
  stage1_ms?: number | null
  stage2_ms?: number | null
}

export interface SmartWatchHistoryResponse {
  items: SmartWatchHistoryItem[]
}

export interface SmartWatchDashboardResponse {
  total_analyses: number
  watch_count: number
  skim_count: number
  skip_count: number
  avg_confidence: number
  timestamp_clicks: number
  timestamps_generated: number
  avg_stage1_ms: number
  avg_stage2_ms: number
  estimated_time_saved_minutes: number
}

export interface AuthStatusResponse {
  has_token: boolean
  notion_page_id: string | null
  user_id?: string | null
}

export interface StudySource {
  source_index: number
  type: 'youtube' | 'pdf' | 'article'
  title: string
  url_or_filename: string
  extraction_status: 'pending' | 'done' | 'failed'
}

export interface SourceCitation {
  source_index: number
  timestamp_or_page: string
  quote: string
}

export interface ConceptMapping {
  concept_name: string
  best_source_index: number
  best_explanation: string
  supporting_sources: number[]
  timestamp_or_page: string
}

export interface SourceContradiction {
  topic: string
  source_a_index: number
  source_a_says: string
  source_b_index: number
  source_b_says: string
  resolution: string | null
}

export interface KnowledgeMap {
  concepts: ConceptMapping[]
  agreements: string[]
  contradictions: SourceContradiction[]
  knowledge_gaps: string[]
}

export interface KnowledgeCheckQuestion {
  id: string
  question: string
  type: 'recall' | 'application' | 'synthesis'
  difficulty: 'easy' | 'medium' | 'hard'
  answered: boolean
  user_answer: string | null
  evaluation: QuestionEvaluation | null
}

export interface TutorOutput {
  foundation: string
  foundation_source_index: number
  foundation_timestamp_or_page: string
  core_teaching: string
  core_citations: SourceCitation[]
  common_misconceptions: string[]
  knowledge_check: KnowledgeCheckQuestion[]
  next_steps: string[]
}

export interface QuestionEvaluation {
  correct: 'true' | 'false' | 'partial'
  feedback: string
  misconception: string | null
  correction: string | null
  ready_to_advance: boolean
  cited_source_index: number
}

export interface StudySession {
  study_session_id: string
  learning_goal: string
  student_level: string
  sources: StudySource[]
  knowledge_map: KnowledgeMap | null
  tutor_output: TutorOutput | null
  qa_history: object[]
  status: 'building' | 'ready' | 'complete'
  created_at: string
}

export interface CreateSessionResponse {
  study_session_id: string
  status: string
}

export interface AnswerEvaluationResponse {
  evaluation: QuestionEvaluation
  question_id: string
  session_updated: boolean
}


export interface ConceptComparison {
  concept_name: string
  consensus: string | null
  differences: string[]
  source_perspectives: Record<number, string>
}

export interface SourceSummary {
  title: string
  extraction_type: 'study' | 'work' | 'quick'
  key_points: string[]
}

export interface SynthesisAnalysis {
  common_themes: string[]
  unique_insights: string[]
  contradictions: string[]
  synthesis_summary: string
  recommended_order: number[]
  knowledge_gaps: string[]
}

export interface SynthesisResponse {
  analysis: SynthesisAnalysis
  sources_count: number
  synthesis_cache_used: boolean
}

// ============================================================================
// UNIFIED LIBRARY TYPES
// ============================================================================

export type LibraryContentType = 
  | 'youtube_study' 
  | 'youtube_work' 
  | 'youtube_quick' 
  | 'smart_watch' 
  | 'study_session'

// Content data structures for each type
export interface YouTubeStudyContent {
  core_concept?: string
  formula_sheet?: string[]
  key_facts?: string[]
  common_mistakes?: string[]
  self_test?: string[]
  prerequisites?: string[]
  further_reading?: string[]
  moments?: any[]
}

export interface YouTubeWorkContent {
  one_liner?: string
  recommendation?: string
  key_points?: string[]
  tools_mentioned?: string[]
  decisions_to_make?: string[]
  next_actions?: string[]
  moments?: any[]
}

export interface YouTubeQuickContent {
  summary?: string
  key_takeaways?: string[]
  topics_covered?: string[]
  action_items?: string[]
  moments?: any[]
}

export interface SmartWatchContent {
  verdict: 'watch' | 'skim' | 'skip'
  confidence: number
  reason: string
  estimated_timestamp_range?: string
  user_question: string
  relevant_moments?: SmartWatchMoment[]
  stage1_ms?: number
  stage2_ms?: number
}

export interface StudySessionContent {
  learning_goal: string
  student_level: string
  concepts?: any[]
  knowledge_map?: any
  tutor_output?: any
  sources?: Array<{ source_index: number; title: string; type: string }>
}

export type LibraryContentData =
  | YouTubeStudyContent
  | YouTubeWorkContent
  | YouTubeQuickContent
  | SmartWatchContent
  | StudySessionContent

export interface UnifiedLibraryItem {
  id: string
  user_id?: string | null
  session_id: string
  content_type: LibraryContentType
  title: string
  source_url?: string | null
  video_id?: string | null
  summary?: string | null
  content_data: LibraryContentData
  notion_page_id?: string | null
  tags: string[]
  created_at: string
  updated_at: string
}

export interface LibraryFilters {
  content_type?: LibraryContentType | 'all'
  search_query?: string
  date_range?: 'today' | 'week' | 'month' | 'all'
}

export interface ListLibraryResponse {
  items: UnifiedLibraryItem[]
  total: number
  has_more: boolean
}

export interface AddLibraryItemRequest {
  session_id: string
  user_id?: string | null
  content_type: LibraryContentType
  title: string
  source_url?: string | null
  video_id?: string | null
  summary?: string | null
  content_data: LibraryContentData
  notion_page_id?: string | null
  tags?: string[]
}

