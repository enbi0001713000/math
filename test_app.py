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


def test_unit_start_always_step1():
    res = client.post("/api/v1/units/unit_1/start", headers=_auth_header())
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["currentStepOrder"] == 1
    assert data["currentStepType"] == "intro"


def test_submit_test_pass_threshold_80():
    res = client.post(
        "/api/v1/units/unit_1/tests/submit",
        headers=_auth_header(),
        json={"answers": [{"questionId": "q_t_1", "answer": "A"}]},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["scorePercent"] == 100.0
    assert data["isPassed"] is True
    assert data["nextAction"] == "passed"


def test_review_clear_condition_4_of_5():
    payload = {
        "reviewSetId": "rs_1",
        "answers": [
            {"questionId": "q_r_1", "answer": "7"},
            {"questionId": "q_r_2", "answer": "6"},
            {"questionId": "q_r_3", "answer": "5"},
            {"questionId": "q_r_4", "answer": "8"},
            {"questionId": "q_r_5", "answer": "0"},
        ],
    }
    res = client.post("/api/v1/units/unit_1/review-set/submit", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["correctCount"] == 4
    assert data["isCleared"] is True
    assert data["canRetryTest"] is True


def test_random_recommendations_source_label():
    res = client.get("/api/v1/recommendations/today?count=2", headers=_auth_header())
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["source"] == "random"
    assert len(data["items"]) <= 2