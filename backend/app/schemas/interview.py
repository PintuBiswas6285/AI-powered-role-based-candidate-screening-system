from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionCreateResponse(BaseModel):
    session_id: int
    target_role: str
    extracted_profile: dict[str, Any]
    first_question: "QuestionResponse"


class QuestionResponse(BaseModel):
    turn_id: int
    question: str
    topic: str
    difficulty: str
    rationale: str
    retrieved_context: list[dict[str, Any]]


class AnswerRequest(BaseModel):
    answer: str = Field(..., min_length=2)


class AnswerResponse(BaseModel):
    saved_turn_id: int
    feedback: str
    answer_score: float
    next_question: QuestionResponse | None = None
    session_complete: bool


class SessionSummaryResponse(BaseModel):
    session_id: int
    target_role: str
    status: str
    extracted_profile: dict[str, Any]
    turns: list[dict[str, Any]]
    summary: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None


class RoleResponse(BaseModel):
    roles: list[str]


SessionCreateResponse.model_rebuild()
