from pydantic import BaseModel

from app.models import ReviewDecision


class ReviewDecisionIn(BaseModel):
    decision: ReviewDecision
    comment: str | None = None
