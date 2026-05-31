from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base

beijing_tz = timezone(timedelta(hours=8))


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pr_url = Column(String, nullable=False)
    summary = Column(Text, default="")
    risks = Column(Text, default="[]")
    suggestions = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(beijing_tz))
