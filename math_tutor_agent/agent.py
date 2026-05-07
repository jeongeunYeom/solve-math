from __future__ import annotations

from math_tutor_agent.models import (
    ProblemRequest,
    SolutionResponse,
    SolutionStep,
    VerificationStatus,
)
from math_tutor_agent.retriever import KeywordRetriever
from math_tutor_agent.solver import RuleBasedSolver
from math_tutor_agent.store import TextbookStore

LOW_OCR_CONFIDENCE = 0.75


class MathTutorAgent:
    """Coordinates OCR confidence checks, textbook retrieval, solving, and validation."""

    def __init__(self, store: TextbookStore | None = None) -> None:
        self.store = store or TextbookStore()
        self.retriever = KeywordRetriever(self.store)
        self.solver = RuleBasedSolver()

    def solve(self, request: ProblemRequest | dict) -> SolutionResponse:
        if isinstance(request, ProblemRequest):
            problem = request
        else:
            problem = ProblemRequest.from_dict(request)
        contexts = self.retriever.retrieve(
            problem.problem_text,
            publisher=problem.publisher,
            grade=problem.grade,
            subject=problem.subject,
        )
        if problem.ocr_confidence is not None and problem.ocr_confidence < LOW_OCR_CONFIDENCE:
            return SolutionResponse(
                status=VerificationStatus.NEEDS_CONFIRMATION,
                normalized_problem=problem.problem_text,
                textbook_context=contexts,
                warnings=[
                    "OCR 신뢰도가 낮아 풀이 전에 학생이 문제 인식 결과를 확인해야 합니다."
                ],
                steps=[
                    SolutionStep(
                        title="문제 확인 필요",
                        explanation="카메라 인식 결과에 오탈자나 수식 누락이 있을 수 있습니다.",
                    )
                ],
            )
        solution = self.solver.solve(problem.problem_text)
        if solution is None:
            return SolutionResponse(
                status=VerificationStatus.UNSUPPORTED,
                normalized_problem=problem.problem_text,
                textbook_context=contexts,
                warnings=["현재 MVP 규칙 풀이기는 일차방정식과 일부 이차방정식만 지원합니다."],
                steps=[
                    SolutionStep(
                        title="교과서 개념 확인",
                        explanation="검색된 교과서 개념을 바탕으로 풀이 유형을 확장할 수 있습니다.",
                    )
                ],
            )
        return SolutionResponse(
            status=VerificationStatus.VERIFIED,
            normalized_problem=problem.problem_text,
            answer=solution.answer,
            steps=solution.steps,
            textbook_context=contexts,
            verification=solution.verification,
        )
