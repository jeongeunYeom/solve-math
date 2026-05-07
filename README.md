# 고1 수학 튜터 에이전트 MVP

핸드폰 카메라로 인식한 고등학교 1학년 수학 문제를 교과서 기반으로 설명하고 풀이하는 AI 에이전트의 초기 구현입니다.
현재 저장소는 바로 확장 가능한 백엔드 MVP를 제공합니다.

## 현재 구현 범위

- 텍스트/OCR 결과로 들어온 문제를 `ProblemRequest`로 표준화합니다.
- 출판사별 교과서 chunk를 검색하는 RAG 형태의 `TextbookStore`와 `KeywordRetriever`를 제공합니다.
- 고1 수준의 일차방정식과 일부 이차방정식을 규칙 기반으로 풀이하고 검증합니다.
- OCR 신뢰도가 낮으면 풀이 전에 학생 확인이 필요하다는 응답을 반환합니다.
- FastAPI `/solve` 엔드포인트로 모바일 앱과 연결할 수 있습니다.

## 빠른 실행

의존성 설치 없이 바로 확인하려면 표준 라이브러리 서버를 실행합니다.

```bash
python -m math_tutor_agent.server
```

FastAPI 개발 서버로 실행하려면 의존성을 설치한 뒤 `uvicorn`을 실행합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn math_tutor_agent.api:app --reload
```

브라우저에서 실행용 HTML 열기:

```text
http://127.0.0.1:8000/
```

HTML 파일만 직접 열고 싶다면 `web/index.html`을 브라우저로 열고 API 주소를 `http://127.0.0.1:8000`으로 둡니다.

헬스 체크:

```bash
curl http://127.0.0.1:8000/health
```

문제 풀이:

```bash
curl -X POST http://127.0.0.1:8000/solve \
  -H 'Content-Type: application/json' \
  -d '{"problem_text":"x^2 - 5x + 6 = 0의 두 근을 구하시오.","publisher":"샘플출판사"}'
```

## 교과서 데이터 넣기

`examples/textbook_chunks.sample.json`과 같은 형식으로 출판사, 단원, 개념, 키워드를 chunk 단위로 저장합니다.
실서비스에서는 출판사 라이선스를 확보한 자료만 저장하고, 원문 장문 노출을 제한해야 합니다.

```python
from math_tutor_agent import MathTutorAgent, TextbookStore

store = TextbookStore.from_json("examples/textbook_chunks.sample.json")
agent = MathTutorAgent(store)
```

## PDF 교과서를 학습시키는 방식

제공한 미래엔 교과서 PDF 같은 자료는 모델을 직접 파인튜닝하는 대신, 권한을 확인한 뒤 PDF 텍스트를 추출해 작은 chunk로 나누고 검색 지식베이스에 넣는 RAG 방식으로 연결합니다.
홍보용/미리보기 PDF나 출판사 원문은 저작권이 있을 수 있으므로, 실서비스에서는 출판사 제휴 또는 명시적 이용 허락이 있는 자료만 저장해야 합니다.

로컬 PDF 수집 예시:

```bash
pip install -e '.[pdf]'
```

```python
from math_tutor_agent import MathTutorAgent, ingest_pdf_to_store

store = ingest_pdf_to_store(
    "./licensed_textbooks/mirae-n_basic_math_1.pdf",
    publisher="미래엔",
    grade="고1",
    subject="기본수학1",
    chapter="대수",
    section="미분류",
    source_license="출판사 제휴 계약 또는 내부 사용 권한 확인됨",
)
agent = MathTutorAgent(store)
```

스캔본처럼 텍스트 추출이 되지 않는 PDF는 별도 OCR/수식 인식 파이프라인이 필요합니다.

실행 중인 API에 로컬 PDF를 추가할 수도 있습니다. 이 엔드포인트도 서버가 접근 가능한 로컬 파일 경로만 받도록 두어, 원격 URL 토큰 저장과 무단 다운로드를 애플리케이션 계층에서 통제하게 했습니다.

```bash
curl -X POST http://127.0.0.1:8000/textbooks/pdf \
  -H 'Content-Type: application/json' \
  -d '{"pdf_path":"./licensed_textbooks/mirae-n_basic_math_1.pdf","publisher":"미래엔","subject":"기본수학1","source_license":"권한 확인됨"}'
```

## 다음 단계

1. 이미지 업로드와 OCR/수식 인식 파이프라인 연결
2. PostgreSQL + pgvector 기반 교과서 벡터 검색으로 교체
3. LLM 풀이 생성 계층 추가
4. SymPy 등 수식 검증 엔진 확장
5. 학생별 학습 기록, 오답 유형 분석, 유사 문제 추천 기능 추가
