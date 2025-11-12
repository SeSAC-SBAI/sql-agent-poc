"""
execute_sql 노드 테스트
"""

import pytest
from agents.state import StatsChatbotState
from agents.nodes import execute_sql
from langgraph.types import Command


class TestExecuteSQL:
    """execute_sql 노드 테스트"""

    def test_execute_sql_success_with_data(self):
        """SQL 실행 성공 + 데이터 있음"""
        state = StatsChatbotState(
            user_query="서울시 인구수 알려줘",
            sql_query="SELECT * FROM population_gender_stats WHERE 행정구역='서울특별시' LIMIT 1;",
            scenario_type="single_value",
        )

        result = execute_sql(state)

        assert isinstance(result, Command)
        assert result.goto == "process_data"
        assert "query_result" in result.update
        assert len(result.update["query_result"]) > 0
        assert isinstance(result.update["query_result"], list)

    def test_execute_sql_success_no_data(self):
        """SQL 실행 성공 + 데이터 없음"""
        state = StatsChatbotState(
            user_query="존재하지않는지역 인구수",
            sql_query="SELECT * FROM population_gender_stats WHERE 행정구역='존재하지않는지역';",
            scenario_type="single_value",
        )

        result = execute_sql(state)

        assert isinstance(result, Command)
        assert result.goto == "__end__"
        assert "조회 결과가 없습니다" in result.update["final_response"]

    def test_execute_sql_error_first_retry(self):
        """SQL 실행 실패 + 첫 재시도"""
        state = StatsChatbotState(
            user_query="서울시 인구",
            sql_query="SELECT * FROM wrong_table;",  # 잘못된 테이블명
            scenario_type="single_value",
            sql_retry_count=0,
        )

        result = execute_sql(state)

        assert isinstance(result, Command)
        assert result.goto == "generate_sql"
        assert "sql_error" in result.update
        assert result.update["sql_retry_count"] == 1

    def test_execute_sql_error_max_retry(self):
        """SQL 실행 실패 + 최대 재시도"""
        state = StatsChatbotState(
            user_query="서울시 인구",
            sql_query="SELECT * FROM wrong_table;",
            scenario_type="single_value",
            sql_retry_count=3,
        )

        result = execute_sql(state)

        assert isinstance(result, Command)
        assert result.goto == "__end__"
        assert "SQL 쿼리 생성에 실패" in result.update["final_response"]

    def test_execute_sql_result_parsing(self):
        """결과 파싱 확인 (문자열 → 리스트)"""
        state = StatsChatbotState(
            user_query="전국 인구수",
            sql_query="SELECT * FROM population_gender_stats WHERE 행정구역='전국' LIMIT 2;",
            scenario_type="single_value",
        )

        result = execute_sql(state)

        query_result = result.update["query_result"]
        assert isinstance(query_result, list)
        assert len(query_result) > 0
        assert isinstance(query_result[0], tuple)  # 각 행은 튜플

    def test_execute_sql_count_query(self):
        """COUNT 쿼리 실행"""
        state = StatsChatbotState(
            user_query="총 데이터 개수",
            sql_query="SELECT COUNT(*) FROM population_gender_stats;",
            scenario_type="simple_aggregation",
        )

        result = execute_sql(state)

        assert isinstance(result, Command)
        assert result.goto == "process_data"
        query_result = result.update["query_result"]
        assert len(query_result) == 1  # [(count,)]
        assert isinstance(query_result[0][0], int)  # 숫자


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
