"""최종 응답 생성 노드"""

from typing import Literal
from langgraph.types import Command
from langgraph.graph import END

from agents.state import StatsChatbotState
from agents.helpers import get_llm_text
from utils.prompts import RESPONSE_GENERATION_PROMPT


def generate_response(state: StatsChatbotState) -> Command[Literal["__end__"]]:
    """
    9. 응답 생성 노드 (LLM 단계)

    최종 응답 생성
    - 자연어 답변
    - 데이터 (테이블)
    - 인사이트
    - 시각화 차트 (있으면)
    """
    # LLM 초기화
    llm = get_llm_text()

    # 응답에 포함할 데이터 결정
    if state.get("processed_data"):
        data = state["processed_data"]
    else:
        data = state["query_result"]

    # 인사이트
    insight = state.get("insight", "")

    # 차트 정보
    chart_info = ""
    if state.get("chart_spec"):
        chart_info = f"시각화: {state['chart_spec'].get('chart_type', 'none')}"
    else:
        chart_info = "시각화 없음"

    # 프롬프트 포맷팅
    prompt = RESPONSE_GENERATION_PROMPT.format(
        user_query=state["user_query"],
        data=str(data),
        insight=insight,
        chart_info=chart_info,
    )

    # LLM 호출
    try:
        response = llm.invoke(prompt)
        final_response = response.content.strip()
    except Exception as e:
        print(f"응답 생성 실패: {e}")
        # Fallback: 간단한 응답
        final_response = f"조회 결과:\n{str(data)}\n\n{insight}"

    return Command(goto=END, update={"final_response": final_response})
