import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Review
from app.schemas import ReviewRequest, ReviewResponse, HistoryItem
from app.services.review import perform_review

router = APIRouter()


@router.post("/api/review", response_model=ReviewResponse)
def create_review(req: ReviewRequest, db: Session = Depends(get_db)):
    result = perform_review(req.pr_url)
    record = Review(
        pr_url=req.pr_url,
        summary=result["summary"],
        risks=json.dumps(result["risks"]),
        suggestions=json.dumps(result["suggestions"]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ReviewResponse(
        id=record.id,
        pr_url=record.pr_url,
        summary=record.summary,
        risks=json.loads(record.risks or "[]"),
        suggestions=json.loads(record.suggestions or "[]"),
        created_at=record.created_at,
    )


@router.get("/api/history", response_model=list[HistoryItem])
def list_history(db: Session = Depends(get_db)):
    records = db.query(Review).order_by(Review.created_at.desc()).all()
    return [
        HistoryItem(
            id=r.id,
            pr_url=r.pr_url,
            summary=r.summary,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/api/review/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    record = db.query(Review).filter(Review.id == review_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse(
        id=record.id,
        pr_url=record.pr_url,
        summary=record.summary,
        risks=json.loads(record.risks or "[]"),
        suggestions=json.loads(record.suggestions or "[]"),
        created_at=record.created_at,
    )
