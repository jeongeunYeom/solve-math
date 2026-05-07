from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, get_args, get_origin


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    NEEDS_CONFIRMATION = "needs_confirmation"
    UNSUPPORTED = "unsupported"


@dataclass
class ProblemRequest:
    """Normalized input from mobile text entry, OCR, or a math-recognition pipeline."""

    problem_text: str
    publisher: str | None = None
    grade: str = "고1"
    subject: str | None = None
    ocr_confidence: float | None = None
    image_id: str | None = None

    def __post_init__(self) -> None:
        self.problem_text = " ".join(str(self.problem_text).strip().split())
        if not self.problem_text:
            raise ValueError("problem_text must not be empty.")
        if self.ocr_confidence is not None and not 0 <= self.ocr_confidence <= 1:
            raise ValueError("ocr_confidence must be between 0 and 1.")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ProblemRequest:
        return cls(**value)


@dataclass
class TextbookChunk:
    id: str
    publisher: str
    chapter: str
    section: str
    concept: str
    content: str
    grade: str = "고1"
    subject: str | None = None
    keywords: list[str] = field(default_factory=list)
    source_license: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> TextbookChunk:
        return cls(**value)


@dataclass
class RetrievedChunk:
    chunk: TextbookChunk
    score: float
    matched_keywords: list[str] = field(default_factory=list)


@dataclass
class SolutionStep:
    title: str
    explanation: str
    expression: str | None = None


@dataclass
class SolutionResponse:
    status: VerificationStatus
    normalized_problem: str
    answer: str | None = None
    steps: list[SolutionStep] = field(default_factory=list)
    textbook_context: list[RetrievedChunk] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    verification: str | None = None


def to_plain_dict(value: Any) -> Any:
    """Convert dataclasses and enums into JSON-serializable values."""

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {item.name: to_plain_dict(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, list):
        return [to_plain_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain_dict(item) for key, item in value.items()}
    return value


def dataclass_from_dict(cls: type[Any], value: dict[str, Any]) -> Any:
    """Small recursive constructor useful when FastAPI/Pydantic is unavailable in tests."""

    kwargs = {}
    for item in fields(cls):
        if item.name not in value:
            continue
        kwargs[item.name] = _coerce_value(item.type, value[item.name])
    return cls(**kwargs)


def _coerce_value(annotation: Any, value: Any) -> Any:
    origin = get_origin(annotation)
    if origin is list:
        inner = get_args(annotation)[0]
        return [_coerce_value(inner, item) for item in value]
    if isinstance(annotation, type) and is_dataclass(annotation) and isinstance(value, dict):
        return dataclass_from_dict(annotation, value)
    return value


# Keep a named import of asdict available for integrations that prefer stdlib conversion.
__all__ = [
    "ProblemRequest",
    "RetrievedChunk",
    "SolutionResponse",
    "SolutionStep",
    "TextbookChunk",
    "VerificationStatus",
    "asdict",
    "dataclass_from_dict",
    "to_plain_dict",
]
