from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from math_tutor_agent.agent import MathTutorAgent
from math_tutor_agent.models import ProblemRequest, SolutionResponse, TextbookChunk, to_plain_dict
from math_tutor_agent.pdf import ingest_pdf_to_store
from math_tutor_agent.store import TextbookStore

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CHUNKS = ROOT / "examples" / "textbook_chunks.sample.json"
WEB_DIR = ROOT / "web"

store = TextbookStore.from_json(EXAMPLE_CHUNKS) if EXAMPLE_CHUNKS.exists() else TextbookStore()
agent = MathTutorAgent(store)
app = FastAPI(title="고1 수학 튜터 에이전트 MVP", version="0.1.0")

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@dataclass
class PdfIngestRequest:
    pdf_path: str
    publisher: str
    source_license: str
    grade: str = "고1"
    subject: str | None = None
    chapter: str = "미분류"
    section: str = "미분류"


@app.get("/")
def index() -> FileResponse | dict[str, str]:
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "고1 수학 튜터 에이전트 MVP"}


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "textbook_chunks": len(store.all())}


@app.post("/solve", response_model=SolutionResponse)
def solve_problem(request: ProblemRequest) -> dict:
    return to_plain_dict(agent.solve(request))


@app.post("/textbooks/chunks")
def add_textbook_chunk(chunk: TextbookChunk) -> dict[str, str | int]:
    store.add(chunk)
    return {"status": "added", "textbook_chunks": len(store.all())}


@app.post("/textbooks/pdf")
def add_textbook_pdf(request: PdfIngestRequest) -> dict[str, str | int]:
    imported_store = ingest_pdf_to_store(**to_plain_dict(request))
    store.extend(imported_store.all())
    return {"status": "added", "imported_chunks": len(imported_store.all())}
