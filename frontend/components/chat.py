"""채팅 인터페이스 컴포넌트"""

import streamlit as st
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.session import (
    add_message,
    get_messages,
    get_thread_id,
    get_graph,
    set_graph,
)
from frontend.utils.format import (
    format_sql_result,
    extract_sql_from_response,
    extract_column_names,
)
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
                df = format_sql_result(metadata["query_result"])
                if isinstance(df, pd.DataFrame) and not df.empty:
                    with st.expander("데이터 테이블"):
                        st.dataframe(df, use_container_width=True)

            if metadata.get("chart_spec"):
                from frontend.components.visualization import create_chart

                query_result = metadata["query_result"]
                sql_query = metadata.get("sql_query", "")
                chart_spec = metadata["chart_spec"]

                if isinstance(query_result, list) and query_result:
                    col_names = extract_column_names(sql_query, len(query_result[0]))

                    df = pd.DataFrame(query_result, columns=col_names)
                    df.columns = [str(col) for col in df.columns]

                    if len(df.columns) == 1 and chart_spec.get("x_column") == "항목":
                        df["항목"] = [f"값 {i+1}" for i in range(len(df))]

                elif isinstance(query_result, pd.DataFrame):
                    df = query_result
                else:
                    df = None

                if df is not None and not df.empty:
                    chart = create_chart(df, chart_spec)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    else:
                        st.warning("차트 생성 중 오류가 발생했습니다.")

    is_processing = st.session_state.get("is_processing", False)

    if prompt := st.chat_input(
        "통계 데이터에 대해 질문해보세요...", disabled=is_processing
    ):
        handle_user_input(prompt, graph)


def render_welcome_message():
    """웰컴 메시지 표시"""
    from frontend.components.welcome import render_welcome

    render_welcome()


def handle_user_input(prompt: str, graph):
    """사용자 입력 처리"""

    # 처리 시작
    st.session_state.is_processing = True

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

                response = final_state.get(
                    "final_response", "답변을 생성하지 못했습니다."
                )
                st.markdown(response)

                # chart_spec이 있으면 시각화
                if final_state.get("chart_spec") and final_state.get("query_result"):
                    from frontend.components.visualization import create_chart

                    query_result = final_state["query_result"]
                    sql_query = final_state.get("sql_query", "")
                    chart_spec = final_state["chart_spec"]

                    if isinstance(query_result, list) and query_result:
                        col_names = extract_column_names(
                            sql_query, len(query_result[0])
                        )

                        df = pd.DataFrame(query_result, columns=col_names)
                        df.columns = [str(col) for col in df.columns]

                        # 단일 컬럼인 경우 항목 컬럼 추가
                        if (
                            len(df.columns) == 1
                            and chart_spec.get("x_column") == "항목"
                        ):
                            df["항목"] = [f"값 {i+1}" for i in range(len(df))]

                    elif isinstance(query_result, pd.DataFrame):
                        df = query_result
                    else:
                        df = None

                    print(
                        f"[DEBUG handle_user_input] df.columns: {list(df.columns) if df is not None else 'None'}"
                    )

                    if df is not None and not df.empty:
                        print(f"[DEBUG] 차트 생성 중: {chart_spec}")
                        chart = create_chart(df, chart_spec)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                        else:
                            st.warning("차트 생성 중 오류가 발생했습니다.")

                # SQL 쿼리 표시
                if final_state.get("sql_query"):
                    with st.expander("실행된 SQL"):
                        st.code(final_state["sql_query"], language="sql")

                # 데이터 테이블 표시
                if final_state.get("query_result"):
                    df = format_sql_result(final_state["query_result"])
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        with st.expander("데이터 테이블"):
                            st.dataframe(df, use_container_width=True)

                # 메타데이터 저장
                metadata = {
                    "sql_query": final_state.get("sql_query"),
                    "query_result": final_state.get("query_result"),
                    "chart_spec": final_state.get("chart_spec"),
                    "scenario_type": final_state.get("scenario_type"),
                }

                add_message("assistant", response, metadata)

            except Exception as e:
                error_msg = f"오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                add_message("assistant", error_msg)

            finally:
                # 처리 완료 (에러 발생해도 반드시 실행)
                st.session_state.is_processing = False
