from __future__ import annotations

import json
import math
import os
import re
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .questions import ADAPTIVE_QUESTION_BANK, BASELINE_QUESTIONS

TRAITS = [
    "analytical",
    "visual",
    "creative",
    "social",
    "communication",
    "hands_on",
    "technical",
    "structured",
    "detail",
    "data",
    "leadership",
    "service",
    "independent",
    "experimental",
    "adaptable",
]

SKILL_TO_TRAITS = {
    "reading comprehension": ["detail", "analytical"],
    "active listening": ["communication", "social"],
    "writing": ["communication", "structured"],
    "speaking": ["communication", "social"],
    "mathematics": ["data", "analytical"],
    "science": ["analytical", "detail"],
    "critical thinking": ["analytical", "structured"],
    "active learning": ["experimental", "adaptable"],
    "learning strategies": ["structured", "adaptable"],
    "monitoring": ["detail", "structured"],
    "programming": ["technical", "analytical"],
    "systems analysis": ["technical", "analytical"],
    "operations analysis": ["technical", "structured"],
    "complex problem solving": ["analytical", "technical"],
    "social perceptiveness": ["social", "service"],
    "coordination": ["social", "leadership"],
    "persuasion": ["communication", "leadership"],
    "service orientation": ["service", "social"],
    "equipment maintenance": ["hands_on", "technical"],
    "repairing": ["hands_on", "technical"],
    "quality control analysis": ["detail", "technical"],
    "design": ["visual", "creative"],
}

# Trait associations for each official SOC major-group domain. Unlike a
# keyword classifier over titles/descriptions, every career's Domain comes
# directly from its O*NET-SOC code (see scripts/merge_onet_data.py), so this
# mapping applies to 100% of rows -- there is no "unclassified" bucket.
DOMAIN_TRAITS = {
    "Management": ["leadership", "structured", "communication"],
    "Business and Financial Operations": ["data", "structured", "analytical"],
    "Computer and Mathematical": ["technical", "analytical", "data"],
    "Architecture and Engineering": ["technical", "hands_on", "analytical"],
    "Life, Physical, and Social Science": ["analytical", "detail", "experimental"],
    "Community and Social Service": ["service", "social", "communication"],
    "Legal": ["analytical", "communication", "detail"],
    "Education, Training, and Library": ["communication", "service", "social"],
    "Arts, Design, Entertainment, and Media": ["creative", "visual", "communication"],
    "Healthcare Practitioners and Technical": ["service", "detail", "analytical"],
    "Healthcare Support": ["service", "detail", "social"],
    "Protective Service": ["structured", "hands_on", "service"],
    "Food Preparation and Serving": ["hands_on", "service", "detail"],
    "Building and Grounds Cleaning and Maintenance": ["hands_on", "detail", "structured"],
    "Personal Care and Service": ["service", "social", "communication"],
    "Sales and Related": ["communication", "leadership", "social"],
    "Office and Administrative Support": ["structured", "detail", "communication"],
    "Farming, Fishing, and Forestry": ["hands_on", "independent", "experimental"],
    "Construction and Extraction": ["hands_on", "technical", "structured"],
    "Installation, Maintenance, and Repair": ["hands_on", "technical", "detail"],
    "Production": ["hands_on", "detail", "structured"],
    "Transportation and Material Moving": ["hands_on", "structured", "independent"],
    "Military Specific": ["leadership", "structured", "hands_on"],
}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "into", "is", "it", "of", "on", "or", "that", "the", "their", "to",
    "with", "work", "workers", "using", "use", "may", "such", "other",
}


@dataclass
class Career:
    domain: str
    title: str
    description: str
    required_skills: list[str]
    software_tools: list[str]
    trait_vector: np.ndarray
    text_vector: np.ndarray


class CareerDataset:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path).fillna("")
        self.vocabulary = self._build_vocabulary(self.df)
        self.idf = self._compute_idf(self.df, self.vocabulary)
        self.careers = self._build_careers()

    def _tokenize(self, text: str) -> list[str]:
        return [t for t in re.findall(r"[a-zA-Z][a-zA-Z+#.-]*", text.lower()) if t not in STOPWORDS and len(t) > 2]

    def _row_text(self, row: pd.Series) -> str:
        return f"{row['Domain']} {row['Title']} {row['Description']} {row['Required_Skills']}"

    def _build_vocabulary(self, df: pd.DataFrame) -> list[str]:
        counts = Counter()
        for _, row in df.iterrows():
            counts.update(set(self._tokenize(self._row_text(row))))
        return [word for word, count in counts.most_common(1400) if count >= 2]

    def _compute_idf(self, df: pd.DataFrame, vocabulary: list[str]) -> dict[str, float]:
        docs = [set(self._tokenize(self._row_text(row))) for _, row in df.iterrows()]
        total = len(docs)
        return {word: math.log((1 + total) / (1 + sum(word in doc for doc in docs))) + 1 for word in vocabulary}

    def text_to_vector(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        counts = Counter(tokens)
        vector = np.array([counts[word] * self.idf.get(word, 1.0) for word in self.vocabulary], dtype=float)
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def _trait_vector_from_row(self, row: pd.Series) -> np.ndarray:
        scores = defaultdict(float)
        skills = split_items(row["Required_Skills"])
        for skill in skills:
            for trait in SKILL_TO_TRAITS.get(skill.lower(), []):
                scores[trait] += 1.8
        # Domain-derived traits are the strongest, most reliable signal since
        # Domain comes from the official SOC code, not a guess.
        for trait in DOMAIN_TRAITS.get(row["Domain"], []):
            scores[trait] += 2.2
        text = f"{row['Title']} {row['Description']}".lower()
        for trait in TRAITS:
            if trait.replace("_", " ") in text:
                scores[trait] += 1.0
        vector = np.array([scores[t] for t in TRAITS], dtype=float)
        norm = np.linalg.norm(vector)
        return vector / norm if norm else np.ones(len(TRAITS), dtype=float) / len(TRAITS)

    def _build_careers(self) -> list[Career]:
        careers = []
        for _, row in self.df.iterrows():
            careers.append(
                Career(
                    domain=row["Domain"],
                    title=row["Title"],
                    description=row["Description"],
                    required_skills=split_items(row["Required_Skills"]),
                    software_tools=split_items(row.get("Software_Tools", "")),
                    trait_vector=self._trait_vector_from_row(row),
                    text_vector=self.text_to_vector(self._row_text(row)),
                )
            )
        return careers


class ProfileBuilder:
    """Algorithm 1: convert the first 5 psychology answers into a trait profile."""

    def build(self, answers: Iterable[dict]) -> dict:
        scores = defaultdict(float)
        explanations = []
        answer_map = {a["question_id"]: a for a in answers}
        for question in BASELINE_QUESTIONS:
            selected = answer_map.get(question["id"], {}).get("option_id")
            option = next((o for o in question["options"] if o["id"] == selected), None)
            if not option:
                continue
            for trait, weight in option["weights"].items():
                scores[trait] += weight
            explanations.append({"question": question["text"], "answer": option["label"], "trait": question["trait"]})
        normalized = normalize_scores(scores)
        primary = [trait for trait, _ in sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:5]]
        return {
            "scores": normalized,
            "primary_traits": primary,
            "summary": profile_summary(primary),
            "evidence": explanations,
        }


class AdaptiveQuestionSelector:
    """Algorithm 2A: choose 10 simple questions based on the baseline profile."""

    def select(self, profile: dict, count: int = 10) -> list[dict]:
        trait_scores = profile["scores"]
        ranked = []
        for question in ADAPTIVE_QUESTION_BANK:
            coverage = sum(trait_scores.get(tag, 0) for tag in question["tags"])
            diversity = len(set(question["tags"]) & set(profile["primary_traits"]))
            ranked.append((coverage + diversity * 0.08, question))
        selected = [q for _, q in sorted(ranked, key=lambda x: x[0], reverse=True)[:count]]
        if len(selected) < count:
            selected_ids = {q["id"] for q in selected}
            selected.extend(q for q in ADAPTIVE_QUESTION_BANK if q["id"] not in selected_ids)
        return selected[:count]


class CareerMatcher:
    """Algorithm 2B: hybrid affinity matching over traits, domain, and career text."""

    def __init__(self, dataset: CareerDataset, learning_store: "LearningStore"):
        self.dataset = dataset
        self.learning_store = learning_store

    def match(self, baseline_profile: dict, adaptive_answers: Iterable[dict], top_n: int = 6) -> dict:
        user_scores = defaultdict(float, baseline_profile["scores"])
        answer_text = []
        option_lookup = {q["id"]: q for q in ADAPTIVE_QUESTION_BANK}
        for answer in adaptive_answers:
            question = option_lookup.get(answer["question_id"])
            if not question:
                continue
            option = next((o for o in question["options"] if o["id"] == answer.get("option_id")), None)
            if option:
                answer_text.append(f"{question['text']} {option['label']}")
                for trait, weight in option["weights"].items():
                    user_scores[trait] += weight
            if answer.get("text"):
                answer_text.append(answer["text"])
        trait_vector = vectorize_traits(user_scores)
        text_vector = self.dataset.text_to_vector(" ".join(answer_text + baseline_profile["primary_traits"]))
        learned = self.learning_store.profile_adjustments(baseline_profile["primary_traits"])

        scored = []
        for career in self.dataset.careers:
            trait_score = cosine(trait_vector, career.trait_vector)
            text_score = cosine(text_vector, career.text_vector)
            domain_score = domain_fit_score(user_scores, career.domain)
            title_score = title_fit_score(user_scores, career.title)
            learning_bonus = learned.get(career.title, 0.0)
            score = max(0.0, min(1.0, 0.46 * trait_score + 0.20 * text_score + 0.22 * domain_score + 0.07 * title_score + learning_bonus))
            scored.append((score, career, trait_score, text_score, learning_bonus))

        scored.sort(key=lambda x: x[0], reverse=True)
        safe = [self._format_match(*item, track_type="safe") for item in scored[:top_n]]
        top_domains = {item[1].domain for item in scored[:3]}
        growth_pool = [item for item in scored if item[1].domain not in top_domains and item[0] >= 0.24]
        growth = [self._format_match(*item, track_type="growth") for item in growth_pool[:3]]
        return {
            "profile": {
                **baseline_profile,
                "scores": normalize_scores(user_scores),
                "primary_traits": [t for t, _ in sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:5]],
            },
            "top_matches": safe,
            "growth_matches": growth,
        }

    def _format_match(self, score: float, career: Career, trait_score: float, text_score: float, learning_bonus: float, track_type: str) -> dict:
        return {
            "title": career.title,
            "domain": career.domain,
            "description": career.description,
            "required_skills": career.required_skills[:8],
            "software_tools": career.software_tools[:6],
            "affinity_score": round(score * 100, 1),
            "confidence": confidence_label(score),
            "why_it_fits": [
                f"Trait alignment score: {round(trait_score * 100)}%",
                f"Answer-to-job text similarity: {round(text_score * 100)}%",
                "Past feedback slightly improved this recommendation." if learning_bonus > 0 else "Matched using current answers and O*NET role data.",
            ],
            "skill_gaps": infer_skill_gaps(career.required_skills),
            "track_type": track_type,
        }


class LearningStore:
    """Algorithm 3: persistent feedback learning and pattern mining."""

    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"events": [], "weights": {}}, indent=2), encoding="utf-8")

    def read(self) -> dict:
        with self.lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def record(self, profile_traits: list[str], selected_title: str, rating: int, felt_right: bool, comment: str | None) -> dict:
        with self.lock:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            key = "|".join(sorted(profile_traits[:4]))
            weights = data.setdefault("weights", {})
            title_weights = weights.setdefault(key, {})
            delta = (rating - 3) * 0.015
            if felt_right:
                delta += 0.02
            title_weights[selected_title] = round(max(-0.12, min(0.12, title_weights.get(selected_title, 0.0) + delta)), 4)
            data.setdefault("events", []).append(
                {
                    "profile_key": key,
                    "traits": profile_traits,
                    "title": selected_title,
                    "rating": rating,
                    "felt_right": felt_right,
                    "comment": comment or "",
                }
            )
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return {"profile_key": key, "title_weight": title_weights[selected_title], "delta": round(delta, 4)}

    def profile_adjustments(self, profile_traits: list[str]) -> dict[str, float]:
        data = self.read()
        key = "|".join(sorted(profile_traits[:4]))
        return data.get("weights", {}).get(key, {})

    def patterns(self, min_events: int = 3) -> list[dict]:
        data = self.read()
        grouped = defaultdict(list)
        for event in data.get("events", []):
            grouped[event["profile_key"]].append(event)
        patterns = []
        for key, events in grouped.items():
            if len(events) < min_events:
                continue
            avg_by_title = defaultdict(list)
            for event in events:
                avg_by_title[event["title"]].append(event["rating"])
            best_title, ratings = max(avg_by_title.items(), key=lambda item: sum(item[1]) / len(item[1]))
            patterns.append(
                {
                    "profile_key": key,
                    "sample_size": len(events),
                    "strongest_career": best_title,
                    "average_rating": round(sum(ratings) / len(ratings), 2),
                }
            )
        return sorted(patterns, key=lambda p: (p["sample_size"], p["average_rating"]), reverse=True)


def split_items(raw: str) -> list[str]:
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def normalize_scores(scores: dict) -> dict:
    total = sum(max(0.0, float(v)) for v in scores.values()) or 1.0
    return {trait: round(max(0.0, float(scores.get(trait, 0))) / total, 4) for trait in TRAITS}


def vectorize_traits(scores: dict) -> np.ndarray:
    vector = np.array([float(scores.get(t, 0)) for t in TRAITS], dtype=float)
    norm = np.linalg.norm(vector)
    return vector / norm if norm else np.ones(len(TRAITS), dtype=float) / len(TRAITS)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def profile_summary(traits: list[str]) -> str:
    labels = {
        "analytical": "logic-first problem solver",
        "visual": "visual-spatial thinker",
        "creative": "idea-driven creator",
        "social": "people-centered collaborator",
        "technical": "systems and technology learner",
        "hands_on": "practical hands-on learner",
        "data": "pattern and data explorer",
        "leadership": "organizer and decision maker",
    }
    return ", ".join(labels.get(t, t.replace("_", " ")) for t in traits[:3])


def confidence_label(score: float) -> str:
    if score >= 0.72:
        return "High"
    if score >= 0.5:
        return "Medium"
    return "Exploratory"


def infer_skill_gaps(required_skills: list[str]) -> list[str]:
    """
    Returns the required skills most worth prioritizing first.

    NOTE ON SCOPE: this ranks the CAREER's own required skills by general
    learning priority (foundational skills first). It does not yet compare
    against skills the specific user already has -- the assessment doesn't
    currently collect that. A true personalized gap analysis would need a
    "skills you already have" question and diff it against required_skills.
    Flagged here explicitly so this isn't mistaken for more than it is.
    """
    priority_order = [
        "Critical Thinking", "Active Learning", "Reading Comprehension", "Speaking",
        "Writing", "Mathematics", "Monitoring", "Active Listening", "Science", "Learning Strategies",
    ]
    ranked = sorted(required_skills, key=lambda s: priority_order.index(s) if s in priority_order else len(priority_order))
    return ranked[:3]


def domain_fit_score(user_scores: dict, domain: str) -> float:
    traits = DOMAIN_TRAITS.get(domain, ["adaptable", "structured"])
    total = sum(float(user_scores.get(trait, 0)) for trait in traits)
    max_possible = sum(max(float(v), 0.0) for v in user_scores.values()) or 1.0
    return min(1.0, (total / max_possible) * 2.8)


def title_fit_score(user_scores: dict, title: str) -> float:
    lower = title.lower()
    score = 0.0
    if user_scores.get("data", 0) and any(k in lower for k in ["data", "analyst", "statistic", "database"]):
        score += 0.55
    if user_scores.get("technical", 0) and any(k in lower for k in ["software", "developer", "programmer", "computer", "systems"]):
        score += 0.45
    if user_scores.get("creative", 0) and any(k in lower for k in ["design", "artist", "writer", "media"]):
        score += 0.45
    if user_scores.get("service", 0) and any(k in lower for k in ["teacher", "counsel", "health", "therap"]):
        score += 0.35
    if "all other" in lower:
        score -= 0.2
    return max(0.0, min(1.0, score))


def build_roadmap(matches: list[dict]) -> dict:
    first = matches[0] if matches else {"title": "Career exploration", "skill_gaps": []}
    skills = first.get("skill_gaps", [])[:3]
    return {
        "30_days": [f"Learn basics of {skill}" for skill in skills] or ["Complete one beginner career exploration module"],
        "60_days": [f"Build a small project using {skill}" for skill in skills] or ["Interview two people in matching careers"],
        "90_days": [f"Create portfolio proof for {first['title']}"] + [f"Practice explaining {skill}" for skill in skills[:2]],
        "free_resources": ["NPTEL/SWAYAM", "Google Skillshop", "freeCodeCamp", "Kaggle Learn", "O*NET career pages"],
    }


def generate_blueprint(profile: dict, matches: list[dict], roadmap: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = (
                "Write a concise student career blueprint in simple Indian English. "
                f"Profile: {profile}. Matches: {matches[:3]}. Roadmap: {roadmap}."
            )
            return model.generate_content(prompt).text
        except Exception:
            pass
    titles = ", ".join(m["title"] for m in matches[:3])
    return (
        f"Your profile looks like a {profile.get('summary', 'balanced learner')}. "
        f"Your strongest career paths are {titles}. Start with the 30-day plan, build one small proof project, "
        "then use feedback to refine your direction."
    )
