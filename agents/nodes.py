import json
from typing import Dict, Any, Literal, Optional, List
from langgraph.types import Command, interrupt
from langgraph.graph import END
from langchain_upstage import ChatUpstage
from agents.state import StatsChatbotState
from config.settings import settings
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

    # LLM 초기화
    llm = ChatUpstage(model=settings.MODEL_NAME, temperature=settings.TEMPERATURE)

    # 프롬프트 포맷팅
    prompt = CLASSIFY_INTENT_PROMPT.format(user_query=user_query)

    # LLM 호출
    response = llm.invoke(prompt)

    # JSON 파싱
    try:
        result = json.loads(response.content)
        scenario_type = result["scenario_type"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"JSON 파싱 실패: {e}")
        scenario_type = "out_of_scope"

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
    - 거리 임계값(1.5) 필터링
    - 테이블명 + 스키마 정보 반환
    """
    from database.vector_db import search_tables_from_db

    # 벡터DB에서 테이블 검색 (거리 1.5 이하만)
    tables_info = search_tables_from_db(state["user_query"], n_results=1, threshold=1.5)

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


def generate_sql(state: StatsChatbotState) -> Command[Literal["execute_sql"]]:
    """
    4. SQL 생성 노드 (LLM 단계)

    자연어 질문과 테이블 스키마 정보를 바탕으로 SQL 쿼리 생성
    - 이전 에러가 있으면 에러 메시지도 함께 전달
    """
    from utils.prompts import SQL_GENERATION_PROMPT

    # LLM 초기화
    llm = ChatUpstage(model=settings.MODEL_NAME, temperature=settings.TEMPERATURE)

    # 테이블 정보 포맷팅
    tables_info_str = "\n\n".join(
        [
            f"테이블명: {table['table_name']}\n"
            f"컬럼: {table['columns']}\n"
            f"설명: {table['description']}"
            for table in state["tables_info"]
        ]
    )

    # 에러 피드백 (재시도 시)
    error_feedback = ""
    if state.get("sql_error"):
        error_feedback = f"\n## 이전 시도 에러:\n{state['sql_error']}\n위 에러를 고려하여 SQL을 수정하세요."

    # 프롬프트 포맷팅
    prompt = SQL_GENERATION_PROMPT.format(
        user_query=state["user_query"],
        tables_info=tables_info_str,
        error_feedback=error_feedback,
    )

    # LLM 호출
    response = llm.invoke(prompt)
    sql_query = response.content.strip()

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
    from database.connection import db_manager
    import ast

    try:
        # DB 연결 및 SQL 실행
        db = db_manager.get_db()
        result_str = db.run(state["sql_query"])

        # 문자열 결과를 리스트로 파싱
        query_result = ast.literal_eval(result_str) if result_str else []

        # 데이터 없음 → 종료
        if not query_result:
            return Command(
                goto=END,
                update={
                    "query_result": [],
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


def generate_response(state: StatsChatbotState) -> Command[Literal["__end__"]]:
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

    final_response = ""  # LLM 생성 응답

    return Command(goto=END, update={"final_response": final_response})
