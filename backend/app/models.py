from __future__ import annotations

from pydantic import BaseModel, Field


class Answer(BaseModel):
    question_id: str
    option_id: str | None = None
    text: str | None = None


class StartSessionRequest(BaseModel):
    name: str | None = None


class StartSessionResponse(BaseModel):
    session_id: str
    questions: list[dict]


class BaselineRequest(BaseModel):
    session_id: str
    answers: list[Answer] = Field(min_length=5, max_length=5)


class AdaptiveQuestionResponse(BaseModel):
    session_id: str
    profile: dict
    questions: list[dict]


class RecommendationRequest(BaseModel):
    session_id: str
    baseline_answers: list[Answer] = Field(min_length=5, max_length=5)
    adaptive_answers: list[Answer] = Field(min_length=10, max_length=10)


class CareerMatch(BaseModel):
    title: str
    domain: str
    description: str
    required_skills: list[str]
    software_tools: list[str]
    affinity_score: float
    confidence: str
    why_it_fits: list[str]
    skill_gaps: list[str]
    track_type: str


class RecommendationResponse(BaseModel):
    session_id: str
    profile: dict
    top_matches: list[CareerMatch]
    growth_matches: list[CareerMatch]
    roadmap: dict
    blueprint: str


class FeedbackRequest(BaseModel):
    session_id: str
    selected_title: str
    rating: int = Field(ge=1, le=5)
    felt_right: bool
    comment: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    learning_update: dict
    discovered_patterns: list[dict]
