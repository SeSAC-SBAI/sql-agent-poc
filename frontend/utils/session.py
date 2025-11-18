"""세션 상태 관리 유틸리티"""

import streamlit as st
import uuid
from typing import List, Dict, Any


def initialize_session():
    """세션 상태 초기화"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"streamlit-{st.session_state.session_id}"
    
    if "graph" not in st.session_state:
        st.session_state.graph = None
    
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False


def add_message(role: str, content: str, metadata: Dict[str, Any] = None):
    """메시지 추가"""
    message = {
        "role": role,
        "content": content,
        "metadata": metadata or {}
    }
    st.session_state.messages.append(message)


def clear_messages():
    """메시지 히스토리 초기화"""
    st.session_state.messages = []
    st.session_state.thread_id = f"streamlit-{uuid.uuid4()}"


def get_messages() -> List[Dict[str, Any]]:
    """메시지 히스토리 반환"""
    return st.session_state.messages


def get_thread_id() -> str:
    """현재 스레드 ID 반환"""
    return st.session_state.thread_id


def set_graph(graph):
    """그래프 인스턴스 설정"""
    st.session_state.graph = graph


def get_graph():
    """그래프 인스턴스 반환"""
    return st.session_state.graph


def get_session_id() -> str:
    """현재 세션 ID 반환"""
    return st.session_state.session_id

