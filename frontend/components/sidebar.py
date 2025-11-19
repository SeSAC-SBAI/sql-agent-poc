"""사이드바 컴포넌트"""

import streamlit as st
from frontend.utils.session import (
    get_session_id,
    get_thread_id,
    clear_messages,
    get_messages,
)


def render_sidebar():
    """사이드바 렌더링"""

    with st.sidebar:
        st.title("Easystat Q")

        st.markdown("---")

        st.subheader("정보")
        st.markdown(
            """
        <p>
            이 챗봇은 KOSIS(국가통계포털) 데이터를 자연어로 조회할 수 있도록 도와줍니다.
            SQL 쿼리를 자동으로 생성하고 실행하여 결과를 보여드립니다.
        </p>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        st.subheader("대화 히스토리")
        message_count = len(get_messages())
        st.write(f"총 {message_count}개의 메시지")

        if st.button("대화 초기화", use_container_width=True):
            clear_messages()
            st.rerun()
