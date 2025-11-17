"""SQL 생성 및 실행 노드"""

import ast
from typing import Literal
from langgraph.types import Command
from langgraph.graph import END

from agents.state import StatsChatbotState
from agents.helpers import get_llm_text
from utils.prompts import SQL_GENERATION_PROMPT


def generate_sql(state: StatsChatbotState) -> Command[Literal["execute_sql"]]:
    """
    4. SQL 생성 노드 (LLM 단계)

    자연어 질문과 테이블 스키마 정보를 바탕으로 SQL 쿼리 생성
    - 이전 에러가 있으면 에러 메시지도 함께 전달
    """
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

    # 디버깅
    print(f"\n[DEBUG] SQL 생성 시도 {state.get('sql_retry_count', 0) + 1}회")
    print(f"[DEBUG] 사용 테이블: {[t['table_name'] for t in state['tables_info']]}")

    # LLM 호출
    response = llm.invoke(prompt)

    # 디버깅
    print(f"[DEBUG] LLM 응답 타입: {type(response)}")
    print(f"[DEBUG] LLM 응답 전체: {response}")
    print(f"[DEBUG] content 길이: {len(response.content) if response.content else 0}")

    if hasattr(response, "response_metadata"):
        print(f"[DEBUG] metadata: {response.response_metadata}")

    sql_query = response.content.strip()

    print(f"[DEBUG] 생성된 SQL (raw): {repr(sql_query[:100])}")

    # SQL 쿼리 후처리
    # 1. 큰따옴표 제거
    sql_query = sql_query.strip('"').strip("'")

    # 2. 마크다운 코드 블록 제거
    if sql_query.startswith("```"):
        sql_query = sql_query.split("```")[1]
        if sql_query.startswith("sql"):
            sql_query = sql_query[3:]
        sql_query = sql_query.strip()

    # 3. 세미콜론 자동 추가
    if not sql_query.endswith(";"):
        sql_query += ";"

    print(f"[DEBUG] 최종 SQL: {sql_query}")

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

    try:
        # DB 연결 및 SQL 실행
        db = db_manager.get_db()
        result_str = db.run(state["sql_query"])

        # 문자열 결과를 리스트로 파싱
        query_result = ast.literal_eval(result_str) if result_str else []

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
