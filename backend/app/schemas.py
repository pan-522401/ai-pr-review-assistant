from datetime import datetime
from pydantic import BaseModel


class ReviewRequest(BaseModel):
    pr_url: str


class ReviewResponse(BaseModel):
    id: int
    pr_url: str
    summary: str
    risks: list
    suggestions: list
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
