from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _auth_header() -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/signup",
        json={"email": "student@example.com", "password": "SecurePass123!", "displayName": "student"},
    )
    if res.status_code == 400:
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "student@example.com", "password": "SecurePass123!"},
        )
        token = login.json()["data"]["token"]
    else:
        token = res.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_me_requires_and_returns_user():
    unauthorized = client.get("/api/v1/auth/me")
    assert unauthorized.status_code == 403

    res = client.get("/api/v1/auth/me", headers=_auth_header())
    assert res.status_code == 200
    assert res.json()["data"]["user"]["email"] == "student@example.com"


def test_step_lock_and_order_progression():
    headers = _auth_header()
    client.post("/api/v1/units/unit_1/start", headers=headers)

    locked = client.get("/api/v1/units/unit_1/steps/test", headers=headers)
    assert locked.status_code == 409

    intro = client.get("/api/v1/units/unit_1/steps/intro", headers=headers)
    assert intro.status_code == 200
    example = client.get("/api/v1/units/unit_1/steps/example", headers=headers)
    assert example.status_code == 200
    practice = client.get("/api/v1/units/unit_1/steps/practice", headers=headers)
    assert practice.status_code == 200


def test_submit_test_fail_requires_review_then_clear_and_retry():
    headers = _auth_header()
    client.post("/api/v1/units/unit_1/start", headers=headers)
    client.get("/api/v1/units/unit_1/steps/example", headers=headers)
    client.get("/api/v1/units/unit_1/steps/practice", headers=headers)

    fail = client.post(
        "/api/v1/units/unit_1/tests/submit",
        headers=headers,
        json={"answers": [{"questionId": "q_t_1", "answer": "B"}]},
    )
    assert fail.status_code == 200
    assert fail.json()["data"]["isPassed"] is False

    blocked_retry = client.post(
        "/api/v1/units/unit_1/tests/submit",
        headers=headers,
        json={"answers": [{"questionId": "q_t_1", "answer": "A"}]},
    )
    assert blocked_retry.status_code == 409

    review_payload = {
        "reviewSetId": "rs_1",
        "answers": [
            {"questionId": "q_r_1", "answer": "7"},
            {"questionId": "q_r_2", "answer": "6"},
            {"questionId": "q_r_3", "answer": "5"},
            {"questionId": "q_r_4", "answer": "8"},
            {"questionId": "q_r_5", "answer": "0"},
        ],
    }
    review = client.post("/api/v1/units/unit_1/review-set/submit", headers=headers, json=review_payload)
    assert review.status_code == 200
    assert review.json()["data"]["isCleared"] is True

    retry = client.post(
        "/api/v1/units/unit_1/tests/submit",
        headers=headers,
        json={"answers": [{"questionId": "q_t_1", "answer": "A"}]},
    )
    assert retry.status_code == 200
    assert retry.json()["data"]["isPassed"] is True


def test_phase3_progress_summary_and_badges():
    headers = _auth_header()

    # learning log should increase by answering a question
    answer = client.post("/api/v1/questions/q_pr_1/answer", headers=headers, json={"answer": "5"})
    assert answer.status_code == 200

    summary = client.get("/api/v1/progress/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["data"]["todaySolvedCount"] >= 1

    # complete one unit then evaluate badges
    client.post("/api/v1/units/unit_1/start", headers=headers)
    client.get("/api/v1/units/unit_1/steps/example", headers=headers)
    client.get("/api/v1/units/unit_1/steps/practice", headers=headers)
    client.post("/api/v1/units/unit_1/tests/submit", headers=headers, json={"answers": [{"questionId": "q_t_1", "answer": "A"}]})

    awarded = client.post("/api/v1/badges/evaluate", headers=headers)
    assert awarded.status_code == 200

    mine = client.get("/api/v1/badges/me", headers=headers)
    assert mine.status_code == 200
    ids = {b["badgeId"] for b in mine.json()["data"]}
    assert "b_first" in ids


def test_random_recommendations_source_label():
    headers = _auth_header()
    res = client.get("/api/v1/recommendations/today?count=2", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["source"] == "random"
    assert len(data["items"]) <= 2
