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

    # 질문들을 행 단위로 나누기 (3열씩)
    num_cols = 3
    for row_start in range(0, len(EXAMPLE_QUESTIONS), num_cols):
        cols = st.columns(num_cols)
        
        for col_idx in range(num_cols):
            question_idx = row_start + col_idx
            if question_idx < len(EXAMPLE_QUESTIONS):
                question = EXAMPLE_QUESTIONS[question_idx]
                with cols[col_idx]:
                    if st.button(question, key=f"example_{question_idx}", use_container_width=True):
                        st.session_state.example_question = question
                        st.rerun()