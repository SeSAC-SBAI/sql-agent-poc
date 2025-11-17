"""
agents/helpers.py

노드에서 사용하는 헬퍼 함수들
"""

import re
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

# ============================================
# LLM 초기화
# ============================================


def get_llm():
    """
    LLM 인스턴스 반환

    Returns:
        ChatGoogleGenerativeAI 인스턴스
    """
    return ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        temperature=settings.TEMPERATURE,
        google_api_key=settings.GOOGLE_API_KEY,
        response_mime_type="application/json",
        max_output_tokens=2048,
    )


def get_llm_text():
    """텍스트 출력 전용 (JSON 모드 없음)"""
    return ChatGoogleGenerativeAI(
        model=settings.MODEL_NAME,
        temperature=settings.TEMPERATURE,
        google_api_key=settings.GOOGLE_API_KEY,
        max_output_tokens=4096,
    )


def extract_calculation_hints(user_query: str) -> list:
    """
    사용자 질문에서 계산 힌트 추출

    Args:
        user_query: 사용자 질문

    Returns:
        list: 계산 힌트 리스트
    """
    hints = []

    # 증가율/감소율
    if "증가율" in user_query or "감소율" in user_query or "증감" in user_query:
        hints.append("시간에 따른 증가율 또는 감소율 계산")

    # 비율
    if "비율" in user_query or "성비" in user_query or "비중" in user_query:
        hints.append("항목 간 비율 계산")

    # 평균
    if "평균" in user_query:
        hints.append("평균값 계산")

    # 상위 N개
    top_match = re.search(r"상위\s*(\d+)", user_query)
    if top_match:
        n = top_match.group(1)
        hints.append(f"상위 {n}개 추출 및 정렬")

    # 하위 N개
    bottom_match = re.search(r"하위\s*(\d+)", user_query)
    if bottom_match:
        n = bottom_match.group(1)
        hints.append(f"하위 {n}개 추출 및 정렬")

    # 변화량
    if "변화" in user_query or "차이" in user_query:
        hints.append("값의 변화량 계산")

    # 힌트 없으면 기본
    return hints if hints else ["질문에 맞는 적절한 계산 수행"]


def validate_calculation_result(result: dict) -> bool:
    """
    계산 결과 검증

    Args:
        result: LLM이 반환한 계산 결과 (dict)

    Returns:
        bool: 유효하면 True, 아니면 False
    """
    try:
        # 필수 필드 확인
        if "calculated_data" not in result:
            return False
        if "description" not in result:
            return False

        # calculated_data가 비어있지 않은지
        if not result["calculated_data"]:
            return False

        return True
    except:
        return False


# ============================================
# 나중에 MapleRepair용으로 추가할 함수들
# ============================================


def validate_schema(sql_query: str, tables_info: list) -> str:
    """
    SQL 스키마 검증 (Rule-based)

    Args:
        sql_query: 생성된 SQL 쿼리
        tables_info: 사용 가능한 테이블 정보

    Returns:
        str: 에러 메시지 (없으면 빈 문자열)

    TODO: MapleRepair 적용 시 구현
    - 테이블명 존재 여부 확인
    - 컬럼명 존재 여부 확인
    - 오타 체크
    """
    # TODO: 구현 필요
    return ""


def validate_syntax(sql_query: str) -> str:
    """
    SQL 문법 검증 (Rule-based)

    Args:
        sql_query: 생성된 SQL 쿼리

    Returns:
        str: 에러 메시지 (없으면 빈 문자열)

    TODO: MapleRepair 적용 시 구현
    - SELECT 키워드 포함 여부
    - 괄호 매칭
    - 기본 문법 체크 (sqlparse 사용)
    """
    # TODO: 구현 필요
    return ""


def classify_sql_error(error_msg: str) -> str:
    """
    SQL 에러 메시지 분류

    Args:
        error_msg: Exception 에러 메시지

    Returns:
        str: 에러 타입 ("schema", "syntax", "value", "other")

    TODO: MapleRepair 적용 시 구현
    """
    error_lower = error_msg.lower()

    if "no such table" in error_lower or "no such column" in error_lower:
        return "schema"
    elif "syntax error" in error_lower:
        return "syntax"
    elif "datatype mismatch" in error_lower or "invalid" in error_lower:
        return "value"
    else:
        return "other"
