from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .algorithms import (
    AdaptiveQuestionSelector,
    CareerDataset,
    CareerMatcher,
    LearningStore,
    ProfileBuilder,
    build_roadmap,
    generate_blueprint,
)
from .models import (
    AdaptiveQuestionResponse,
    BaselineRequest,
    FeedbackRequest,
    FeedbackResponse,
    RecommendationRequest,
    RecommendationResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from .questions import BASELINE_QUESTIONS

# Backend is fully self-contained: data/ lives inside backend/, not in a
# sibling folder. This is intentional -- it lets Render deploy the backend/
# folder on its own (Root Directory = backend) with no dependency on the
# rest of the repo, since the frontend is deployed separately on Vercel.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = BACKEND_ROOT / "data" / "onet_jobs.csv"
LEARNING_PATH = BACKEND_ROOT / "storage" / "learning.json"

# CORS: set ALLOWED_ORIGINS on Render to your Vercel URL(s), comma-separated,
# e.g. "https://your-app.vercel.app,https://your-app-git-main-you.vercel.app"
# Falls back to "*" (any origin) if unset, which is fine for early testing
# but should be tightened before sharing the app widely.
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()] or ["*"]

app = FastAPI(
    title="AI Career Affinity Navigator API",
    description="Adaptive 5+10 question career guidance engine using real O*NET data.",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

dataset = CareerDataset(DATA_PATH)
learning_store = LearningStore(LEARNING_PATH)
profile_builder = ProfileBuilder()
question_selector = AdaptiveQuestionSelector()
matcher = CareerMatcher(dataset, learning_store)
sessions: dict[str, dict] = {}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "careers_loaded": len(dataset.careers), "feedback_events": len(learning_store.read()["events"])}


@app.post("/api/session", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest) -> dict:
    session_id = str(uuid4())
    sessions[session_id] = {"name": payload.name, "baseline": None, "adaptive": None, "recommendations": None}
    return {"session_id": session_id, "questions": BASELINE_QUESTIONS}


@app.post("/api/adaptive-questions", response_model=AdaptiveQuestionResponse)
def adaptive_questions(payload: BaselineRequest) -> dict:
    ensure_session(payload.session_id)
    answer_dicts = [answer.model_dump() for answer in payload.answers]
    profile = profile_builder.build(answer_dicts)
    questions = question_selector.select(profile, count=10)
    sessions[payload.session_id]["baseline"] = {"answers": answer_dicts, "profile": profile}
    sessions[payload.session_id]["adaptive"] = questions
    return {"session_id": payload.session_id, "profile": profile, "questions": questions}


@app.post("/api/recommendations", response_model=RecommendationResponse)
def recommendations(payload: RecommendationRequest) -> dict:
    ensure_session(payload.session_id)
    baseline_answers = [answer.model_dump() for answer in payload.baseline_answers]
    adaptive_answers = [answer.model_dump() for answer in payload.adaptive_answers]
    profile = profile_builder.build(baseline_answers)
    result = matcher.match(profile, adaptive_answers)
    roadmap = build_roadmap(result["top_matches"])
    blueprint = generate_blueprint(result["profile"], result["top_matches"], roadmap)
    response = {
        "session_id": payload.session_id,
        "profile": result["profile"],
        "top_matches": result["top_matches"],
        "growth_matches": result["growth_matches"],
        "roadmap": roadmap,
        "blueprint": blueprint,
    }
    sessions[payload.session_id]["recommendations"] = response
    return response


@app.post("/api/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackRequest) -> dict:
    ensure_session(payload.session_id)
    session = sessions[payload.session_id]
    recommendation = session.get("recommendations")
    if not recommendation:
        raise HTTPException(status_code=400, detail="Generate recommendations before feedback.")
    traits = recommendation["profile"]["primary_traits"]
    update = learning_store.record(traits, payload.selected_title, payload.rating, payload.felt_right, payload.comment)
    return {"status": "learned", "learning_update": update, "discovered_patterns": learning_store.patterns()}


@app.get("/api/analytics")
def analytics() -> dict:
    data = learning_store.read()
    events = data.get("events", [])
    title_counts: dict[str, int] = {}
    total_rating = 0
    for event in events:
        title_counts[event["title"]] = title_counts.get(event["title"], 0) + 1
        total_rating += event["rating"]
    popular = sorted(title_counts.items(), key=lambda item: item[1], reverse=True)[:8]
    return {
        "total_feedback": len(events),
        "average_rating": round(total_rating / len(events), 2) if events else 0,
        "popular_careers": [{"title": title, "count": count} for title, count in popular],
        "patterns": learning_store.patterns(),
    }


def ensure_session(session_id: str) -> None:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Start a new session.")
