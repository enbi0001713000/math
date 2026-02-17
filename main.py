from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="High School Math Learning API", version="1.0.0")

StepType = Literal["intro", "example", "practice", "test"]
QuestionType = Literal["numeric_input", "dropdown"]


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    displayName: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OAuthRequest(BaseModel):
    provider: Literal["google", "apple"]
    idToken: str


class AnswerRequest(BaseModel):
    answer: str
    elapsedMs: int | None = None


class TestAnswerItem(BaseModel):
    questionId: str
    answer: str


class TestSubmitRequest(BaseModel):
    answers: list[TestAnswerItem]


class ReviewSubmitRequest(BaseModel):
    reviewSetId: str
    answers: list[TestAnswerItem]


class AdminUnitUpsertRequest(BaseModel):
    subjectCode: Literal["1A", "2B", "2C"]
    title: str
    description: str = ""
    isPublished: bool = True


class AdminStepUpsertRequest(BaseModel):
    stepType: StepType
    stepOrder: int = Field(ge=1, le=4)
    title: str
    contentMarkdown: str


class AdminQuestionUpsertRequest(BaseModel):
    unitId: str
    stepType: Literal["practice", "test", "review"]
    questionType: QuestionType
    body: str
    choices: list[dict] | None = None
    correctAnswer: str
    explanation: str = ""


class AdminHintUpsertRequest(BaseModel):
    hintLevel: int = Field(ge=1)
    hintText: str


class AdminReviewSetUpsertRequest(BaseModel):
    unitId: str
    questionIds: list[str] = Field(min_length=5, max_length=5)
    requiredCorrectCount: int = Field(default=4, ge=1, le=5)


class AdminBadgeUpsertRequest(BaseModel):
    badgeType: Literal["first_completion", "unit_completion", "streak"]
    name: str
    conditionValue: int | None = None


SUBJECTS = [
    {"id": "sub_1a", "code": "1A", "name": "数学1A", "sortOrder": 1},
    {"id": "sub_2b", "code": "2B", "name": "数学2B", "sortOrder": 2},
    {"id": "sub_2c", "code": "2C", "name": "数学2C", "sortOrder": 3},
]

users: dict[str, dict] = {}
users_by_email: dict[str, str] = {}
units: dict[str, dict] = {
    "unit_1": {
        "unitId": "unit_1",
        "subjectCode": "1A",
        "title": "数と式",
        "description": "文字式と計算",
        "isPublished": True,
        "steps": [
            {"stepOrder": 1, "stepType": "intro", "title": "導入", "contentMarkdown": "導入"},
            {"stepOrder": 2, "stepType": "example", "title": "例題", "contentMarkdown": "例題"},
            {"stepOrder": 3, "stepType": "practice", "title": "演習", "contentMarkdown": "演習"},
            {"stepOrder": 4, "stepType": "test", "title": "確認テスト", "contentMarkdown": "確認"},
        ],
    }
}
questions: dict[str, dict] = {
    "q_pr_1": {
        "questionId": "q_pr_1",
        "unitId": "unit_1",
        "stepType": "practice",
        "questionType": "numeric_input",
        "body": "2+3= ?",
        "choices": [],
        "correctAnswer": "5",
        "explanation": "2と3を足すと5",
    },
    "q_t_1": {
        "questionId": "q_t_1",
        "unitId": "unit_1",
        "stepType": "test",
        "questionType": "dropdown",
        "body": "x^2-5x+6=0 の解",
        "choices": [{"key": "A", "text": "2,3"}, {"key": "B", "text": "1,6"}],
        "correctAnswer": "A",
        "explanation": "(x-2)(x-3)=0",
    },
    "q_r_1": {
        "questionId": "q_r_1",
        "unitId": "unit_1",
        "stepType": "review",
        "questionType": "numeric_input",
        "body": "10-3=?",
        "choices": [],
        "correctAnswer": "7",
        "explanation": "10から3を引く",
    },
    "q_r_2": {"questionId": "q_r_2", "unitId": "unit_1", "stepType": "review", "questionType": "numeric_input", "body": "8-2=?", "choices": [], "correctAnswer": "6", "explanation": ""},
    "q_r_3": {"questionId": "q_r_3", "unitId": "unit_1", "stepType": "review", "questionType": "numeric_input", "body": "6-1=?", "choices": [], "correctAnswer": "5", "explanation": ""},
    "q_r_4": {"questionId": "q_r_4", "unitId": "unit_1", "stepType": "review", "questionType": "numeric_input", "body": "4+4=?", "choices": [], "correctAnswer": "8", "explanation": ""},
    "q_r_5": {"questionId": "q_r_5", "unitId": "unit_1", "stepType": "review", "questionType": "numeric_input", "body": "9-4=?", "choices": [], "correctAnswer": "5", "explanation": ""},
}
hints: dict[str, list[dict]] = {
    "q_t_1": [{"hintLevel": 1, "hintText": "積が6、和が-5"}, {"hintLevel": 2, "hintText": "2と3"}]
}
review_sets: dict[str, dict] = {
    "rs_1": {
        "reviewSetId": "rs_1",
        "unitId": "unit_1",
        "questionIds": ["q_r_1", "q_r_2", "q_r_3", "q_r_4", "q_r_5"],
        "requiredCorrectCount": 4,
    }
}
progress: dict[tuple[str, str], dict] = {}
badges_catalog: list[dict] = [
    {"badgeId": "b_first", "badgeType": "first_completion", "name": "初回完了", "conditionValue": None},
    {"badgeId": "b_streak_3", "badgeType": "streak", "name": "3日継続", "conditionValue": 3},
]
user_badges: dict[str, list[dict]] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ok(data):
    return {"success": True, "data": data, "error": None}


def _unit_or_404(unit_id: str) -> dict:
    unit = units.get(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="unit not found")
    return unit


def _question_or_404(question_id: str) -> dict:
    q = questions.get(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="question not found")
    return q


@app.post("/api/v1/auth/signup")
def signup(req: SignupRequest):
    if req.email in users_by_email:
        raise HTTPException(status_code=400, detail="email already exists")
    user_id = f"u_{uuid.uuid4().hex[:8]}"
    user = {"id": user_id, "email": req.email, "displayName": req.displayName}
    users[user_id] = user
    users_by_email[req.email] = user_id
    return ok({"user": user, "token": f"token-{user_id}"})


@app.post("/api/v1/auth/login")
def login(req: LoginRequest):
    user_id = users_by_email.get(req.email)
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return ok({"user": users[user_id], "token": f"token-{user_id}"})


@app.post("/api/v1/auth/oauth")
def oauth(req: OAuthRequest):
    user_id = f"u_{uuid.uuid4().hex[:8]}"
    user = {"id": user_id, "email": None, "displayName": f"{req.provider}_user"}
    users[user_id] = user
    return ok({"user": user, "token": f"token-{user_id}"})


@app.post("/api/v1/auth/logout")
def logout():
    return ok({})


@app.get("/api/v1/auth/me")
def me():
    sample_user = next(iter(users.values()), {"id": "u_demo", "email": "demo@example.com", "displayName": "demo"})
    return ok({"user": sample_user})


@app.get("/api/v1/home")
def home():
    recs = random.sample(list(questions.values()), k=min(1, len(questions)))
    mapped = [{k: q.get(k) for k in ["questionId", "unitId", "questionType", "body"]} | {"unitTitle": units[q["unitId"]]["title"]} for q in recs]
    return ok({"todayRecommendation": mapped, "streakDays": 0, "inProgressUnit": None, "latestBadges": []})


@app.get("/api/v1/recommendations/today")
def recommendations_today(count: int = 3):
    count = max(1, min(10, count))
    all_q = list(questions.values())
    picks = random.sample(all_q, k=min(count, len(all_q)))
    items = [
        {
            "questionId": q["questionId"],
            "unitId": q["unitId"],
            "unitTitle": units[q["unitId"]]["title"],
            "questionType": q["questionType"],
            "body": q["body"],
        }
        for q in picks
    ]
    return ok({"source": "random", "items": items})


@app.get("/api/v1/subjects")
def get_subjects():
    return ok(SUBJECTS)


@app.get("/api/v1/units")
def get_units(subject: str | None = None):
    arr = []
    for u in units.values():
        if subject and u["subjectCode"] != subject:
            continue
        arr.append({"unitId": u["unitId"], "subjectCode": u["subjectCode"], "title": u["title"], "status": "not_started", "currentStepOrder": 1})
    return ok(arr)


@app.get("/api/v1/units/{unit_id}")
def get_unit(unit_id: str):
    u = _unit_or_404(unit_id)
    return ok({"unitId": u["unitId"], "subjectCode": u["subjectCode"], "title": u["title"], "description": u["description"], "steps": [{"stepOrder": s["stepOrder"], "stepType": s["stepType"], "title": s["title"]} for s in u["steps"]]})


@app.post("/api/v1/units/{unit_id}/start")
def start_unit(unit_id: str):
    _unit_or_404(unit_id)
    uid = "u_demo"
    progress[(uid, unit_id)] = {"status": "in_progress", "currentStepOrder": 1, "currentStepType": "intro", "completedAt": None}
    return ok({"unitId": unit_id, "status": "in_progress", "currentStepOrder": 1, "currentStepType": "intro"})


@app.get("/api/v1/units/{unit_id}/progress")
def unit_progress(unit_id: str):
    _unit_or_404(unit_id)
    p = progress.get(("u_demo", unit_id), {"status": "not_started", "currentStepOrder": 1, "completedAt": None})
    return ok({"unitId": unit_id, **p})


@app.get("/api/v1/units/{unit_id}/steps/{step_type}")
def unit_step(unit_id: str, step_type: StepType):
    u = _unit_or_404(unit_id)
    for s in u["steps"]:
        if s["stepType"] == step_type:
            return ok({"unitId": unit_id, "stepType": step_type, "title": s["title"], "contentMarkdown": s["contentMarkdown"]})
    raise HTTPException(status_code=404, detail="step not found")


@app.get("/api/v1/units/{unit_id}/questions")
def list_questions(unit_id: str, stepType: Literal["practice", "test", "review"] | None = None, count: int = 10, random_order: bool = Query(False, alias="random")):
    _unit_or_404(unit_id)
    items = [q for q in questions.values() if q["unitId"] == unit_id and (stepType is None or q["stepType"] == stepType)]
    if random_order:
        random.shuffle(items)
    items = items[: max(1, min(50, count))]
    payload = [{"questionId": q["questionId"], "unitId": q["unitId"], "stepType": q["stepType"], "questionType": q["questionType"], "body": q["body"], "choices": q.get("choices", [])} for q in items]
    return ok(payload)


@app.post("/api/v1/questions/{question_id}/answer")
def answer_question(question_id: str, req: AnswerRequest):
    q = _question_or_404(question_id)
    correct = str(req.answer).strip() == str(q["correctAnswer"]).strip()
    return ok({"isCorrect": correct, "correctAnswer": q["correctAnswer"], "explanation": q.get("explanation", ""), "nextHintAvailable": (not correct and len(hints.get(question_id, [])) > 0)})


@app.get("/api/v1/questions/{question_id}/hints/{level}")
def get_hint(question_id: str, level: int):
    _question_or_404(question_id)
    arr = hints.get(question_id, [])
    for h in arr:
        if h["hintLevel"] == level:
            return ok({"questionId": question_id, **h})
    raise HTTPException(status_code=404, detail="hint not found")


@app.post("/api/v1/units/{unit_id}/tests/submit")
def submit_test(unit_id: str, req: TestSubmitRequest):
    _unit_or_404(unit_id)
    total = len(req.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="answers required")
    correct = 0
    for a in req.answers:
        q = _question_or_404(a.questionId)
        if q["unitId"] == unit_id and q["stepType"] == "test" and str(a.answer).strip() == str(q["correctAnswer"]).strip():
            correct += 1
    score = round((correct / total) * 100, 2)
    passed = score >= 80
    if passed:
        progress[("u_demo", unit_id)] = {"status": "completed", "currentStepOrder": 4, "currentStepType": "test", "completedAt": now_iso()}
    return ok({"scorePercent": score, "passThreshold": 80, "isPassed": passed, "nextAction": "passed" if passed else "go_review"})


@app.get("/api/v1/units/{unit_id}/review-set")
def get_review_set(unit_id: str):
    _unit_or_404(unit_id)
    rs = next((r for r in review_sets.values() if r["unitId"] == unit_id), None)
    if not rs:
        raise HTTPException(status_code=404, detail="review set not found")
    qs = [questions[qid] for qid in rs["questionIds"]]
    return ok({"reviewSetId": rs["reviewSetId"], "questionCount": len(qs), "requiredCorrectCount": rs["requiredCorrectCount"], "questions": [{"questionId": q["questionId"], "unitId": q["unitId"], "stepType": q["stepType"], "questionType": q["questionType"], "body": q["body"], "choices": q.get("choices", [])} for q in qs]})


@app.post("/api/v1/units/{unit_id}/review-set/submit")
def submit_review(unit_id: str, req: ReviewSubmitRequest):
    _unit_or_404(unit_id)
    rs = review_sets.get(req.reviewSetId)
    if not rs or rs["unitId"] != unit_id:
        raise HTTPException(status_code=404, detail="review set not found")
    correct = 0
    for a in req.answers:
        q = _question_or_404(a.questionId)
        if q["questionId"] in rs["questionIds"] and str(a.answer).strip() == str(q["correctAnswer"]).strip():
            correct += 1
    count = len(rs["questionIds"])
    cleared = correct >= rs["requiredCorrectCount"]
    return ok({"correctCount": correct, "questionCount": count, "requiredCorrectCount": rs["requiredCorrectCount"], "isCleared": cleared, "canRetryTest": cleared})


@app.get("/api/v1/progress/summary")
def progress_summary():
    completed = sum(1 for p in progress.values() if p["status"] == "completed")
    in_progress = sum(1 for p in progress.values() if p["status"] == "in_progress")
    return ok({"completedUnits": completed, "inProgressUnits": in_progress, "streakDays": 0, "todaySolvedCount": 0})


@app.get("/api/v1/badges")
def badges():
    return ok(badges_catalog)


@app.get("/api/v1/badges/me")
def my_badges():
    return ok(user_badges.get("u_demo", []))


@app.post("/api/v1/badges/evaluate")
def eval_badges():
    return ok({})


# Admin endpoints
@app.post("/api/v1/admin/units")
def admin_create_unit(req: AdminUnitUpsertRequest):
    unit_id = f"unit_{uuid.uuid4().hex[:6]}"
    units[unit_id] = {"unitId": unit_id, "subjectCode": req.subjectCode, "title": req.title, "description": req.description, "isPublished": req.isPublished, "steps": []}
    return ok({"unitId": unit_id, "subjectCode": req.subjectCode, "title": req.title, "description": req.description, "steps": []})


@app.put("/api/v1/admin/units/{unit_id}")
def admin_update_unit(unit_id: str, req: AdminUnitUpsertRequest):
    u = _unit_or_404(unit_id)
    u.update({"subjectCode": req.subjectCode, "title": req.title, "description": req.description, "isPublished": req.isPublished})
    return ok({"unitId": unit_id, "subjectCode": u["subjectCode"], "title": u["title"], "description": u["description"], "steps": [{"stepOrder": s["stepOrder"], "stepType": s["stepType"], "title": s["title"]} for s in u["steps"]]})


@app.delete("/api/v1/admin/units/{unit_id}")
def admin_delete_unit(unit_id: str):
    _unit_or_404(unit_id)
    del units[unit_id]
    return ok({})


@app.post("/api/v1/admin/units/{unit_id}/steps")
def admin_create_step(unit_id: str, req: AdminStepUpsertRequest):
    u = _unit_or_404(unit_id)
    step = {"stepId": f"st_{uuid.uuid4().hex[:6]}", "stepType": req.stepType, "stepOrder": req.stepOrder, "title": req.title, "contentMarkdown": req.contentMarkdown}
    u["steps"].append(step)
    return ok({"unitId": unit_id, "stepType": req.stepType, "title": req.title, "contentMarkdown": req.contentMarkdown})


@app.put("/api/v1/admin/steps/{step_id}")
def admin_update_step(step_id: str, req: AdminStepUpsertRequest):
    for u in units.values():
        for s in u["steps"]:
            if s.get("stepId") == step_id:
                s.update({"stepType": req.stepType, "stepOrder": req.stepOrder, "title": req.title, "contentMarkdown": req.contentMarkdown})
                return ok({"unitId": u["unitId"], "stepType": s["stepType"], "title": s["title"], "contentMarkdown": s["contentMarkdown"]})
    raise HTTPException(status_code=404, detail="step not found")


@app.post("/api/v1/admin/questions")
def admin_create_question(req: AdminQuestionUpsertRequest):
    _unit_or_404(req.unitId)
    qid = f"q_{uuid.uuid4().hex[:6]}"
    q = {"questionId": qid, "unitId": req.unitId, "stepType": req.stepType, "questionType": req.questionType, "body": req.body, "choices": req.choices or [], "correctAnswer": req.correctAnswer, "explanation": req.explanation}
    questions[qid] = q
    return ok({"questionId": qid, "unitId": req.unitId, "stepType": req.stepType, "questionType": req.questionType, "body": req.body, "choices": req.choices or []})


@app.put("/api/v1/admin/questions/{question_id}")
def admin_update_question(question_id: str, req: AdminQuestionUpsertRequest):
    _question_or_404(question_id)
    questions[question_id].update({"unitId": req.unitId, "stepType": req.stepType, "questionType": req.questionType, "body": req.body, "choices": req.choices or [], "correctAnswer": req.correctAnswer, "explanation": req.explanation})
    q = questions[question_id]
    return ok({"questionId": q["questionId"], "unitId": q["unitId"], "stepType": q["stepType"], "questionType": q["questionType"], "body": q["body"], "choices": q.get("choices", [])})


@app.delete("/api/v1/admin/questions/{question_id}")
def admin_delete_question(question_id: str):
    _question_or_404(question_id)
    del questions[question_id]
    return ok({})


@app.post("/api/v1/admin/questions/{question_id}/hints")
def admin_create_hint(question_id: str, req: AdminHintUpsertRequest):
    _question_or_404(question_id)
    hints.setdefault(question_id, []).append({"hintId": f"h_{uuid.uuid4().hex[:6]}", "hintLevel": req.hintLevel, "hintText": req.hintText})
    return ok({"questionId": question_id, "hintLevel": req.hintLevel, "hintText": req.hintText})


@app.put("/api/v1/admin/hints/{hint_id}")
def admin_update_hint(hint_id: str, req: AdminHintUpsertRequest):
    for qid, hs in hints.items():
        for h in hs:
            if h.get("hintId") == hint_id:
                h.update({"hintLevel": req.hintLevel, "hintText": req.hintText})
                return ok({"questionId": qid, "hintLevel": h["hintLevel"], "hintText": h["hintText"]})
    raise HTTPException(status_code=404, detail="hint not found")


@app.post("/api/v1/admin/review-sets")
def admin_create_review_set(req: AdminReviewSetUpsertRequest):
    _unit_or_404(req.unitId)
    set_id = f"rs_{uuid.uuid4().hex[:6]}"
    review_sets[set_id] = {"reviewSetId": set_id, "unitId": req.unitId, "questionIds": req.questionIds, "requiredCorrectCount": req.requiredCorrectCount}
    return get_review_set(req.unitId)


@app.put("/api/v1/admin/review-sets/{set_id}")
def admin_update_review_set(set_id: str, req: AdminReviewSetUpsertRequest):
    _unit_or_404(req.unitId)
    if set_id not in review_sets:
        raise HTTPException(status_code=404, detail="review set not found")
    review_sets[set_id] = {"reviewSetId": set_id, "unitId": req.unitId, "questionIds": req.questionIds, "requiredCorrectCount": req.requiredCorrectCount}
    qs = [questions[qid] for qid in req.questionIds if qid in questions]
    return ok({"reviewSetId": set_id, "questionCount": len(req.questionIds), "requiredCorrectCount": req.requiredCorrectCount, "questions": [{"questionId": q["questionId"], "unitId": q["unitId"], "stepType": q["stepType"], "questionType": q["questionType"], "body": q["body"], "choices": q.get("choices", [])} for q in qs]})


@app.post("/api/v1/admin/badges")
def admin_create_badge(req: AdminBadgeUpsertRequest):
    badge = {"badgeId": f"b_{uuid.uuid4().hex[:6]}", "badgeType": req.badgeType, "name": req.name, "conditionValue": req.conditionValue, "awardedAt": None}
    badges_catalog.append(badge)
    return ok(badges_catalog)


@app.put("/api/v1/admin/badges/{badge_id}")
def admin_update_badge(badge_id: str, req: AdminBadgeUpsertRequest):
    for b in badges_catalog:
        if b["badgeId"] == badge_id:
            b.update({"badgeType": req.badgeType, "name": req.name, "conditionValue": req.conditionValue})
            return ok(badges_catalog)
    raise HTTPException(status_code=404, detail="badge not found")
