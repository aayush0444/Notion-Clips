export type Mode = 'study' | 'work' | 'quick'

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
  watch_or_skip: string
  key_points: string[]
  tools_mentioned: string[]
  decisions_to_make: string[]
  next_actions: string[]
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
}

export interface ExtractResponse {
  mode: Mode
  word_count: number
  duration_minutes?: number | null
  insights: Insights
}

export interface PushResponse {
  status: 'ok'
  page_id: string | null
}

export interface AuthStatusResponse {
  has_token: boolean
  notion_page_id: string | null
}
