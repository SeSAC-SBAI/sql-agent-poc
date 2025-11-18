"""웰컴 화면 컴포넌트"""

import streamlit as st
from frontend.utils.constants import EXAMPLE_QUESTIONS, WELCOME_MESSAGE


def render_welcome():
    """웰컴 메시지 및 예시 질문 렌더링"""

    st.markdown(
        f"""
    <div class="welcome-card">
        <h2>{WELCOME_MESSAGE['title']}</h2>
        <p>{WELCOME_MESSAGE['description']}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("### 💡 예시 질문")

    cols = st.columns(min(len(EXAMPLE_QUESTIONS), 3))
    for idx, question in enumerate(EXAMPLE_QUESTIONS):
        col_idx = idx % 3
        with cols[col_idx]:
            if st.button(question, key=f"example_{idx}", use_container_width=True):
                st.session_state.example_question = question
                st.rerun()
