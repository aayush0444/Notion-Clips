"""
Unified Library API - Stores all user content across all modes

SQL to run in Supabase SQL editor:

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
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/library", tags=["library"])


# Request/Response Models
class AddLibraryItemRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    content_type: str
    title: str
    source_url: Optional[str] = None
    video_id: Optional[str] = None
    summary: Optional[str] = None
    content_data: Dict[str, Any] = {}
    notion_page_id: Optional[str] = None
    tags: List[str] = []


class LibraryItemResponse(BaseModel):
    id: str
    user_id: Optional[str]
    session_id: str
    content_type: str
    title: str
    source_url: Optional[str]
    video_id: Optional[str]
    summary: Optional[str]
    content_data: Dict[str, Any]
    notion_page_id: Optional[str]
    tags: List[str]
    created_at: str
    updated_at: str


class ListLibraryRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    content_type: Optional[str] = None  # Filter by type
    limit: int = 50
    offset: int = 0


class ListLibraryResponse(BaseModel):
    items: List[LibraryItemResponse]
    total: int
    has_more: bool


class SearchLibraryRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    query: str
    content_type: Optional[str] = None
    limit: int = 50


class DeleteLibraryItemRequest(BaseModel):
    item_id: str
    session_id: str
    user_id: Optional[str] = None


# API Endpoints
@router.post("/add")
async def add_library_item(req: AddLibraryItemRequest) -> LibraryItemResponse:
    """Add an item to the user's library"""
    from backend.supabase_client import save_library_item
    
    try:
        item = save_library_item(
            session_id=req.session_id,
            user_id=req.user_id,
            content_type=req.content_type,
            title=req.title,
            source_url=req.source_url,
            video_id=req.video_id,
            summary=req.summary,
            content_data=req.content_data,
            notion_page_id=req.notion_page_id,
            tags=req.tags,
        )
        return LibraryItemResponse(**item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add library item: {str(e)}")


@router.post("/list")
async def list_library(req: ListLibraryRequest) -> ListLibraryResponse:
    """List library items with optional filtering"""
    from backend.supabase_client import list_library_items
    
    try:
        result = list_library_items(
            session_id=req.session_id,
            user_id=req.user_id,
            content_type=req.content_type,
            limit=req.limit,
            offset=req.offset,
        )
        
        items = [LibraryItemResponse(**item) for item in result["items"]]
        
        return ListLibraryResponse(
            items=items,
            total=result["total"],
            has_more=result["has_more"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list library: {str(e)}")


@router.get("/{item_id}")
async def get_library_item(
    item_id: str,
    session_id: str,
    user_id: Optional[str] = None,
) -> LibraryItemResponse:
    """Get a single library item by ID"""
    from backend.supabase_client import get_library_item
    
    try:
        item = get_library_item(item_id=item_id, session_id=session_id, user_id=user_id)
        if not item:
            raise HTTPException(status_code=404, detail="Library item not found")
        return LibraryItemResponse(**item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get library item: {str(e)}")


@router.post("/search")
async def search_library(req: SearchLibraryRequest) -> ListLibraryResponse:
    """Search library items by query"""
    from backend.supabase_client import search_library_items
    
    try:
        result = search_library_items(
            session_id=req.session_id,
            user_id=req.user_id,
            query=req.query,
            content_type=req.content_type,
            limit=req.limit,
        )
        
        items = [LibraryItemResponse(**item) for item in result["items"]]
        
        return ListLibraryResponse(
            items=items,
            total=result["total"],
            has_more=False,  # Search doesn't paginate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search library: {str(e)}")


@router.delete("/{item_id}")
async def delete_library_item(
    item_id: str,
    session_id: str,
    user_id: Optional[str] = None,
) -> Dict[str, str]:
    """Delete a library item"""
    from backend.supabase_client import delete_library_item
    
    try:
        success = delete_library_item(item_id=item_id, session_id=session_id, user_id=user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Library item not found")
        return {"message": "Library item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete library item: {str(e)}")
