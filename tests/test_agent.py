from math_tutor_agent import MathTutorAgent, ProblemRequest, TextbookStore


def sample_agent() -> MathTutorAgent:
    return MathTutorAgent(TextbookStore.from_json("examples/textbook_chunks.sample.json"))


def test_solves_quadratic_with_context() -> None:
    response = sample_agent().solve(
        ProblemRequest(
            problem_text="x^2 - 5x + 6 = 0의 두 근을 구하시오.",
            publisher="샘플출판사",
            subject="공통수학1",
        )
    )

    assert response.status == "verified"
    assert response.answer == "두 근은 2, 3입니다."
    assert response.textbook_context


def test_low_ocr_confidence_requires_confirmation() -> None:
    response = sample_agent().solve(
        {
            "problem_text": "2x + 4 = 10",
            "publisher": "샘플출판사",
            "ocr_confidence": 0.4,
        }
    )

    assert response.status == "needs_confirmation"
    assert response.answer is None
    assert "OCR 신뢰도" in response.warnings[0]


def test_solves_linear_equation() -> None:
    response = sample_agent().solve({"problem_text": "2x + 4 = 10"})

    assert response.status == "verified"
    assert response.answer == "x = 3"
