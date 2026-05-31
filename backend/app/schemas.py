from datetime import datetime
from pydantic import BaseModel


class ReviewRequest(BaseModel):
    pr_url: str


class StatsSchema(BaseModel):
    file_count: int = 0
    additions: int = 0
    deletions: int = 0


class ReviewResponse(BaseModel):
    id: int
    pr_url: str
    summary: str
    risks: list
    suggestions: list
    stats: StatsSchema = StatsSchema()
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    id: int
    pr_url: str
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True
