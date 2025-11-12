"""
search_tables 노드 테스트
"""

import pytest
from agents.state import StatsChatbotState
from agents.nodes import search_tables
from langgraph.types import Command


class TestSearchTables:
    """search_tables 노드 테스트"""

    def test_search_tables_success(self):
        """정상적으로 테이블을 찾는 경우"""
        state = StatsChatbotState(
            user_query="서울시 인구수 알려줘",
            scenario_type="single_value",
            clarification_count=0,
        )

        result = search_tables(state)

        assert isinstance(result, Command)
        assert result.goto == "generate_sql"
        assert len(result.update["tables_info"]) > 0
        assert "table_name" in result.update["tables_info"][0]

    def test_search_tables_no_result_first_try(self):
        """테이블을 못 찾고 첫 시도인 경우 - clarification 요청"""
        state = StatsChatbotState(
            user_query="완전 관련 없는 질문",
            scenario_type="single_value",
            clarification_count=0,
        )

        result = search_tables(state)

        assert isinstance(result, Command)
        assert result.goto == "request_clarification"
        assert result.update["tables_info"] == []

    def test_search_tables_no_result_second_try(self):
        """테이블을 못 찾고 재시도인 경우 - 종료"""
        state = StatsChatbotState(
            user_query="완전 관련 없는 질문",
            scenario_type="single_value",
            clarification_count=1,
        )

        result = search_tables(state)

        assert isinstance(result, Command)
        assert result.goto == "__end__"
        assert "죄송합니다" in result.update["final_response"]

    def test_search_tables_age_query(self):
        """연령 관련 질문 - population_age_stats 테이블 선택"""
        state = StatsChatbotState(
            user_query="서울에 60대 노인은 몇 명이야?",
            scenario_type="single_value",
            clarification_count=0,
        )

        result = search_tables(state)

        assert isinstance(result, Command)
        assert result.goto == "generate_sql"
        assert result.update["tables_info"][0]["table_name"] == "population_age_stats"

    def test_search_tables_gender_query(self):
        """성별 관련 질문 - population_gender_stats 테이블 선택"""
        state = StatsChatbotState(
            user_query="경기도 여자 인구는?",
            scenario_type="single_value",
            clarification_count=0,
        )

        result = search_tables(state)

        assert isinstance(result, Command)
        assert result.goto == "generate_sql"
        assert (
            result.update["tables_info"][0]["table_name"] == "population_gender_stats"
        )

    def test_search_tables_household_query(self):
        """세대수 관련 질문 - population_stats 테이블 선택"""
        state = StatsChatbotState(
            user_query="수원시의 세대수는?",
            scenario_type="single_value",
            clarification_count=0,
        )

        result = search_tables(state)

        assert isinstance(result, Command)
        assert result.goto == "generate_sql"
        assert result.update["tables_info"][0]["table_name"] == "population_stats"

    def test_search_tables_strict_threshold(self):
        """엄격한 threshold (1.0) - 테이블 못 찾음"""
        from database.vector_db import search_tables_from_db

        tables = search_tables_from_db(
            "서울시 인구수 알려줘", n_results=1, threshold=1.0
        )
        assert len(tables) == 0  # 거리 1.356이므로 1.0보다 크면 제외

    def test_search_tables_moderate_threshold(self):
        """적당한 threshold (1.5) - 테이블 찾음"""
        from database.vector_db import search_tables_from_db

        tables = search_tables_from_db(
            "서울시 인구수 알려줘", n_results=1, threshold=1.5
        )
        assert len(tables) == 1  # 거리 1.356이므로 통과
        assert tables[0]["table_name"] == "population_gender_stats"

    def test_search_tables_loose_threshold(self):
        """관대한 threshold (2.0) - 테이블 찾음"""
        from database.vector_db import search_tables_from_db

        tables = search_tables_from_db(
            "서울시 인구수 알려줘", n_results=1, threshold=2.0
        )
        assert len(tables) == 1  # 더 관대하므로 당연히 통과
        assert tables[0]["table_name"] == "population_gender_stats"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
