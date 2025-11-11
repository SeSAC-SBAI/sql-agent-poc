# SQL Agent POC

자연어 질문을 SQL 쿼리로 변환하여 인구 통계 데이터를 조회하는 AI Agent 시스템

## 주요 기능

- 자연어로 질문하면 자동으로 SQL 쿼리 생성
- 2016년 1월 ~ 2025년 10월 인구 통계 데이터 조회
- Streamlit 기반 대화형 웹 인터페이스
- 실행된 SQL 쿼리 및 처리 과정 표시
- ChromaDB를 활용한 테이블 메타데이터 검색

## 프로젝트 구조

```
.
├── agents/              # SQL Agent 관리
│   ├── sql_agent.py
│   └── __init__.py
├── config/              # 설정 파일
│   ├── settings.py
│   └── __init__.py
├── database/            # DB 연결 관리
│   ├── connection.py
│   └── __init__.py
├── utils/               # 유틸리티 함수
│   ├── tools.py         # 커스텀 도구
│   ├── logger.py
│   └── __init__.py
├── tests/               # 테스트 파일
│   ├── test_agent.py
│   └── test_db.py
├── embeding_DB/         # ChromaDB 저장소
├── app.py               # Streamlit 웹 앱
├── embedding_setup.py   # 임베딩 초기 설정
├── population_v1.17.db  # SQLite 데이터베이스
├── requirements.txt
└── .env
```

## 설치 방법

### 1. 필수 요구사항

- Python 3.8+
- pip

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일 생성:

```env
# Upstage API (기본)
UPSTAGE_API_KEY=your_upstage_api_key

# LangSmith (선택)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_api_key

# 데이터베이스
DATABASE_PATH=population_v1.17.db

# 모델 설정
MODEL_NAME=solar-pro2
TEMPERATURE=0
```

### 4. 임베딩 DB 초기화

```bash
python embedding_setup.py
```

## 사용 방법

### Streamlit 웹 앱 실행

```bash
streamlit run app.py
```

브라우저에서 자동으로 열립니다 (기본: http://localhost:8501)

### 커맨드라인 테스트

```bash
python tests/test_agent.py
```

## 데이터베이스 구조

### population_gender_stats
- 성별 인구 통계
- 컬럼: 행정구역, 년월, 항목(총인구수/남자인구수/여자인구수), 값

### population_age_stats
- 연령대별 인구 통계
- 컬럼: 행정구역, 년월, 연령대, 항목, 값
- 연령대: 0-4, 5-9, ..., 95-99, 100+

### population_stats
- 세대수 통계
- 컬럼: 행정구역, 년월, 값

## 질문 예시

- "서울특별시의 최신 총인구수는?"
- "경기도 세대수는 얼마야?"
- "부산에는 30대가 몇명이나 살아?"
- "2025년 10월 인구 150만명 미만 광역시는?"

## 사용된 기술 스택

- **LLM**: Upstage Solar Pro2
- **Framework**: LangChain
- **Database**: SQLite
- **Vector DB**: ChromaDB
- **UI**: Streamlit
- **Python Libraries**: 
  - langchain-upstage
  - langchain-community
  - streamlit
  - chromadb
  - sqlalchemy

## 주요 특징

### 1. 지능형 테이블 선택
ChromaDB 기반 임베딩을 통해 질문에 가장 적합한 테이블 자동 선택

### 2. SQL 쿼리 검증
LangChain의 query checker를 통한 SQL 문법 검증

### 3. 대화형 인터페이스
- 질문 히스토리 유지
- 실행된 SQL 쿼리 표시
- 처리 과정 단계별 확인

### 4. 에러 처리
- 명확한 에러 메시지
- 자동 재시도 메커니즘

## 설정 커스터마이징

### config/settings.py

```python
# 모델 변경
MODEL_NAME = "solar-pro2"  # 또는 다른 모델

# Temperature 조정
TEMPERATURE = 0  # 0-1 사이 값

# DB 경로 변경
DATABASE_PATH = "your_database.db"
```

## 문제 해결

### LangSmith 403 에러
`.env`에서 `LANGCHAIN_TRACING_V2=false`로 설정

### DB 파일 없음 에러
`config/settings.py`에서 `DATABASE_PATH` 확인

### 임베딩 DB 없음
`python embedding_setup.py` 실행

## 라이선스

MIT License

## 개발자

Built with using LangChain and Streamlit
