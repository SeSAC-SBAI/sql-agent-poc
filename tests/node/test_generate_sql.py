"""
generate_sql 노드 테스트
"""

import pytest
from agents.state import StatsChatbotState
from agents.nodes import generate_sql
from langgraph.types import Command


class TestGenerateSQL:
    """generate_sql 노드 테스트"""

    def test_generate_sql_success(self):
        """정상적으로 SQL이 생성되는 경우"""
        state = StatsChatbotState(
            user_query="서울시 2023년 인구수 알려줘",
            scenario_type="single_value",
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계 테이블",
                }
            ],
        )

        result = generate_sql(state)

        assert isinstance(result, Command)
        assert result.goto == "execute_sql"
        assert "sql_query" in result.update
        assert isinstance(result.update["sql_query"], str)
        assert len(result.update["sql_query"]) > 0

    def test_generate_sql_contains_table_name(self):
        """생성된 SQL에 테이블명이 포함되는지"""
        state = StatsChatbotState(
            user_query="부산시 인구 알려줘",
            scenario_type="single_value",
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계",
                }
            ],
        )

        result = generate_sql(state)

        sql_query = result.update["sql_query"]
        assert "population_gender_stats" in sql_query

    def test_generate_sql_with_error_feedback(self):
        """이전 에러가 있을 때 재생성"""
        state = StatsChatbotState(
            user_query="서울시 인구 알려줘",
            scenario_type="single_value",
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계",
                }
            ],
            sql_error="no such column: population",
            sql_retry_count=1,
        )

        result = generate_sql(state)

        assert isinstance(result, Command)
        assert result.goto == "execute_sql"
        assert "sql_query" in result.update

    def test_generate_sql_select_query(self):
        """SELECT 쿼리가 생성되는지"""
        state = StatsChatbotState(
            user_query="경기도 인구 조회",
            scenario_type="single_value",
            tables_info=[
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계",
                }
            ],
        )

        result = generate_sql(state)

        sql_query = result.update["sql_query"].upper()
        assert "SELECT" in sql_query

    def test_generate_sql_multiple_tables(self):
        """여러 테이블 정보가 있을 때"""
        state = StatsChatbotState(
            user_query="서울시 60대 인구 알려줘",
            scenario_type="single_value",
            tables_info=[
                {
                    "table_name": "population_age_stats",
                    "columns": "행정구역,년월,연령대,항목,값",
                    "description": "연령대별 인구 통계",
                },
                {
                    "table_name": "population_gender_stats",
                    "columns": "행정구역,년월,항목,값",
                    "description": "성별 인구 통계",
                },
            ],
        )

        result = generate_sql(state)

        assert isinstance(result, Command)
        assert "sql_query" in result.update


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
