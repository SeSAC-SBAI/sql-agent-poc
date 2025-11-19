"""콘텐츠 스타일 변환 유틸리티"""

from typing import Optional
from langsmith import traceable


from agents.helpers import get_llm_text
from utils.prompts import (
    REPORTER_RESPONSE_PROMPT,
    PAPER_RESPONSE_PROMPT,
    BLOG_RESPONSE_PROMPT,
)


@traceable(name="format_answer_by_style")
def format_answer_by_style(
    *,
    base_answer: str,
    user_query: str,
    style: str,
    style_request: Optional[str] = None,
    query_result: Optional[list] = None,
    insight: Optional[str] = None,
    processed_data: Optional[dict] = None,
    tables_info: Optional[list] = None,
) -> str:
    """
    최종 답변을 기자/논문/블로그 스타일로 변환하는 헬퍼 함수.

    Args:
        base_answer: 기본 답변 텍스트
        user_query: 사용자 질문
        style: 스타일 ("report"/"reporter"/"기자", "paper"/"논문", "blog"/"블로그")
        style_request: 사용자 추가 요구사항 (선택)
        query_result: SQL 실행 결과 원본 데이터
        insight: 인사이트 분석
        processed_data: 계산된 데이터 (증가율 등)
        tables_info: 사용된 테이블 정보

    Returns:
        스타일 변환된 텍스트
    """
    llm = get_llm_text()
    style = (style or "").lower()

    # 스타일별 프롬프트 선택
    if style in ("report", "reporter", "기자"):
        prompt_tmpl = REPORTER_RESPONSE_PROMPT
    elif style in ("paper", "논문"):
        prompt_tmpl = PAPER_RESPONSE_PROMPT
    elif style in ("blog", "블로그"):
        prompt_tmpl = BLOG_RESPONSE_PROMPT
    else:
        return base_answer

    # 사용자 추가 요구사항 섹션
    user_request_section = ""
    if style_request:
        user_request_section = f"\n[사용자 추가 요구]\n{style_request}\n"

    # 스타일별 데이터 섹션 구성
    data_section = ""
    insight_section = ""
    method_section = ""

    if style in ("report", "reporter", "기자"):
        # 기자: query_result, insight
        if query_result:
            data_section = f"\n[조회 데이터]\n{str(query_result)}\n"
        if insight:
            insight_section = f"\n[인사이트]\n{insight}\n"

    elif style in ("paper", "논문"):
        # 논문: query_result, insight, processed_data, tables_info
        if query_result:
            data_section = f"\n[조회 데이터]\n{str(query_result)}\n"
        if insight:
            insight_section = f"\n[인사이트]\n{insight}\n"
        if processed_data:
            method_section += f"\n[계산된 데이터]\n{str(processed_data)}\n"
        if tables_info:
            table_names = [t.get("table_name", "") for t in tables_info]
            method_section += f"\n[사용 테이블]\n{', '.join(table_names)}\n"

    elif style in ("blog", "블로그"):
        # 블로그: insight만
        if insight:
            insight_section = f"\n[인사이트]\n{insight}\n"

    # 프롬프트 포맷팅
    prompt = prompt_tmpl.format(
        user_query=user_query,
        base_answer=base_answer,
        data_section=data_section,
        insight_section=insight_section,
        method_section=method_section,
        user_request_section=user_request_section,
    )

    try:
        response = llm.invoke(prompt)
        styled = response.content.strip()
    except Exception as e:
        print(f"[format_answer_by_style] 스타일 변환 실패: {e}")
        styled = base_answer

    return styled
