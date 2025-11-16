"""
통계 데이터 챗봇 Streamlit UI (스타일 업그레이드)
"""

import streamlit as st
import uuid
from agents.langgraph_agent import langgraph_agent_manager

# 페이지 설정
st.set_page_config(
    page_title="📊 easystat Q",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    /* 메인 배경 */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2C3E50 0%, #34495E 100%);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    /* 채팅 메시지 스타일 */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* 사용자 메시지 */
    [data-testid="stChatMessageContent"] {
        background-color: transparent;
    }
    
    /* 입력창 스타일 */
    .stChatInputContainer {
        background-color: white;
        border-radius: 25px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* 버튼 스타일 */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* 제목 스타일 */
    h1 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        font-weight: 800;
    }
    
    /* SQL 코드 블록 */
    .stCodeBlock {
        background-color: #2C3E50;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    /* Expander 스타일 */
    .streamlit-expanderHeader {
        background-color: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* 마크다운 스타일 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 사이드바 제목 */
    [data-testid="stSidebar"] h1 {
        color: white;
        text-align: center;
        font-size: 28px;
        margin-bottom: 20px;
    }
    
    /* 사이드바 마크다운 */
    [data-testid="stSidebar"] .element-container p,
    [data-testid="stSidebar"] .element-container li {
        color: #ECF0F1;
    }
    
    /* 사이드바 구분선 */
    [data-testid="stSidebar"] hr {
        border-color: rgba(236, 240, 241, 0.3);
    }
    
    /* 로딩 스피너 */
    .stSpinner > div {
        border-top-color: #667eea;
    }
    
    /* 카드 스타일 메시지 */
    .info-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 유틸리티 함수
def generate_thread_id():
    """새 thread ID 생성"""
    return str(uuid.uuid4())

def reset_chat():
    """채팅 초기화"""
    st.session_state['thread_id'] = generate_thread_id()
    st.session_state['messages'] = []

# Agent 초기화 (캐싱)
@st.cache_resource
def get_agent():
    """LangGraph Agent 초기화"""
    agent = langgraph_agent_manager
    agent.initialize()
    return agent

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

# 사이드바
with st.sidebar:
    st.title("📊 easystat Q")
    st.markdown("---")
    
    if st.button("🔄 새로운 대화", use_container_width=True):
        reset_chat()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 사용 방법")
    st.markdown("""
    - 통계 데이터에 대해 질문하세요
    - 자연어로 편하게 물어보세요
    - SQL 쿼리가 자동 생성됩니다
    """)
    
    st.markdown("---")
    st.markdown("### 📌 기능")
    st.markdown("""
    - 🤖 AI 기반 자연어 처리
    - 📊 실시간 데이터 조회
    - 💾 대화 히스토리 저장
    - 🔍 SQL 쿼리 확인 가능
    """)
    
    st.markdown("---")
    st.markdown(f"**🔑 세션 ID**")
    st.code(st.session_state['thread_id'][:8] + "...", language="text")

# 메인 화면
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.title("📊 easystat Q")
    st.markdown("### 통계 데이터에 대해 무엇이든 물어보세요!")
    st.markdown("")

# 시작 안내 메시지 (대화가 없을 때)
if len(st.session_state['messages']) == 0:
    st.markdown("""
    <div class="info-card">
        <h3 style="color: #667eea; margin-top: 0;">👋 환영합니다!</h3>
        <p style="color: #555; margin-bottom: 10px;">easystat Q는 AI 기반 통계 데이터 조회 챗봇입니다.</p>
        <p style="color: #555; margin-bottom: 10px;"><strong>예시 질문:</strong></p>
        <ul style="color: #666;">
            <li>2023년 서울시 인구는?</li>
            <li>최근 5년간 출생률 추이는?</li>
            <li>강남구와 강북구의 세대수 비교</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 대화 히스토리 표시
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        
        # SQL 쿼리 표시 (있는 경우)
        if 'sql' in message and message['sql']:
            with st.expander("🔍 실행된 SQL 쿼리 보기"):
                st.code(message['sql'], language='sql')

# 사용자 입력
if prompt := st.chat_input("💬 질문을 입력하세요..."):
    
    # 사용자 메시지 추가
    st.session_state['messages'].append({
        'role': 'user',
        'content': prompt
    })
    
    # 사용자 메시지 표시
    with st.chat_message('user'):
        st.markdown(prompt)
    
    # 어시스턴트 응답
    with st.chat_message('assistant'):
        with st.spinner('🤔 답변을 생성하고 있습니다...'):
            try:
                # Agent 로드
                agent = get_agent()
                
                # Agent 실행
                result = agent.query(prompt)
                
                # 답변 가져오기
                if result['success']:
                    answer = result['answer']
                    sql_query = result['sql_queries'][0] if result['sql_queries'] else ""
                else:
                    answer = f"❌ 오류가 발생했습니다: {result['error']}"
                    sql_query = ""
                
                # 답변 표시
                st.markdown(answer)
                
                # SQL 쿼리 표시
                if sql_query:
                    with st.expander("🔍 실행된 SQL 쿼리 보기"):
                        st.code(sql_query, language='sql')
                
                # 세션에 저장
                st.session_state['messages'].append({
                    'role': 'assistant',
                    'content': answer,
                    'sql': sql_query
                })
                
            except Exception as e:
                error_msg = f"❌ 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                
                st.session_state['messages'].append({
                    'role': 'assistant',
                    'content': error_msg,
                    'sql': None
                })