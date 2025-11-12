"""
SQL 생성 및 실행 통합 테스트
"""

import pytest
from agents.state import StatsChatbotState
from agents.nodes import generate_sql, execute_sql
from langgraph.types import Command


class TestSQLIntegration:
    """generate_sql + execute_sql 통합 테스트"""

    def test_sql_generation_and_execution_success(self):
        """SQL 생성 → 실행 전체 플로우 (정상)"""
        # 1단계: SQL 생성
        initial_state = StatsChatbotState(
            user_query="서울특별시 2016년 1월 총인구수 알려줘",
            scenario_type="single_value",
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계 테이블",
                }
            ],
        )

        sql_result = generate_sql(initial_state)

        # SQL이 생성되었는지 확인
        assert sql_result.goto == "execute_sql"
        assert "sql_query" in sql_result.update
        generated_sql = sql_result.update["sql_query"]
        print(f"\n생성된 SQL: {generated_sql}")

        # 2단계: SQL 실행
        execute_state = StatsChatbotState(
            user_query=initial_state["user_query"],
            scenario_type=initial_state["scenario_type"],
            sql_query=generated_sql,
        )

        execute_result = execute_sql(execute_state)

        # 실행 결과 확인
        assert execute_result.goto == "process_data"
        assert "query_result" in execute_result.update
        assert len(execute_result.update["query_result"]) > 0

        print(f"조회 결과: {execute_result.update['query_result'][:3]}")  # 처음 3개만

    def test_sql_generation_with_error_and_retry(self):
        """SQL 생성 → 실행 실패 → 재생성"""
        # 1단계: 잘못된 SQL 생성 (의도적으로 틀린 쿼리)
        initial_state = StatsChatbotState(
            user_query="서울시 인구",
            scenario_type="single_value",
            sql_query="SELECT * FROM wrong_table_name;",  # 의도적 오류
            sql_retry_count=0,
        )

        # 실행 실패
        execute_result = execute_sql(initial_state)

        assert execute_result.goto == "generate_sql"
        assert "sql_error" in execute_result.update
        assert execute_result.update["sql_retry_count"] == 1

        # 2단계: 에러 피드백과 함께 재생성
        retry_state = StatsChatbotState(
            user_query=initial_state["user_query"],
            scenario_type=initial_state["scenario_type"],
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계",
                }
            ],
            sql_error=execute_result.update["sql_error"],
            sql_retry_count=execute_result.update["sql_retry_count"],
        )

        regenerate_result = generate_sql(retry_state)

        # 재생성된 SQL 확인
        assert regenerate_result.goto == "execute_sql"
        regenerated_sql = regenerate_result.update["sql_query"]
        print(f"\n재생성된 SQL: {regenerated_sql}")

    def test_sql_integration_count_query(self):
        """집계 쿼리 (COUNT) 통합 테스트"""
        # SQL 생성
        initial_state = StatsChatbotState(
            user_query="전국 인구 데이터가 총 몇 개야?",
            scenario_type="simple_aggregation",
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계",
                }
            ],
        )

        sql_result = generate_sql(initial_state)
        generated_sql = sql_result.update["sql_query"]
        print(f"\n생성된 COUNT SQL: {generated_sql}")

        # SQL 실행
        execute_state = StatsChatbotState(
            user_query=initial_state["user_query"],
            scenario_type=initial_state["scenario_type"],
            sql_query=generated_sql,
        )

        execute_result = execute_sql(execute_state)

        # 결과 확인
        assert execute_result.goto == "process_data"
        query_result = execute_result.update["query_result"]
        assert len(query_result) > 0
        print(f"COUNT 결과: {query_result}")

    def test_sql_integration_no_result(self):
        """데이터 없는 경우 통합 테스트"""
        # SQL 생성
        initial_state = StatsChatbotState(
            user_query="존재하지않는지역 인구수",
            scenario_type="single_value",
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계",
                }
            ],
        )

        sql_result = generate_sql(initial_state)
        generated_sql = sql_result.update["sql_query"]

        # SQL 실행
        execute_state = StatsChatbotState(
            user_query=initial_state["user_query"],
            scenario_type=initial_state["scenario_type"],
            sql_query=generated_sql,
        )

        execute_result = execute_sql(execute_state)

        # 결과 없음 확인
        assert execute_result.goto == "__end__"
        assert "조회 결과가 없습니다" in execute_result.update["final_response"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s: print 출력 보기
