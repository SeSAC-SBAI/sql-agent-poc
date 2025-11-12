from typing import Literal
from langgraph.types import Command
from langgraph.graph import END
from agents.state import StatsChatbotState


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
    # TODO: LLM API 호출하여 질문 분류
    scenario_type = ""  # LLM 결과

    # 범위 외 질문이면 종료
    if scenario_type == "out_of_scope":
        final_response = "죄송합니다. 저는 통계 데이터 조회 전문 챗봇입니다. 인구, 경제, 사회 등의 통계 데이터 관련 질문을 해주세요."
        return Command(
            goto=END,
            update={"scenario_type": scenario_type, "final_response": final_response},
        )

    # 범위 내 질문이면 테이블 검색으로
    return Command(goto="search_tables", update={"scenario_type": scenario_type})


def search_tables(
    state: StatsChatbotState,
) -> Command[Literal["request_clarification", "generate_sql", "__end__"]]:
    """
    2. 테이블 및 스키마 검색 노드 (Data 단계)

    벡터DB에서 질문과 관련된 테이블 검색
    - 질문을 임베딩하여 유사도 검색
    - 유사도 임계값(0.7) 필터링
    - 테이블명 + 스키마 정보 반환
    """
    # TODO: 질문 임베딩
    # TODO: 벡터DB 검색
    # TODO: 유사도 필터링

    tables_info = []  # 검색 결과
    clarification_count = state.get("clarification_count", 0)

    # 테이블 없음 & 재시도 0회 → 추가 정보 요청
    if not tables_info and clarification_count == 0:
        return Command(
            goto="request_clarification", update={"tables_info": tables_info}
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
    - LLM이 부족한 정보 파악
    - 재질문 생성
    - interrupt()로 사용자 입력 대기
    """
    # TODO: LLM으로 부족한 정보 파악
    # TODO: 재질문 생성
    # TODO: interrupt()로 사용자 답변 대기

    clarification_message = "좀 더 구체적으로 알려주시겠어요? (예: 어느 지역? 몇 년도?)"

    # 사용자 답변 받으면 질문 분류부터 재시작
    return Command(
        goto="classify_intent",
        update={
            "clarification_count": state["clarification_count"] + 1,
            # TODO: interrupt로 받은 답변을 user_query에 추가
        },
    )


def generate_sql(state: StatsChatbotState) -> Command[Literal["execute_sql"]]:
    """
    4. SQL 생성 노드 (LLM 단계)

    자연어 질문과 테이블 스키마 정보를 바탕으로 SQL 쿼리 생성
    - 이전 에러가 있으면 에러 메시지도 함께 전달
    """
    # TODO: LLM API 호출하여 SQL 생성
    # TODO: sql_error가 있으면 피드백으로 전달

    sql_query = ""  # LLM 생성 결과

    return Command(goto="execute_sql", update={"sql_query": sql_query})


def execute_sql(
    state: StatsChatbotState,
) -> Command[Literal["generate_sql", "process_data", "__end__"]]:
    """
    5. SQL 실행 및 결과 확인 노드 (Data 단계)

    생성된 SQL을 실제 DB에 실행하고 결과 확인
    - Exception 발생 시 에러 메시지 저장 및 재시도
    - 실행 성공 시 결과 데이터 확인
    """
    # TODO: SQL 실행
    # TODO: Exception 처리
    # TODO: 결과 데이터 확인

    try:
        query_result = []  # DB 실행 결과

        # 데이터 없음 → 종료
        if not query_result:
            return Command(
                goto=END,
                update={
                    "query_result": query_result,
                    "final_response": "조회 결과가 없습니다.",
                },
            )

        # 데이터 있음 → 후처리로
        return Command(
            goto="process_data",
            update={"query_result": query_result, "sql_error": None},
        )

    except Exception as e:
        sql_retry_count = state.get("sql_retry_count", 0)

        # 재시도 3회 미만 → SQL 재생성
        if sql_retry_count < 3:
            return Command(
                goto="generate_sql",
                update={"sql_error": str(e), "sql_retry_count": sql_retry_count + 1},
            )

        # 재시도 3회 이상 → 종료
        return Command(
            goto=END,
            update={
                "sql_error": str(e),
                "final_response": "SQL 쿼리 생성에 실패했습니다.",
            },
        )


def process_data(state: StatsChatbotState) -> Command[Literal["analyze_insight"]]:
    """
    6. 데이터 후처리 노드 (LLM 단계)

    시나리오 타입에 따라 추가 계산 수행
    - derived_calculation, multi_step_analysis: LLM이 계산 수행
    - 나머지: 계산 없이 패스
    """
    scenario_type = state["scenario_type"]

    # 계산이 필요한 시나리오
    if scenario_type in ["derived_calculation", "multi_step_analysis"]:
        # TODO: LLM으로 계산 수행 (증가율, 비율 등)
        processed_data = {}  # LLM 계산 결과
    else:
        # 계산 불필요
        processed_data = None

    return Command(goto="analyze_insight", update={"processed_data": processed_data})


def analyze_insight(state: StatsChatbotState) -> Command[Literal["plan_visualization"]]:
    """
    7. 인사이트 분석 노드 (LLM 단계)

    데이터를 분석하여 경향, 패턴, 특이사항 파악
    - 예: "2020년 이후 감소하다가 2023년부터 회복"
    """
    # TODO: LLM API 호출하여 인사이트 분석

    insight = ""  # LLM 분석 결과

    return Command(goto="plan_visualization", update={"insight": insight})


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


def generate_response(state: StatsChatbotState) -> Dict[str, Any]:
    """
    9. 응답 생성 노드 (LLM 단계)

    최종 응답 생성
    - 자연어 답변
    - 데이터 (테이블)
    - 인사이트
    - 시각화 차트 (있으면)
    """
    # TODO: LLM으로 최종 응답 생성
    # TODO: 데이터 + 인사이트 + 차트 통합

    return {
        "final_response": "",
    }
