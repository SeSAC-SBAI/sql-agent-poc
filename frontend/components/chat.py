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
)
from frontend.utils.format import (
    format_sql_result,
    extract_sql_from_response,
    extract_column_names,
)
from agents.graph import create_stats_chatbot_graph
from agents.nodes.content import format_answer_by_style
from database.vector_db import get_vectorstore, get_query_embeddings
from database.metadata_manager import get_metadata_manager
from frontend.utils.format import style_dataframe_with_highlight


@st.cache_resource
def initialize_graph():
    """그래프 초기화 (캐싱)"""
    manager = get_metadata_manager()
    embeddings = get_query_embeddings()
    vectorstore = get_vectorstore()
    graph = create_stats_chatbot_graph()
    return graph


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

    for idx, message in enumerate(get_messages()):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            metadata = message.get("metadata", {})

            if metadata.get("sql_query"):
                with st.expander("실행된 SQL"):
                    st.code(metadata["sql_query"], language="sql")

            # 데이터 테이블 - chart_data 우선 사용
            if metadata.get("query_result"):
                display_data = metadata.get("chart_data") or metadata["query_result"]

                # DataFrame 변환 (extended_sql 기준으로 컬럼명 추출)
                if isinstance(display_data, list) and display_data:
                    sql_query = metadata.get("extended_sql") or metadata.get(
                        "sql_query", ""
                    )
                    col_names = extract_column_names(sql_query, len(display_data[0]))
                    df = pd.DataFrame(display_data, columns=col_names)
                else:
                    df = format_sql_result(display_data)

                if isinstance(df, pd.DataFrame) and not df.empty:
                    with st.expander("데이터 테이블"):
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            target = metadata.get("target_value")
                            styled_df = style_dataframe_with_highlight(df, target)
                            st.dataframe(
                                styled_df,
                                hide_index=True,
                                # height=400,
                                use_container_width=True,
                            )
            if metadata.get("chart_spec"):
                from frontend.components.visualization import create_chart

                query_result = metadata.get("chart_data") or metadata["query_result"]
                sql_query = metadata.get("extended_sql") or metadata.get(
                    "sql_query", ""
                )
                chart_spec = metadata["chart_spec"]
                target_value = metadata.get("target_value")

                if isinstance(query_result, list) and query_result:
                    col_names = extract_column_names(sql_query, len(query_result[0]))

                    df = pd.DataFrame(query_result, columns=col_names)
                    df.columns = [str(col) for col in df.columns]

                elif isinstance(query_result, pd.DataFrame):
                    df = query_result
                else:
                    df = None

                if df is not None and not df.empty:
                    chart = create_chart(df, chart_spec, target_value)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    else:
                        st.warning("차트 생성 중 오류가 발생했습니다.")

            if message["role"] == "assistant" and metadata:
                print(
                    f"[DEBUG] 메시지 {idx}: assistant={message['role']=='assistant'}, metadata={bool(metadata)}"
                )
                print(
                    f"[DEBUG] metadata keys: {list(metadata.keys()) if metadata else 'None'}"
                )

                if st.button("📊 컨텐츠 생성", key=f"extra_{idx}"):
                    st.session_state[f"show_options_{idx}"] = True

                if st.session_state.get(f"show_options_{idx}"):
                    render_content_buttons(idx, message, metadata)

            else:
                print(
                    f"[DEBUG] 메시지 {idx} 스킵: role={message['role']}, metadata={bool(metadata)}"
                )

    is_processing = st.session_state.get("is_processing", False)

    if prompt := st.chat_input(
        "통계 데이터에 대해 질문해보세요...", disabled=is_processing
    ):
        handle_user_input(prompt, graph)


def render_content_buttons(message_idx: int, message: dict, metadata: dict):
    """콘텐츠 생성 버튼 렌더링"""

    st.markdown("---")
    st.markdown("### 📝 다른 형식으로 변환")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button(
            "📰 기사", key=f"reporter_{message_idx}", use_container_width=True
        ):
            st.session_state[f"selected_style_{message_idx}"] = "reporter"

    with col2:
        if st.button("📄 논문", key=f"paper_{message_idx}", use_container_width=True):
            st.session_state[f"selected_style_{message_idx}"] = "paper"

    with col3:
        if st.button("✍️ 블로그", key=f"blog_{message_idx}", use_container_width=True):
            st.session_state[f"selected_style_{message_idx}"] = "blog"

    selected_style = st.session_state.get(f"selected_style_{message_idx}")
    if selected_style:
        style_names = {"reporter": "기자", "paper": "논문", "blog": "블로그"}

        st.markdown(f"**{style_names[selected_style]} 스타일 생성**")

        with st.form(key=f"content_form_{message_idx}"):
            style_request = st.text_input(
                "추가 요구사항 (선택)",
                placeholder="예: 객관적이고 간결하게",
            )

            submitted = st.form_submit_button("생성")

        if submitted:
            with st.spinner(f"{style_names[selected_style]} 스타일 생성 중..."):
                try:
                    messages = get_messages()
                    user_query = (
                        messages[message_idx - 1]["content"] if message_idx > 0 else ""
                    )

                    styled_content = format_answer_by_style(
                        base_answer=message["content"],
                        user_query=user_query,
                        style=selected_style,
                        style_request=style_request if style_request else None,
                        query_result=metadata.get("query_result"),
                        insight=metadata.get("insight"),
                        processed_data=metadata.get("processed_data"),
                        tables_info=metadata.get("tables_info"),
                    )

                    st.markdown("---")
                    st.markdown(f"**📰 {style_names[selected_style]} 스타일 결과**")
                    st.markdown(styled_content)

                    del st.session_state[f"selected_style_{message_idx}"]

                except Exception as e:
                    st.error(f"콘텐츠 생성 중 오류 발생: {str(e)}")


def render_welcome_message():
    """웰컴 메시지 표시"""
    from frontend.components.welcome import render_welcome

    render_welcome()


def handle_user_input(prompt: str, graph):
    """사용자 입력 처리"""

    st.session_state.is_processing = True

    add_message("user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            try:
                messages = get_messages()
                conversation_history = "\n".join(
                    [f"{msg['role']}: {msg['content']}" for msg in messages[-4:]]
                )

                state = {
                    "user_query": prompt,
                    "conversation_history": conversation_history,
                }

                config = {"configurable": {"thread_id": get_thread_id()}}

                final_state = graph.invoke(state, config=config)

                response = final_state.get(
                    "final_response", "답변을 생성하지 못했습니다."
                )
                st.markdown(response)

                # chart_spec이 있으면 시각화
                if final_state.get("chart_spec"):
                    from frontend.components.visualization import create_chart

                    query_result = final_state.get("chart_data") or final_state.get(
                        "query_result"
                    )
                    sql_query = final_state.get("extended_sql") or final_state.get(
                        "sql_query", ""
                    )
                    chart_spec = final_state["chart_spec"]
                    target_value = final_state.get("target_value")

                    if isinstance(query_result, list) and query_result:
                        col_names = extract_column_names(
                            sql_query, len(query_result[0])
                        )

                        df = pd.DataFrame(query_result, columns=col_names)
                        df.columns = [str(col) for col in df.columns]

                    elif isinstance(query_result, pd.DataFrame):
                        df = query_result
                    else:
                        df = None

                    if df is not None and not df.empty:
                        chart = create_chart(df, chart_spec, target_value)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                        else:
                            st.warning("차트 생성 중 오류가 발생했습니다.")

                # SQL 쿼리 표시
                if final_state.get("sql_query"):
                    with st.expander("실행된 SQL"):
                        st.code(final_state["sql_query"], language="sql")

                # 데이터 테이블 표시 - chart_data 우선 사용
                if final_state.get("query_result"):
                    display_data = (
                        final_state.get("chart_data") or final_state["query_result"]
                    )

                    # DataFrame 변환 (extended_sql 기준으로 컬럼명 추출)
                    if isinstance(display_data, list) and display_data:
                        sql_query = final_state.get("extended_sql") or final_state.get(
                            "sql_query", ""
                        )

                        print(f"[DEBUG] SQL: {sql_query}")
                        print(f"[DEBUG] 데이터 첫 행: {display_data[0]}")

                        col_names = extract_column_names(
                            sql_query, len(display_data[0])
                        )

                        print(
                            f"[DEBUG] 추출된 컬럼명: {col_names}, 실제 컬럼 수: {len(display_data[0])}"
                        )

                        df = pd.DataFrame(display_data, columns=col_names)
                    else:
                        df = format_sql_result(display_data)

                    if isinstance(df, pd.DataFrame) and not df.empty:
                        with st.expander("데이터 테이블"):
                            col1, col2, col3 = st.columns([1, 2, 1])
                            with col2:
                                target = final_state.get("target_value")
                                styled_df = style_dataframe_with_highlight(df, target)
                                st.dataframe(
                                    styled_df,
                                    hide_index=True,
                                    # height=400,
                                    use_container_width=True,
                                )
                # 메타데이터 저장
                metadata = {
                    "sql_query": final_state.get("sql_query"),
                    "query_result": final_state.get("query_result"),
                    "chart_data": final_state.get("chart_data"),
                    "extended_sql": final_state.get("extended_sql"),
                    "target_value": final_state.get("target_value"),
                    "chart_spec": final_state.get("chart_spec"),
                    "scenario_type": final_state.get("scenario_type"),
                    "insight": final_state.get("insight"),
                    "processed_data": final_state.get("processed_data"),
                    "tables_info": final_state.get("tables_info"),
                }

                add_message("assistant", response, metadata)

            except Exception as e:
                error_msg = f"오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                add_message("assistant", error_msg, {})

            finally:
                st.session_state.is_processing = False
                st.rerun()
