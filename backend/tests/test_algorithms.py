from pathlib import Path
import sys

# backend/tests/test_algorithms.py -> parents[1] is backend/, which is
# self-contained (app/ and data/ both live inside it).
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.algorithms import AdaptiveQuestionSelector, CareerDataset, CareerMatcher, LearningStore, ProfileBuilder


def baseline_answers():
    return [
        {"question_id": "b1", "option_id": "logic"},
        {"question_id": "b2", "option_id": "numbers"},
        {"question_id": "b3", "option_id": "solo"},
        {"question_id": "b4", "option_id": "systems"},
        {"question_id": "b5", "option_id": "curiosity"},
    ]


def test_profile_and_adaptive_questions():
    profile = ProfileBuilder().build(baseline_answers())
    questions = AdaptiveQuestionSelector().select(profile, count=10)
    assert "analytical" in profile["primary_traits"]
    assert len(questions) == 10
    assert len({q["id"] for q in questions}) == 10


def test_all_careers_have_real_domain_classification():
    """
    Regression test: every career must be classified into one of the
    official SOC-derived domains, not left in a generic catch-all bucket.
    This locks in the fix for the old keyword-guessing approach, which left
    ~42% of careers unclassified.
    """
    from app.algorithms import DOMAIN_TRAITS

    dataset = CareerDataset(BACKEND_ROOT / "data" / "onet_jobs.csv")
    unclassified = [c.title for c in dataset.careers if c.domain not in DOMAIN_TRAITS]
    assert not unclassified, f"{len(unclassified)} careers have no domain trait mapping: {unclassified[:5]}"


def test_matching_and_learning(tmp_path):
    dataset = CareerDataset(BACKEND_ROOT / "data" / "onet_jobs.csv")
    store = LearningStore(tmp_path / "learning.json")
    profile = ProfileBuilder().build(baseline_answers())
    adaptive = []
    for question in AdaptiveQuestionSelector().select(profile, count=10):
        adaptive.append({"question_id": question["id"], "option_id": question["options"][0]["id"]})
    result = CareerMatcher(dataset, store).match(profile, adaptive)
    assert len(result["top_matches"]) == 6
    assert result["top_matches"][0]["affinity_score"] > 0
    update = store.record(result["profile"]["primary_traits"], result["top_matches"][0]["title"], 5, True, "Good fit")
    assert update["title_weight"] > 0
