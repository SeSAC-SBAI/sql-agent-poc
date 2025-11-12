import pytest
from agents.nodes import classify_intent
from agents.state import StatsChatbotState


@pytest.fixture
def base_state():
    """기본 상태 fixture"""
    return StatsChatbotState(
        user_query="",
        scenario_type="",
        tables_info=[],
        sql_query="",
        sql_retry_count=0,
        sql_error=None,
        query_result=[],
        processed_data=None,
        insight="",
        chart_spec=None,
        final_response="",
        clarification_count=0,
        error=None,
    )


@pytest.mark.parametrize(
    "query,expected_type",
    [
        # 단순 조회
        ("서울시 2023년 인구수 알려줘", "single_value"),
        ("부산 2024년 10월 총인구는?", "single_value"),
        # 표 조회
        ("부산의 3년간 인구 데이터 보여줘", "table_view"),
        ("서울시 2020년부터 2024년까지 인구 변화", "table_view"),
        # 단순 집계
        ("전국 평균 인구수는?", "simple_aggregation"),
        ("인구가 가장 많은 도시는?", "simple_aggregation"),
        ("2024년 전국 총인구 합계", "simple_aggregation"),
        # 파생 계산
        ("부산의 3년간 인구 증가율 알려줘", "derived_calculation"),
        ("서울시 남녀 성별 비율은?", "derived_calculation"),
        # 다단계 분석
        ("전국에서 인구 증가율이 가장 높은 상위 5개 도시는?", "multi_step_analysis"),
        ("지역별 인구밀도 순위 알려줘", "multi_step_analysis"),
        # 범위 외
        ("오늘 날씨 어때?", "out_of_scope"),
        ("맛집 추천해줘", "out_of_scope"),
        ("파이썬 코드 작성해줘", "out_of_scope"),
    ],
)
def test_classify_intent_scenarios(base_state, query, expected_type):
    """다양한 시나리오 질문 분류 테스트"""
    # Given
    state = base_state.copy()
    state["user_query"] = query

    # When
    result = classify_intent(state)

    # Then
    assert hasattr(result, "update")
    assert hasattr(result, "goto")
    assert result.update["scenario_type"] == expected_type

    # 범위 외 질문은 END로, 나머지는 search_tables로
    if expected_type == "out_of_scope":
        assert result.goto == "__end__"
        assert "final_response" in result.update
    else:
        assert result.goto == "search_tables"


def test_classify_intent_single_value(base_state):
    """단순 조회 상세 테스트"""
    # Given
    state = base_state.copy()
    state["user_query"] = "서울시 2023년 10월 인구수 알려줘"

    # When
    result = classify_intent(state)

    # Then
    assert result.update["scenario_type"] == "single_value"
    assert result.goto == "search_tables"


def test_classify_intent_out_of_scope(base_state):
    """범위 외 질문 테스트"""
    # Given
    state = base_state.copy()
    state["user_query"] = "오늘 점심 메뉴 추천해줘"

    # When
    result = classify_intent(state)

    # Then
    assert result.update["scenario_type"] == "out_of_scope"
    assert result.goto == "__end__"
    assert "통계 데이터 조회 전문 챗봇" in result.update["final_response"]


def test_classify_intent_json_parse_error(base_state, monkeypatch):
    """JSON 파싱 실패 시 out_of_scope 처리 테스트"""
    # Given
    state = base_state.copy()
    state["user_query"] = "테스트 질문"

    # Mock LLM response to return invalid JSON
    class MockLLM:
        def invoke(self, prompt):
            class MockResponse:
                content = "invalid json"

            return MockResponse()

    from agents import nodes

    def mock_chat_upstage(*args, **kwargs):
        return MockLLM()

    monkeypatch.setattr(nodes, "ChatUpstage", mock_chat_upstage)

    # When
    result = classify_intent(state)

    # Then
    assert result.update["scenario_type"] == "out_of_scope"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
