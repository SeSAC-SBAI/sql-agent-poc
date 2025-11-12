from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import StatsChatbotState
from agents.nodes import (
    classify_intent,
    search_tables,
    request_clarification,
    generate_sql,
    execute_sql,
    process_data,
    analyze_insight,
    plan_visualization,
    generate_response,
)


def create_stats_chatbot_graph():
    """통계 챗봇 그래프 생성 및 컴파일"""

    # StateGraph 생성
    graph = StateGraph(StatsChatbotState)

    # 노드 추가
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("search_tables", search_tables)
    graph.add_node("request_clarification", request_clarification)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("process_data", process_data)
    graph.add_node("analyze_insight", analyze_insight)
    graph.add_node("plan_visualization", plan_visualization)
    graph.add_node("generate_response", generate_response)

    # 진입점 설정
    graph.set_entry_point("classify_intent")

    # 체크포인터 설정 (대화 상태 저장용)
    checkpointer = MemorySaver()

    # 그래프 컴파일
    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph


# 그래프 인스턴스 생성
stats_chatbot = create_stats_chatbot_graph()
