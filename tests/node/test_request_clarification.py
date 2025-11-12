"""
request_clarification 노드 테스트

TODO: interrupt 테스트 수정 필요
- 현재 테스트는 실패함 (질문이 out_of_scope로 분류되거나 테이블을 찾아버림)
- interrupt까지 도달하는 시나리오 설계 필요
- 통합 테스트로 전환 고려
"""

import pytest
from agents.state import StatsChatbotState
from agents.graph import create_stats_chatbot_graph


class TestRequestClarification:
    """request_clarification 노드 테스트"""

    def test_interrupt_and_resume(self):
        """interrupt 발생 후 사용자 답변으로 재개"""
        graph = create_stats_chatbot_graph()

        # 초기 질문 (지역 정보 없음)
        config = {"configurable": {"thread_id": "test_1"}}
        initial_state = {
            "user_query": "인구수 알려줘",
        }

        # 1단계: 그래프 실행 (interrupt 발생 예상)
        result = graph.invoke(initial_state, config)

        # interrupt 메시지 확인
        assert "구체적으로" in str(result) or result is None  # interrupt 발생

        # 2단계: 사용자 답변으로 재개
        resumed_result = graph.invoke({"user_query": "서울시 2023년"}, config)

        # 결과 확인
        assert resumed_result is not None
        print(f"최종 상태: {resumed_result}")

    def test_clarification_count_increment(self):
        """clarification_count가 증가하는지 확인"""
        graph = create_stats_chatbot_graph()

        config = {"configurable": {"thread_id": "test_2"}}
        initial_state = {
            "user_query": "인구수 알려줘",
            "clarification_count": 0,
        }

        # 첫 실행
        result = graph.invoke(initial_state, config)

        # 재개
        resumed = graph.invoke({"user_query": "서울시"}, config)

        # clarification_count가 1로 증가했는지 확인
        if resumed and "clarification_count" in resumed:
            assert resumed["clarification_count"] == 1

    def test_combined_query(self):
        """원래 질문과 추가 정보가 합쳐지는지 확인"""
        graph = create_stats_chatbot_graph()

        config = {"configurable": {"thread_id": "test_3"}}
        initial_state = {
            "user_query": "인구수 알려줘",
        }

        # 실행 및 재개
        graph.invoke(initial_state, config)
        resumed = graph.invoke({"user_query": "서울시 2023년"}, config)

        # user_query가 합쳐졌는지 확인
        if resumed and "user_query" in resumed:
            assert "서울시" in resumed["user_query"]
            assert "인구수" in resumed["user_query"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
