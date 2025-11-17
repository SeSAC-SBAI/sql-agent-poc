"""시각화 계획 노드"""

from typing import Literal
from langgraph.types import Command

from agents.state import StatsChatbotState


def plan_visualization(
    state: StatsChatbotState,
) -> Command[Literal["generate_response"]]:
    """
    8. 시각화 계획 노드 (LLM 단계)

    데이터와 시나리오 타입을 보고 시각화 필요 여부 및 차트 타입 결정
    - 선 그래프: 시간 변화, 트렌드
    - 막대 그래프: 비교, 순위
    - 파이 차트: 비율
    - 테이블: 정확한 수치
    """
    # TODO: LLM으로 시각화 필요 여부 판단
    # TODO: 필요시 차트 타입 및 스펙 생성

    chart_spec = None  # LLM 결정 결과 (없으면 None)

    return Command(goto="generate_response", update={"chart_spec": chart_spec})
