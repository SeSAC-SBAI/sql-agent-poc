"""테이블 검색 노드"""

from typing import Literal
from langgraph.types import Command, interrupt
from langgraph.graph import END

from agents.state import StatsChatbotState


def search_tables(
    state: StatsChatbotState,
) -> Command[Literal["request_clarification", "generate_sql", "__end__"]]:
    """
    2. 테이블 및 스키마 검색 노드 (Data 단계)

    스마트 테이블 검색 (벡터 + Rule 조합)
    - 벡터 검색: 질문을 임베딩하여 유사도 검색
    - Rule 검색: 비율 계산 등 필수 테이블 자동 추가
    - 상세 메타데이터 반환
    """
    from database.vector_db import smart_search_tables

    # Rule 기반 검색 (벡터 + Rule 조합)
    tables_info = smart_search_tables(
        state["user_query"], n_results=5  # 여러 테이블 가능
    )

    clarification_count = state.get("clarification_count", 0)

    # 테이블 없음 & 재시도 0회 → 추가 정보 요청
    if not tables_info and clarification_count == 0:
        return Command(
            goto="request_clarification",
            update={
                "tables_info": tables_info,
                "original_query": state["user_query"],
            },
        )

    # 테이블 없음 & 재시도 1회 이상 → 종료
    if not tables_info and clarification_count >= 1:
        return Command(
            goto=END,
            update={
                "tables_info": tables_info,
                "final_response": "죄송합니다. 해당 통계 데이터를 찾을 수 없습니다.",
            },
        )

    # 테이블 찾음 → SQL 생성으로
    return Command(goto="generate_sql", update={"tables_info": tables_info})


def request_clarification(
    state: StatsChatbotState,
) -> Command[Literal["classify_intent"]]:
    """
    3. 추가 정보 요청 노드 (User Input 단계)

    테이블 검색 실패 시 사용자에게 추가 정보 요청
    - interrupt로 사용자 입력 대기
    - 원래 질문과 추가 정보 결합

    TODO: 테스트 보류
    - interrupt 실제 동작 확인 필요
    - 질문 합치기 검증 필요
    - clarification_count 증가 확인 필요
    - 통합 테스트 또는 별도 시나리오 필요
    """
    clarification_message = "좀 더 구체적으로 알려주시겠어요? (예: 어느 지역? 몇 년도?)"

    # interrupt로 사용자 답변 받기
    user_additional_info = interrupt(clarification_message)

    # 원래 질문 + 추가 정보
    combined_query = f"{user_additional_info} {state['original_query']}"

    return Command(
        goto="classify_intent",
        update={
            "clarification_count": state["clarification_count"] + 1,
            "user_query": combined_query,
        },
    )
