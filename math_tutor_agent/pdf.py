from __future__ import annotations

from importlib import import_module, util
from pathlib import Path

from math_tutor_agent.models import TextbookChunk
from math_tutor_agent.store import TextbookStore


def ingest_pdf_to_store(
    pdf_path: str | Path,
    *,
    publisher: str,
    grade: str = "고1",
    subject: str | None = None,
    chapter: str = "미분류",
    section: str = "미분류",
    source_license: str,
    chunk_chars: int = 900,
    overlap_chars: int = 120,
) -> TextbookStore:
    """Extract text from a licensed local PDF and convert it to searchable chunks."""

    path = Path(pdf_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only local PDF files are supported.")
    text = _extract_pdf_text(path)
    if not text.strip():
        raise ValueError("No text was extracted. Scanned PDFs need a separate OCR pipeline.")
    chunks = []
    for index, content in enumerate(_chunk_text(text, chunk_chars, overlap_chars), start=1):
        chunks.append(
            TextbookChunk(
                id=f"{path.stem}-{index}",
                publisher=publisher,
                grade=grade,
                subject=subject,
                chapter=chapter,
                section=section,
                concept="PDF 추출 chunk",
                keywords=_keywords_from_text(content),
                content=content,
                source_license=source_license,
            )
        )
    return TextbookStore(chunks)


def _extract_pdf_text(path: Path) -> str:
    if util.find_spec("pypdf") is None:  # pragma: no cover - optional extra guard
        raise RuntimeError("Install PDF support with: pip install -e '.[pdf]'")
    pdf_module = import_module("pypdf")
    reader = pdf_module.PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _chunk_text(text: str, chunk_chars: int, overlap_chars: int) -> list[str]:
    if chunk_chars <= overlap_chars:
        raise ValueError("chunk_chars must be greater than overlap_chars.")
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        chunk = normalized[start : start + chunk_chars].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_chars - overlap_chars
    return chunks


def _keywords_from_text(text: str) -> list[str]:
    candidates = ["일차방정식", "이차방정식", "인수분해", "근", "계수", "상수항"]
    return [keyword for keyword in candidates if keyword in text]
