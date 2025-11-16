"""
통계 데이터 챗봇 Streamlit UI (세련된 디자인 + 예시 질문)
"""

import streamlit as st
import uuid
from agents.langgraph_agent import langgraph_agent_manager

# 페이지 설정
st.set_page_config(
    page_title="easystat Q",
    page_icon="🤖",
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
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
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
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(10px);
    }
    
    /* 입력창 스타일 */
    .stChatInputContainer {
        background-color: white;
        border-radius: 30px;
        padding: 5px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* 버튼 스타일 */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 28px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* 제목 스타일 */
    h1 {
        color: white;
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
        font-weight: 900;
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem;
    }
    
    h3 {
        color: rgba(255, 255, 255, 0.9);
        font-weight: 400;
        font-size: 1.3rem;
    }
    
    /* SQL 코드 블록 */
    .stCodeBlock {
        background-color: #1e293b;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Expander 스타일 */
    .streamlit-expanderHeader {
        background-color: rgba(102, 126, 234, 0.15);
        border-radius: 10px;
        font-weight: 600;
        padding: 12px;
    }
    
    /* 마크다운 스타일 */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* 사이드바 제목 */
    [data-testid="stSidebar"] h1 {
        color: white;
        text-align: center;
        font-size: 2rem;
        margin-bottom: 30px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* 사이드바 마크다운 */
    [data-testid="stSidebar"] .element-container p,
    [data-testid="stSidebar"] .element-container li {
        color: #E8EAF6;
        font-size: 0.95rem;
    }
    
    /* 사이드바 구분선 */
    [data-testid="stSidebar"] hr {
        border-color: rgba(232, 234, 246, 0.3);
        margin: 25px 0;
    }
    
    /* 웰컴 카드 */
    .welcome-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
        padding: 35px;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
        margin: 20px 0;
        backdrop-filter: blur(10px);
    }
    
    /* 예시 질문 버튼 그룹 */
    .example-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 20px;
    }
    
    /* 예시 질문 개별 버튼 */
    .example-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        border: none;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
    }
    
    .example-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.5);
    }
    
    /* 로딩 스피너 */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* 카테고리 칩 */
    .category-chip {
        display: inline-block;
        background: rgba(102, 126, 234, 0.2);
        color: #667eea;
        padding: 6px 15px;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 예시 질문 데이터
EXAMPLE_QUESTIONS = {
    "인구": [
        "2023년 서울시 총 인구는?",
        "최근 5년간 전국 인구 추이는?",
        "경기도에서 인구가 가장 많은 지역은?",
    ],
    "세대": [
        "2023년 1인 가구 수는?",
        "서울시 평균 가구원 수는?",
        "최근 3년간 세대수 변화는?",
    ],
    "연령": [
        "2023년 65세 이상 인구 비율은?",
        "20대 인구가 가장 많은 지역은?",
        "전국 평균 연령은?",
    ],
    "비교": [
        "강남구와 강북구의 인구 비교",
        "서울과 부산의 고령화율 비교",
        "수도권과 비수도권 인구 차이는?",
    ]
}

# 유틸리티 함수
def generate_thread_id():
    """새 thread ID 생성"""
    return str(uuid.uuid4())

def reset_chat():
    """채팅 초기화"""
    st.session_state['thread_id'] = generate_thread_id()
    st.session_state['messages'] = []
    st.session_state['selected_question'] = None

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

if 'selected_question' not in st.session_state:
    st.session_state['selected_question'] = None

# 사이드바
with st.sidebar:
    st.title("easystat Q")
    st.markdown("---")
    
    if st.button("🔄 새로운 대화", use_container_width=True):
        reset_chat()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💡 사용 방법")
    st.markdown("""
    - 통계 데이터에 대해 질문하세요
    - 예시 질문을 클릭해보세요
    - SQL 쿼리가 자동 생성됩니다
    """)
    
    st.markdown("---")
    st.markdown("### 📌 주요 기능")
    st.markdown("""
    - 🤖 AI 기반 자연어 처리
    - 📊 실시간 데이터 조회
    - 💾 대화 히스토리 저장
    - 🔍 SQL 쿼리 확인 가능
    """)
    
    st.markdown("---")
    st.markdown("**🔑 세션 ID**")
    st.code(st.session_state['thread_id'][:8] + "...", language="text")

# 메인 화면
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.title("📊 easystat Q")
    st.markdown("### 통계 데이터에 대해 무엇이든 물어보세요")
    st.markdown("")

# 시작 안내 & 예시 질문 (대화가 없을 때)
if len(st.session_state['messages']) == 0:
    st.markdown("""
    <div class="welcome-card">
        <h2 style="color: #667eea; margin-top: 0;">👋 환영합니다!</h2>
        <p style="color: #555; font-size: 1.1rem; margin-bottom: 15px;">
            easystat Q는 AI 기반 통계 데이터 조회 챗봇입니다. 
            아래 예시 질문을 클릭하거나 직접 질문을 입력하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 카테고리별 예시 질문
    st.markdown("### 📝 예시 질문")
    
    tabs = st.tabs(list(EXAMPLE_QUESTIONS.keys()))
    
    for i, (category, questions) in enumerate(EXAMPLE_QUESTIONS.items()):
        with tabs[i]:
            cols = st.columns(1)
            for question in questions:
                if st.button(question, key=f"example_{category}_{question}", use_container_width=True):
                    st.session_state['selected_question'] = question
                    st.rerun()

# 대화 히스토리 표시
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        
        # SQL 쿼리 표시 (있는 경우)
        if 'sql' in message and message['sql']:
            with st.expander("🔍 실행된 SQL 쿼리 보기"):
                st.code(message['sql'], language='sql')

# 선택된 예시 질문 처리
if st.session_state.get('selected_question'):
    prompt = st.session_state['selected_question']
    st.session_state['selected_question'] = None
else:
    prompt = st.chat_input("💬 질문을 입력하세요...")

# 질문 처리
if prompt:
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
    
    st.rerun()