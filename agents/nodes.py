import json
from typing import Dict, Any, Literal, Optional, List
from langgraph.types import Command, interrupt
from langgraph.graph import END
from agents.state import StatsChatbotState
from agents.helpers import (
    extract_calculation_hints,
    validate_calculation_result,
    get_llm,
    get_llm_text,
)
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
    llm = get_llm()

    # 프롬프트 포맷팅
    prompt = CLASSIFY_INTENT_PROMPT.format(user_query=user_query)

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

    # 벡터DB에서 테이블 검색 (거리 1.5 이하만)
    # tables_info = search_tables_from_db(state["user_query"], n_results=1, threshold=1.5)

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


def generate_sql(state: StatsChatbotState) -> Command[Literal["execute_sql"]]:
    """
    4. SQL 생성 노드 (LLM 단계)

    자연어 질문과 테이블 스키마 정보를 바탕으로 SQL 쿼리 생성
    - 이전 에러가 있으면 에러 메시지도 함께 전달
    """
    from utils.prompts import SQL_GENERATION_PROMPT

    # LLM 초기화
    llm = get_llm_text()

    # 테이블 정보 포맷팅
    tables_info_str = "\n\n".join(
        [
            f"### {table['table_name']}\n"
            f"설명: {table['description']}\n"
            f"컬럼: {table['columns']}\n"
            f"시간컬럼: {table.get('period_column', '년월')}\n"
            f"주의사항: {table.get('caution', '없음')}"
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

    # ===== 디버깅 =====
    print(f"\n[DEBUG] SQL 생성 시도 {state.get('sql_retry_count', 0) + 1}회")
    print(f"[DEBUG] 사용 테이블: {[t['table_name'] for t in state['tables_info']]}")
    # ===== 추가 =====

    # LLM 호출
    response = llm.invoke(prompt)

    # ===== 더 자세한 디버깅 =====
    print(f"[DEBUG] LLM 응답 타입: {type(response)}")
    print(f"[DEBUG] LLM 응답 전체: {response}")
    print(f"[DEBUG] content 길이: {len(response.content) if response.content else 0}")

    if hasattr(response, "response_metadata"):
        print(f"[DEBUG] metadata: {response.response_metadata}")
    # ===== 추가 끝 =====

    sql_query = response.content.strip()

    # ===== 디버깅 =====
    print(f"[DEBUG] 생성된 SQL (raw): {repr(sql_query[:100])}")
    # ===== 추가 =====

    # SQL 쿼리 후처리
    # 1. 큰따옴표 제거
    sql_query = sql_query.strip('"').strip("'")

    # 2. 마크다운 코드 블록 제거
    if sql_query.startswith("```"):
        sql_query = sql_query.split("```")[1]
        if sql_query.startswith("sql"):
            sql_query = sql_query[3:]
        sql_query = sql_query.strip()

    # 세미콜론 자동 추가
    if not sql_query.endswith(";"):
        sql_query += ";"

    # ===== 디버깅 =====
    print(f"[DEBUG] 최종 SQL: {sql_query}")
    # ===== 추가 =====

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

    # print("=" * 60)
    # print("DEBUG - execute_sql 시작")
    # print(f"DEBUG - SQL: {state['sql_query']}")
    # print("=" * 60)

    try:
        # DB 연결 및 SQL 실행
        db = db_manager.get_db()
        result_str = db.run(state["sql_query"])

        # print(f"DEBUG - result_str: {repr(result_str)}")
        # print(f"DEBUG - result_str type: {type(result_str)}")
        # print(f"DEBUG - result_str bool: {bool(result_str)}")

        # 문자열 결과를 리스트로 파싱
        query_result = ast.literal_eval(result_str) if result_str else []

        # print(f"DEBUG - query_result: {query_result}")
        # print(f"DEBUG - query_result type: {type(query_result)}")
        # print(f"DEBUG - query_result bool: {bool(query_result)}")
        # print(f"DEBUG - len: {len(query_result)}")
        # print("=" * 60)

        # 데이터 없음 → 재시도 체크
        if not query_result:
            sql_retry_count = state.get("sql_retry_count", 0)

            # 재시도 2회 미만 → SQL 재생성
            if sql_retry_count < 2:
                return Command(
                    goto="generate_sql",
                    update={
                        "query_result": [],
                        "sql_error": "조회 결과가 없습니다. 쿼리를 수정해주세요.",
                        "sql_retry_count": sql_retry_count + 1,
                    },
                )

            # 재시도 2회 이상 → 종료
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
        # print(f"DEBUG - Exception 발생: {e}")
        # print(f"DEBUG - Exception type: {type(e)}")
        # print("=" * 60)

        sql_retry_count = state.get("sql_retry_count", 0)

        # 재시도 2회 미만 → SQL 재생성
        if sql_retry_count < 2:
            return Command(
                goto="generate_sql",
                update={"sql_error": str(e), "sql_retry_count": sql_retry_count + 1},
            )

        # 재시도 2회 이상 → 종료
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
    from utils.prompts import DATA_PROCESSING_PROMPT

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
    from utils.prompts import INSIGHT_ANALYSIS_PROMPT

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
    from utils.prompts import RESPONSE_GENERATION_PROMPT

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
