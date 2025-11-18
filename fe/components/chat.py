"""채팅 인터페이스 컴포넌트"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fe.utils.session import (
    add_message, get_messages, get_thread_id, get_graph, set_graph
)
from fe.utils.format import format_sql_result, extract_sql_from_response
from fe.components.visualization import render_visualization
from agents.graph import create_stats_chatbot_graph
from database.vector_db import get_vectorstore, get_query_embeddings
from database.metadata_manager import get_metadata_manager


def initialize_graph():
    """그래프 초기화"""
    if get_graph() is None:
        with st.spinner("챗봇 초기화 중..."):
            manager = get_metadata_manager()
            embeddings = get_query_embeddings()
            vectorstore = get_vectorstore()
            graph = create_stats_chatbot_graph()
            set_graph(graph)
    return get_graph()


def render_chat():
    """채팅 인터페이스 렌더링"""
    
    graph = initialize_graph()
    
    if "example_question" in st.session_state:
        prompt = st.session_state.example_question
        del st.session_state.example_question
        handle_user_input(prompt, graph)
        st.rerun()
    
    if not get_messages():
        render_welcome_message()
    
    for message in get_messages():
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            metadata = message.get("metadata", {})
            
            if metadata.get("sql_query"):
                with st.expander("실행된 SQL"):
                    st.code(metadata["sql_query"], language="sql")
            
            if metadata.get("query_result"):
                st.dataframe(format_sql_result(metadata["query_result"]))
            
            if metadata.get("chart_spec"):
                render_visualization(metadata["chart_spec"], metadata.get("query_result"))
    
    if prompt := st.chat_input("통계 데이터에 대해 질문해보세요..."):
        handle_user_input(prompt, graph)


def render_welcome_message():
    """웰컴 메시지 표시"""
    from fe.components.welcome import render_welcome
    render_welcome()


def handle_user_input(prompt: str, graph):
    """사용자 입력 처리"""
    
    add_message("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            try:
                state = {
                    "user_query": prompt,
                    "clarification_count": 0,
                    "sql_retry_count": 0,
                }
                
                config = {"configurable": {"thread_id": get_thread_id()}}
                
                final_state = graph.invoke(state, config=config)
                
                response = final_state.get("final_response", "답변을 생성하지 못했습니다.")
                st.markdown(response)
                
                metadata = {
                    "sql_query": final_state.get("sql_query"),
                    "query_result": final_state.get("query_result"),
                    "chart_spec": final_state.get("chart_spec"),
                    "scenario_type": final_state.get("scenario_type"),
                }
                
                if metadata["sql_query"]:
                    with st.expander("실행된 SQL"):
                        st.code(metadata["sql_query"], language="sql")
                
                if metadata["query_result"]:
                    st.dataframe(format_sql_result(metadata["query_result"]))
                
                if metadata["chart_spec"]:
                    render_visualization(metadata["chart_spec"], metadata["query_result"])
                
                add_message("assistant", response, metadata)
                
            except Exception as e:
                error_msg = f"오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                add_message("assistant", error_msg)


if __name__ == "__main__":
    render_chat()

