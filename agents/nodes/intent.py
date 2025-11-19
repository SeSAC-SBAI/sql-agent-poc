"""Intent 분류 노드"""

import json
from typing import Literal
from langgraph.types import Command
from langgraph.graph import END

from agents.state import StatsChatbotState
from agents.helpers import get_llm
from utils.prompts import CLASSIFY_INTENT_PROMPT


def classify_intent(
    state: StatsChatbotState,
) -> Command[Literal["search_tables", "__end__"]]:
    """
    1. 질문 분류 노드 (LLM 단계)

    사용자 질문을 분석하여 6가지 시나리오 중 하나로 분류
    - single_value: 단순 조회
    - table_view: 표 조회
    - simple_aggregation: 단순 집계
    - derived_calculation: 파생 계산
    - multi_step_analysis: 다단계 분석
    - out_of_scope: 범위 외 질문
    """
    user_query = state["user_query"]
    conversation_history = state.get("conversation_history", "없음")

    # LLM 초기화
    llm = get_llm()

    # 프롬프트 포맷팅
    prompt = CLASSIFY_INTENT_PROMPT.format(
        conversation_history=conversation_history, user_query=user_query
    )

    # LLM 호출
    response = llm.invoke(prompt)

    # JSON 파싱
    try:
        result = json.loads(response.content)
        scenario_type = result["scenario_type"]
        reasoning = result.get("reasoning", "분류 완료")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"JSON 파싱 실패: {e}")
        print(f"원본 응답: {response.content}")
        scenario_type = "out_of_scope"
        reasoning = "파싱 실패"

    # 범위 외 질문이면 종료
    if scenario_type == "out_of_scope":
        final_response = "죄송합니다. 저는 통계 데이터 조회 전문 챗봇입니다. 인구, 경제, 사회 등의 통계 데이터 관련 질문을 해주세요."
        return Command(
            goto=END,
            update={
                "scenario_type": scenario_type,
                "final_response": final_response,
                "reasoning": reasoning,
            },
        )

    # 범위 내 질문이면 테이블 검색으로
    return Command(
        goto="search_tables",
        update={"scenario_type": scenario_type, "reasoning": reasoning},
    )
