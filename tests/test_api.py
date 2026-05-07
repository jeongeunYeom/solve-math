import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from math_tutor_agent.api import app  # noqa: E402


def test_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_solve_endpoint() -> None:
    response = TestClient(app).post(
        "/solve",
        json={
            "problem_text": "x^2 - 5x + 6 = 0의 두 근을 구하시오.",
            "publisher": "샘플출판사",
            "subject": "공통수학1",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "verified"
