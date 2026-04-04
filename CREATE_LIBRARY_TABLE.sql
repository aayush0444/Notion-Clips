-- ============================================================================
-- UNIFIED LIBRARY DATABASE SCHEMA
-- Copy and run this in Supabase SQL Editor
-- ============================================================================

CREATE TABLE user_library (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  session_id text NOT NULL,
  content_type text NOT NULL CHECK (content_type IN (
    'youtube_study', 
    'youtube_work', 
    'youtube_quick', 
    'smart_watch', 
    'study_session'
  )),
  title text NOT NULL,
  source_url text,
  video_id text,
  summary text,
  content_data jsonb DEFAULT '{}',
  notion_page_id text,
  tags jsonb DEFAULT '[]',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Row-Level Security
ALTER TABLE user_library ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own library items" ON user_library
FOR ALL USING (
  auth.uid() = user_id OR (auth.uid() IS NULL AND session_id IS NOT NULL)
);

-- Indexes for performance
CREATE INDEX idx_user_library_user_created ON user_library(user_id, created_at DESC);
CREATE INDEX idx_user_library_session_created ON user_library(session_id, created_at DESC);
CREATE INDEX idx_user_library_content_type ON user_library(content_type);
CREATE INDEX idx_user_library_video_id ON user_library(video_id);

-- Full-text search index on title and summary
CREATE INDEX idx_user_library_search ON user_library 
USING GIN (to_tsvector('english', title || ' ' || COALESCE(summary, '')));

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_library_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_library_updated_at
BEFORE UPDATE ON user_library
FOR EACH ROW
EXECUTE FUNCTION update_user_library_updated_at();
