from __future__ import annotations

import math
import re
from dataclasses import dataclass
from fractions import Fraction

from math_tutor_agent.models import SolutionStep

LINEAR_RE = re.compile(
    r"^\s*(?P<a>[+-]?\d*)x\s*(?P<op>[+-])\s*(?P<b>\d+)\s*=\s*(?P<c>[+-]?\d+)\s*"
)
SIMPLE_LINEAR_RE = re.compile(r"^\s*(?P<a>[+-]?\d*)x\s*=\s*(?P<c>[+-]?\d+)\s*")
QUADRATIC_RE = re.compile(
    r"(?P<a>[+-]?\d*)x\^2\s*(?P<b_sign>[+-])\s*(?P<b>\d*)x\s*(?P<c_sign>[+-])\s*(?P<c>\d+)\s*=\s*0"
)


@dataclass(frozen=True)
class RuleSolution:
    answer: str
    steps: list[SolutionStep]
    verification: str


class RuleBasedSolver:
    """Rule-based solver for common grade-1 high-school algebra examples."""

    def solve(self, problem_text: str) -> RuleSolution | None:
        normalized = _normalize_math(problem_text)
        return self._solve_quadratic(normalized) or self._solve_linear(normalized)

    def _solve_linear(self, text: str) -> RuleSolution | None:
        match = LINEAR_RE.search(text)
        if match:
            a = _coefficient(match.group("a"))
            b = int(match.group("b")) * (1 if match.group("op") == "+" else -1)
            c = int(match.group("c"))
        else:
            simple = SIMPLE_LINEAR_RE.search(text)
            if not simple:
                return None
            a = _coefficient(simple.group("a"))
            b = 0
            c = int(simple.group("c"))
        if a == 0:
            return None
        solution = Fraction(c - b, a)
        steps = [
            SolutionStep(
                title="문제 식 정리",
                explanation="일차방정식은 x가 한 번만 나타나는 방정식입니다.",
                expression=f"{a}x + ({b}) = {c}",
            ),
            SolutionStep(
                title="상수항을 이항",
                explanation="양변에서 상수항을 빼서 x항만 남깁니다.",
                expression=f"{a}x = {c - b}",
            ),
            SolutionStep(
                title="계수로 나누기",
                explanation="양변을 x의 계수로 나누면 해를 얻습니다.",
                expression=f"x = {_format_fraction(solution)}",
            ),
        ]
        return RuleSolution(
            answer=f"x = {_format_fraction(solution)}",
            steps=steps,
            verification=f"대입 확인: {a}×({_format_fraction(solution)}) + ({b}) = {c}",
        )

    def _solve_quadratic(self, text: str) -> RuleSolution | None:
        match = QUADRATIC_RE.search(text)
        if not match:
            return None
        a = _coefficient(match.group("a"))
        b_abs = int(match.group("b") or "1")
        b = b_abs if match.group("b_sign") == "+" else -b_abs
        c = int(match.group("c")) if match.group("c_sign") == "+" else -int(match.group("c"))
        discriminant = (b * b) - (4 * a * c)
        if a == 0 or discriminant < 0:
            return None
        sqrt_d = math.isqrt(discriminant)
        if sqrt_d * sqrt_d != discriminant:
            return None
        roots = sorted({Fraction(-b + sqrt_d, 2 * a), Fraction(-b - sqrt_d, 2 * a)})
        factor_hint = _factor_hint(a, b, c, roots)
        steps = [
            SolutionStep(
                title="이차방정식 확인",
                explanation="x의 최고차항이 2인 방정식이므로 인수분해나 근의 공식으로 풉니다.",
                expression=f"{a}x^2 + ({b})x + ({c}) = 0",
            ),
            SolutionStep(
                title="판별식 계산",
                explanation="b²-4ac가 완전제곱수이면 고1 인수분해 풀이와 잘 연결됩니다.",
                expression=f"D = ({b})² - 4×{a}×{c} = {discriminant}",
            ),
            SolutionStep(
                title="근 구하기",
                explanation=factor_hint,
                expression=" 또는 ".join(f"x = {_format_fraction(root)}" for root in roots),
            ),
        ]
        answer = ", ".join(_format_fraction(root) for root in roots)
        return RuleSolution(
            answer=f"두 근은 {answer}입니다.",
            steps=steps,
            verification="각 근을 원래 식에 대입하면 좌변이 0이 됩니다.",
        )


def _normalize_math(text: str) -> str:
    return (
        text.replace("−", "-")
        .replace("＋", "+")
        .replace("＝", "=")
        .replace("²", "^2")
        .replace(" ", "")
    )


def _coefficient(raw: str) -> int:
    if raw in ("", "+"):
        return 1
    if raw == "-":
        return -1
    return int(raw)


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _factor_hint(a: int, b: int, c: int, roots: list[Fraction]) -> str:
    if a == 1 and all(root.denominator == 1 for root in roots):
        p, q = (-roots[0], -roots[1])
        return (
            f"합이 {b}, 곱이 {c}가 되는 두 수를 찾아 "
            f"{_linear_factor(p)}{_linear_factor(q)} = 0으로 봅니다."
        )
    return "근의 공식 x=(-b±√D)/2a를 사용합니다."


def _linear_factor(constant: Fraction) -> str:
    if constant == 0:
        return "x"
    if constant > 0:
        return f"(x + {_format_fraction(constant)})"
    return f"(x - {_format_fraction(-constant)})"
