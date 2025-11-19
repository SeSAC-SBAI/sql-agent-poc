"""최종 응답 생성 노드"""

from typing import Literal
from langgraph.types import Command
from langgraph.graph import END

from agents.state import StatsChatbotState
from agents.helpers import get_llm_text
from utils.prompts import RESPONSE_GENERATION_PROMPT


def generate_response(
    state: StatsChatbotState,
) -> Command[Literal["__end__"]]:
    """
    9. 응답 생성 노드 (LLM 단계)

    최종 응답 생성
    - 자연어 답변
    - 데이터 (테이블)
    - 인사이트
    - 시각화 차트 (있으면)
    """
    try:
        llm = get_llm_text()

        # 응답에 포함할 데이터 결정 (안전하게)
        data = state.get("processed_data") or state.get("query_result") or "데이터 없음"

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
            user_query=state.get("user_query", "질문 없음"),
            data=str(data)[:1000],
            insight=insight,
            chart_info=chart_info,
        )

        # LLM 호출
        response = llm.invoke(prompt)
        final_response = response.content.strip()

    except Exception as e:
        print(f"응답 생성 실패: {e}")
        print(f"State keys: {list(state.keys())}")
        # Fallback
        data = state.get("processed_data") or state.get("query_result") or "데이터 없음"
        insight = state.get("insight", "")
        final_response = (
            f"조회 결과:\n{str(data)}\n\n{insight}"
            if data != "데이터 없음"
            else "답변을 생성하지 못했습니다."
        )

    return Command(goto=END, update={"final_response": final_response})
