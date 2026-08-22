const api = window.API_BASE_URL || "";
let sessionId = null;
let baselineQuestions = [];
let adaptiveQuestions = [];
let baselineAnswers = [];
let lastResults = null;

const $ = (id) => document.getElementById(id);

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    tab.classList.add("active");
    $(`${tab.dataset.view}-view`).classList.add("active");
    if (tab.dataset.view === "analytics") loadAnalytics();
  });
});

$("start-btn").addEventListener("click", startSession);
$("baseline-submit").addEventListener("click", submitBaseline);
$("recommend-btn").addEventListener("click", submitRecommendations);
$("feedback-btn").addEventListener("click", submitFeedback);
$("refresh-analytics").addEventListener("click", loadAnalytics);
$("feedback-rating").addEventListener("input", (event) => {
  $("rating-value").textContent = event.target.value;
});

loadHealth();

async function loadHealth() {
  try {
    const health = await getJson("/api/health");
    $("career-count").textContent = `${health.careers_loaded} O*NET careers loaded`;
  } catch {
    $("career-count").textContent = "Backend unreachable or waking up (free-tier hosts sleep when idle) - retrying may help";
  }
}

async function startSession() {
  const data = await postJson("/api/session", { name: "Student" });
  sessionId = data.session_id;
  baselineQuestions = data.questions;
  renderQuestions($("baseline-form"), baselineQuestions, "baseline");
  $("baseline-submit").classList.remove("hidden");
}

async function submitBaseline() {
  baselineAnswers = collectAnswers(baselineQuestions, "baseline");
  if (baselineAnswers.length !== baselineQuestions.length) return alert("Please answer all 5 questions.");
  const data = await postJson("/api/adaptive-questions", { session_id: sessionId, answers: baselineAnswers });
  adaptiveQuestions = data.questions;
  $("profile-summary").textContent = `Detected profile: ${data.profile.summary}. The next 10 questions were selected from this profile.`;
  renderQuestions($("adaptive-form"), adaptiveQuestions, "adaptive");
  $("adaptive-panel").classList.remove("hidden");
  setStep("step-adaptive");
}

async function submitRecommendations() {
  const adaptiveAnswers = collectAnswers(adaptiveQuestions, "adaptive");
  if (adaptiveAnswers.length !== adaptiveQuestions.length) return alert("Please answer all 10 adaptive questions.");
  lastResults = await postJson("/api/recommendations", {
    session_id: sessionId,
    baseline_answers: baselineAnswers,
    adaptive_answers: adaptiveAnswers,
  });
  renderResults(lastResults);
  $("results-panel").classList.remove("hidden");
  $("feedback-panel").classList.remove("hidden");
  setStep("step-results");
}

async function submitFeedback() {
  const payload = {
    session_id: sessionId,
    selected_title: $("feedback-title").value,
    rating: Number($("feedback-rating").value),
    felt_right: $("felt-right").checked,
    comment: $("feedback-comment").value,
  };
  const data = await postJson("/api/feedback", payload);
  $("feedback-status").textContent = `Learning updated: ${data.learning_update.profile_key} -> ${data.learning_update.title_weight}`;
  setStep("step-learning");
}

function renderQuestions(container, questions, group) {
  container.innerHTML = "";
  questions.forEach((question, index) => {
    const fieldset = document.createElement("fieldset");
    fieldset.className = "question";
    const legend = document.createElement("legend");
    legend.textContent = `${index + 1}. ${question.text}`;
    fieldset.appendChild(legend);
    const options = document.createElement("div");
    options.className = "options";
    question.options.forEach((option) => {
      const id = `${group}-${question.id}-${option.id}`;
      const label = document.createElement("label");
      label.className = "option";
      label.innerHTML = `<input type="radio" name="${group}-${question.id}" value="${option.id}" id="${id}"> <span>${option.label}</span>`;
      options.appendChild(label);
    });
    fieldset.appendChild(options);
    container.appendChild(fieldset);
  });
}

function collectAnswers(questions, group) {
  return questions.map((question) => {
    const checked = document.querySelector(`input[name="${group}-${question.id}"]:checked`);
    return checked ? { question_id: question.id, option_id: checked.value } : null;
  }).filter(Boolean);
}

function renderResults(data) {
  $("blueprint").textContent = data.blueprint;
  renderCards($("safe-results"), data.top_matches);
  renderCards($("growth-results"), data.growth_matches);
  renderRoadmap(data.roadmap);
  const select = $("feedback-title");
  select.innerHTML = "";
  [...data.top_matches, ...data.growth_matches].forEach((match) => {
    const option = document.createElement("option");
    option.value = match.title;
    option.textContent = match.title;
    select.appendChild(option);
  });
}

function renderCards(container, matches) {
  container.innerHTML = "";
  matches.forEach((match) => {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <p class="score">${match.affinity_score}% affinity · ${match.confidence}</p>
      <h3>${match.title}</h3>
      <p class="muted">${match.domain}</p>
      <p>${match.description}</p>
      <strong>Why it fits</strong>
      <ul>${match.why_it_fits.map((item) => `<li>${item}</li>`).join("")}</ul>
      ${match.skill_gaps && match.skill_gaps.length ? `
      <strong>Skill gaps</strong>
      <ul>${match.skill_gaps.map((item) => `<li>${item}</li>`).join("")}</ul>` : ""}
      ${match.software_tools && match.software_tools.length ? `
      <strong>Tools used in this career</strong>
      <ul>${match.software_tools.map((item) => `<li>${item}</li>`).join("")}</ul>` : ""}
    `;
    container.appendChild(card);
  });
}

function renderRoadmap(roadmap) {
  $("roadmap").innerHTML = Object.entries(roadmap).map(([key, items]) => `
    <div>
      <strong>${key.replaceAll("_", " ")}</strong>
      <ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>
    </div>
  `).join("");
}

async function loadAnalytics() {
  const data = await getJson("/api/analytics");
  $("analytics").innerHTML = `
    <div class="metric"><strong>Total feedback</strong><p>${data.total_feedback}</p></div>
    <div class="metric"><strong>Average rating</strong><p>${data.average_rating}</p></div>
    <div class="metric"><strong>Popular careers</strong><ul>${data.popular_careers.map((c) => `<li>${c.title}: ${c.count}</li>`).join("") || "<li>No feedback yet</li>"}</ul></div>
    <div class="metric"><strong>Discovered patterns</strong><ul>${data.patterns.map((p) => `<li>${p.profile_key}: ${p.strongest_career} (${p.average_rating})</li>`).join("") || "<li>Need at least 3 feedback events per profile</li>"}</ul></div>
  `;
}

function setStep(activeId) {
  document.querySelectorAll(".step").forEach((step) => step.classList.remove("active"));
  $(activeId).classList.add("active");
}

async function getJson(path) {
  const response = await fetch(api + path);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

async function postJson(path, body) {
  const response = await fetch(api + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
