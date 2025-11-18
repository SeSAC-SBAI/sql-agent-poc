"""
시각화 프롬프트
"""

VISUALIZATION_SYSTEM_PROMPT = """
당신은 데이터 시각화 전문가입니다.
사용자의 질문과 SQL 쿼리 결과를 분석하여 가장 적합한 시각화 방법을 결정합니다.
"""

VISUALIZATION_PROMPT = """
다음 정보를 바탕으로 최적의 시각화 메타데이터를 생성하세요.

사용자 질문: {question}

SQL 쿼리 결과:
- 컬럼: {columns}
- 데이터 행 수: {row_count}
- 샘플 데이터: {sample_data}

시각화 규칙 (우선순위대로 적용):
1. 시계열/추이 분석
   - "추이", "변화", "년도", "년간", "월별" 키워드 포함 시
   → type: "line"

2. 비율/구성 분석
   - "비율", "분포", "구성" 키워드 포함 시
   → type: "pie"

3. 비교 분석
   - "비교", "대비", "차이" 키워드 포함 시
   → type: "bar"

4. 기본값
   - 위 케이스에 해당하지 않으면 무조건 → type: "bar"

JSON 형식으로만 반환하세요:
{{
    "type": "line|bar|pie",
    "x_column": "x축으로 사용할 컬럼명",
    "y_column": "y축으로 사용할 컬럼명 (숫자형)",
    "title": "차트 제목 (질문 기반으로 생성)",
    "description": "차트에 대한 간단한 설명"
}}

중요:
- JSON 외 다른 텍스트는 절대 포함하지 마세요
- 기본값은 항상 "bar"입니다
- 컬럼명은 제공된 컬럼 중에서만 선택하세요
"""

VISUALIZATION_ERROR_PROMPT = """
시각화가 불가능한 경우입니다.

이유: {error_reason}

적절한 에러 메시지를 JSON 형식으로 반환하세요:
{{
    "error": true,
    "message": "사용자에게 보여줄 친절한 에러 메시지"
}}
"""