"""데이터 처리 및 인사이트 분석 노드"""

import json
from typing import Literal
from langgraph.types import Command

from agents.state import StatsChatbotState
from agents.helpers import (
    extract_calculation_hints,
    validate_calculation_result,
    get_llm,
)
from utils.prompts import DATA_PROCESSING_PROMPT, INSIGHT_ANALYSIS_PROMPT


def process_data(state: StatsChatbotState) -> Command[Literal["analyze_insight"]]:
    """
    6. 데이터 후처리 노드 (LLM 단계)

    시나리오 타입에 따라 추가 계산 수행
    - derived_calculation, multi_step_analysis: LLM이 계산 수행
    - 나머지: 계산 없이 패스
    """
    scenario_type = state["scenario_type"]

    # 계산이 필요한 시나리오가 아니면 패스
    if scenario_type not in ["derived_calculation", "multi_step_analysis"]:
        return Command(goto="analyze_insight", update={"processed_data": None})

    # 1. 질문에서 계산 힌트 추출
    hints = extract_calculation_hints(state["user_query"])

    # 2. LLM 초기화
    llm = get_llm()

    # 3. 프롬프트 포맷팅
    prompt = DATA_PROCESSING_PROMPT.format(
        user_query=state["user_query"],
        query_result=str(state["query_result"]),
        hints=", ".join(hints),
    )

    # 4. LLM 호출
    try:
        response = llm.invoke(prompt)

        # 5. JSON 파싱
        processed_data = json.loads(response.content)

        # 6. 결과 검증
        if validate_calculation_result(processed_data):
            return Command(
                goto="analyze_insight", update={"processed_data": processed_data}
            )

    except (json.JSONDecodeError, Exception) as e:
        print(f"데이터 처리 실패: {e}")

    # 7. 실패 시 원본 데이터 반환
    fallback_data = {
        "calculated_data": state["query_result"],
        "description": "원본 데이터",
    }
    return Command(goto="analyze_insight", update={"processed_data": fallback_data})


def analyze_insight(state: StatsChatbotState) -> Command[Literal["plan_visualization"]]:
    """
    7. 인사이트 분석 노드 (LLM 단계)

    데이터를 분석하여 경향, 패턴, 특이사항 파악
    - 예: "2020년 이후 감소하다가 2023년부터 회복"
    """
    # LLM 초기화
    llm = get_llm()

    # 분석할 데이터 결정
    # processed_data가 있으면 사용, 없으면 query_result 사용
    if state.get("processed_data"):
        data_to_analyze = state["processed_data"]
    else:
        data_to_analyze = state["query_result"]

    # 프롬프트 포맷팅
    prompt = INSIGHT_ANALYSIS_PROMPT.format(
        user_query=state["user_query"], data=str(data_to_analyze)
    )

    # LLM 호출
    try:
        response = llm.invoke(prompt)
        insight = response.content.strip()
    except Exception as e:
        print(f"인사이트 분석 실패: {e}")
        insight = ""  # 실패 시 빈 문자열

    return Command(goto="plan_visualization", update={"insight": insight})
