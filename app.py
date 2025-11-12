import streamlit as st
from config import settings
from agents.langgraph_agent import langgraph_agent_manager as sql_agent_manager

# 페이지 설정
st.set_page_config(
    page_title="통계청 인구 데이터 조회",
    page_icon="🏛️",
    layout="wide"
)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_initialized" not in st.session_state:
    st.session_state.agent_initialized = False

# Agent 초기화
@st.cache_resource
def initialize_agent():
    settings.validate()
    sql_agent_manager.initialize()
    return sql_agent_manager

try:
    agent_manager = initialize_agent()
    st.session_state.agent_initialized = True
except Exception as e:
    st.error(f"Agent 초기화 실패: {e}")
    st.stop()

# 헤더
st.title("🏛️ 통계청 인구 데이터 조회")
st.caption("자연어로 질문하면 SQL 쿼리를 자동 생성하여 답변합니다")

# 사이드바
with st.sidebar:
    st.header("📊 데이터 정보")
    st.info("""
    **데이터 기간**  
    2016년 1월 ~ 2025년 10월
    
    **포함 데이터**
    - 행정구역별 인구수
    - 성별/연령대별 통계
    - 세대수(가구수)
    """)
    
    st.header("💡 질문 예시")
    example_questions = [
        "서울특별시의 최신 총인구수는?",
        "경기도 세대수는 얼마야?",
        "부산에는 30대가 몇명이나 살아?",
        "2025년 10월 인구 150만명 미만 광역시는?"
    ]
    
    for q in example_questions:
        if st.button(q, key=q, use_container_width=True):
            st.session_state.current_question = q
    
    st.divider()
    
    if st.button("🗑️ 대화 기록 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 메인 영역
col1, col2 = st.columns([3, 1])

with col2:
    st.metric("대화 수", len(st.session_state.messages) // 2)

# 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # 모두 plain text로 표시
        st.write(message["content"])
        
        if "sql_queries" in message and message["sql_queries"]:
            with st.expander("📝 실행된 SQL 쿼리"):
                for i, sql in enumerate(message["sql_queries"], 1):
                    if len(message["sql_queries"]) > 1:
                        st.caption(f"쿼리 {i}")
                    st.code(sql, language="sql")
        
        if "steps" in message and message["steps"]:
            with st.expander("🔧 처리 과정"):
                for i, step in enumerate(message["steps"], 1):
                    st.markdown(f"**{i}. {step['tool']}**")
                    if step['input']:
                        st.json(step['input'])

# 질문 입력
question = st.chat_input("질문을 입력하세요")

# 사이드바 버튼으로 질문 설정
if "current_question" in st.session_state:
    question = st.session_state.current_question
    del st.session_state.current_question

if question:
    # 사용자 메시지 추가
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })
    
    with st.chat_message("user"):
        # plain text로 표시
        st.write(question)
    
    # Agent 응답
    with st.chat_message("assistant"):
        with st.spinner("답변 생성 중..."):
            result = agent_manager.query(question)
            
            if result["success"]:
                answer = result["answer"]
                sql_queries = result.get("sql_queries", [])
                steps = result.get("steps", [])
                
                # 답변 표시 (plain text)
                st.success(answer)
                
                # SQL 쿼리 표시
                if sql_queries:
                    with st.expander("📝 실행된 SQL 쿼리", expanded=True):
                        for i, sql in enumerate(sql_queries, 1):
                            if len(sql_queries) > 1:
                                st.caption(f"쿼리 {i}")
                            st.code(sql, language="sql")
                
                # 처리 과정 표시
                if steps:
                    with st.expander("🔧 처리 과정"):
                        for i, step in enumerate(steps, 1):
                            st.markdown(f"**{i}. {step['tool']}**")
                            if step['input']:
                                st.json(step['input'])
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sql_queries": sql_queries,
                    "steps": steps
                })
            else:
                error_msg = f"❌ 오류가 발생했습니다: {result['error']}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sql_queries": [],
                    "steps": []
                })

# 푸터
st.divider()
st.caption("💡 팁: 질문은 구체적으로 작성할수록 정확한 답변을 받을 수 있습니다")