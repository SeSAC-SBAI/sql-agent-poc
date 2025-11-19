# KOSIS SQL Agent

자연어로 KOSIS(국가통계포털) 데이터를 조회하는 LangGraph 기반 챗봇

## 주요 기능

- 자연어 → SQL 자동 변환
- 9단계 파이프라인 (의도 분류 → 테이블 검색 → SQL 생성 → 실행 → 분석 → 시각화 → 응답)
- ChromaDB 벡터 검색 + Rule 기반 하이브리드 테이블 매칭
- Streamlit 프리미엄 UI & Plotly 차트

## 데이터 출처

- **KOSIS** (국가통계포털, Korean Statistical Information Service)
- 제공: 통계청 산하 국가데이터처
- 포함 데이터: 인구, 주거, 노동, 경제 등 한국 통계

## 기술 스택

- **LLM**: Google Gemini 2.5 Flash
- **Framework**: LangGraph, LangChain
- **DB**: Turso (SQLite), ChromaDB
- **Frontend**: Streamlit, Plotly
- **Embedding**: Upstage (passage/query)

## 빠른 시작
```bash
# 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# GOOGLE_API_KEY, UPSTAGE_API_KEY, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN 입력

# 벡터 DB 초기화 (최초 1회)
python scripts/setup_vector_db.py

# 실행
streamlit run app.py
```

## 프로젝트 구조
```
├── agents/          # LangGraph 노드 및 상태 관리
├── database/        # DB 연결, 벡터 검색, 메타데이터
├── frontend/        # Streamlit UI 컴포넌트
├── utils/           # 프롬프트 템플릿
├── config/          # 설정 관리
└── scripts/         # 초기화 스크립트
```

## 환경 변수

필요한 API 키:
- `GOOGLE_API_KEY` - Gemini LLM
- `UPSTAGE_API_KEY` - 임베딩 모델
- `TURSO_DATABASE_URL` - DB URL
- `TURSO_AUTH_TOKEN` - DB 인증