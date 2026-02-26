from pydantic import BaseModel, Field
from typing import List


# ─── Shared ───────────────────────────────────────────────────────────────────

class ActionItem(BaseModel):
    task: str     = Field(description="The specific action item or task")
    assignee: str = Field(description="Person responsible, or 'Team' if unclear")
    due_date: str = Field(description="Due date as YYYY-MM-DD, or 'TBD'")
    priority: str = Field(description="High, Medium, or Low")

class ActionItemList(BaseModel):
    items: List[ActionItem]


# ─── Meeting Mode ─────────────────────────────────────────────────────────────

class MeetingSummary(BaseModel):
    title: str                = Field(description="Short meeting title, max 8 words")
    summary: str              = Field(description="3-4 sentence executive summary of what was discussed")
    key_decisions: List[str]  = Field(description="Key decisions made, up to 5 points")
    next_steps: List[str]     = Field(description="Next steps agreed upon, up to 5 points")


# ─── YouTube Mode ─────────────────────────────────────────────────────────────

class VideoInsights(BaseModel):
    title: str                = Field(description="Short title describing what this video is about")
    summary: str              = Field(description="3-4 sentence summary of the video content")
    key_takeaways: List[str]  = Field(description="Most important points from the video, up to 7")
    topics_covered: List[str] = Field(description="Main topics or sections covered, up to 5")
    action_items: List[str]   = Field(description="Things the viewer should do or look into after watching, up to 5")