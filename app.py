"""Streamlit 메인 앱"""

import streamlit as st
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from frontend.utils.session import initialize_session
from frontend.styles.premium import apply_premium_style
from frontend.components.sidebar import render_sidebar
from frontend.components.chat import render_chat

# 페이지 설정
st.set_page_config(
    page_title="통계청 SQL Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 프리미엄 스타일 적용
apply_premium_style()

# 세션 초기화
initialize_session()

# 사이드바 렌더링
render_sidebar()

# 메인 채팅 인터페이스
render_chat()
