"""
easystat Q - 미니멀 화이트 기업용 디자인
"""

import streamlit as st
import uuid
from agents.langgraph_agent import langgraph_agent_manager

# 페이지 설정
st.set_page_config(
    page_title="easystat Q",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 미니멀 화이트 CSS
st.markdown("""
<style>
    /* 전체 배경 - 깔끔한 화이트 */
    .main {
        background: #ffffff;
        color: #1a1a1a;
    }
    
    /* 사이드바 - 라이트 그레이 */
    [data-testid="stSidebar"] {
        background: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    [data-testid="stSidebar"] * {
        color: #1a1a1a !important;
    }
    
    /* 채팅 메시지 - 심플 카드 */
    .stChatMessage {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease;
    }
    
    .stChatMessage:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* 사용자 메시지 */
    [data-testid="stChatMessageContent"] {
        color: #1a1a1a;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* 입력창 - 심플 보더 */
    .stChatInputContainer {
        background: #ffffff;
        border: 2px solid #e9ecef;
        border-radius: 24px;
        padding: 8px;
        transition: all 0.2s ease;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #4263eb;
        box-shadow: 0 0 0 3px rgba(66, 99, 235, 0.1);
    }
    
    /* 버튼 - 프로페셔널 스타일 */
    .stButton button {
        background: #4263eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(66, 99, 235, 0.2);
    }
    
    .stButton button:hover {
        background: #3451d1;
        box-shadow: 0 4px 8px rgba(66, 99, 235, 0.3);
        transform: translateY(-1px);
    }
    
    /* 제목 - 깔끔한 타이포 */
    h1 {
        color: #1a1a1a;
        font-weight: 700;
        font-size: 2.8rem !important;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    h2 {
        color: #1a1a1a;
        font-weight: 600;
        font-size: 1.8rem;
    }
    
    h3 {
        color: #495057;
        font-weight: 600;
        font-size: 1.2rem;
    }
    
    /* SQL 코드 블록 */
    .stCodeBlock {
        background: #f8f9fa !important;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Expander - 미니멀 스타일 */
    .streamlit-expanderHeader {
        background: #f8f9fa !important;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        font-weight: 600;
        padding: 12px 16px;
        color: #495057 !important;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: #e9ecef !important;
        border-color: #dee2e6;
    }
    
    /* 웰컴 카드 */
    .welcome-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        padding: 32px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin: 20px 0;
    }
    
    .welcome-card h2 {
        color: #4263eb;
        margin-top: 0;
        font-size: 1.8rem;
    }
    
    .welcome-card p {
        color: #495057;
        line-height: 1.7;
        font-size: 1rem;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        padding: 0;
        border-bottom: 2px solid #e9ecef;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 12px 20px;
        color: #6c757d;
        font-weight: 600;
        transition: all 0.2s ease;
        border-bottom: 3px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #4263eb;
        border-bottom-color: #c5d0f5;
    }
    
    .stTabs [aria-selected="true"] {
        color: #4263eb;
        border-bottom-color: #4263eb;
    }
    
    /* 사이드바 제목 */
    [data-testid="stSidebar"] h1 {
        text-align: center;
        font-size: 1.8rem;
        margin-bottom: 24px;
        color: #1a1a1a;
        font-weight: 700;
    }
    
    /* 사이드바 구분선 */
    [data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: #dee2e6;
        margin: 20px 0;
    }
    
    /* 사이드바 텍스트 */
    [data-testid="stSidebar"] p {
        color: #495057 !important;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    /* 사이드바 리스트 */
    [data-testid="stSidebar"] li {
        color: #495057 !important;
        font-size: 0.9rem;
    }
    
    /* 로딩 스피너 */
    .stSpinner > div {
        border-top-color: #4263eb !important;
    }
    
    /* 스크롤바 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f8f9fa;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #ced4da;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #adb5bd;
    }
    
    /* 세션 ID 코드 */
    [data-testid="stSidebar"] code {
        background: #e9ecef !important;
        border: 1px solid #dee2e6;
        color: #495057 !important;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
    }
    
    /* 에러 메시지 */
    .stAlert {
        background: #fff5f5;
        border: 1px solid #feb2b2;
        border-radius: 8px;
        color: #c53030;
    }
    
    /* 컨테이너 패딩 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* 예시 질문 버튼 스타일 개선 */
    div[data-testid="column"] .stButton button {
        background: #f8f9fa;
        color: #1a1a1a;
        border: 1px solid #e9ecef;
        font-weight: 500;
        text-align: left;
        justify-content: flex-start;
        padding: 12px 20px;
    }
    
    div[data-testid="column"] .stButton button:hover {
        background: #4263eb;
        color: white;
        border-color: #4263eb;
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
    return str(uuid.uuid4())

def reset_chat():
    st.session_state['thread_id'] = generate_thread_id()
    st.session_state['messages'] = []
    st.session_state['selected_question'] = None

@st.cache_resource
def get_agent():
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
    
    if st.button("새로운 대화", use_container_width=True):
        reset_chat()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 사용 방법")
    st.markdown("""
    - 통계 데이터에 대해 질문하세요
    - 예시 질문을 클릭해보세요
    - SQL 쿼리가 자동 생성됩니다
    """)
    
    st.markdown("---")
    st.markdown("### 주요 기능")
    st.markdown("""
    - AI 기반 자연어 처리
    - 실시간 데이터 조회
    - 대화 히스토리 저장
    - SQL 쿼리 확인 가능
    """)
    
    st.markdown("---")
    st.markdown("**세션 ID**")
    st.code(st.session_state['thread_id'][:8] + "...")

# 메인 화면
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.title("easystat Q")
    st.markdown("### AI 기반 통계 데이터 조회 챗봇")
    st.markdown("")

# 시작 안내 & 예시 질문
if len(st.session_state['messages']) == 0:
    st.markdown("""
    <div class="welcome-card">
        <h2>환영합니다</h2>
        <p style="font-size: 1.05rem; margin-bottom: 15px;">
            easystat Q는 AI 기반 통계 데이터 조회 챗봇입니다. 
            아래 예시 질문을 클릭하거나 직접 질문을 입력하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 예시 질문")
    
    tabs = st.tabs(list(EXAMPLE_QUESTIONS.keys()))
    
    for i, (category, questions) in enumerate(EXAMPLE_QUESTIONS.items()):
        with tabs[i]:
            for question in questions:
                if st.button(question, key=f"example_{category}_{question}", use_container_width=True):
                    st.session_state['selected_question'] = question
                    st.rerun()

# 대화 히스토리 표시
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        
        if 'sql' in message and message['sql']:
            with st.expander("실행된 SQL 쿼리 보기"):
                st.code(message['sql'], language='sql')

# 선택된 예시 질문 처리
if st.session_state.get('selected_question'):
    prompt = st.session_state['selected_question']
    st.session_state['selected_question'] = None
else:
    prompt = st.chat_input("질문을 입력하세요...")

# 질문 처리
if prompt:
    st.session_state['messages'].append({
        'role': 'user',
        'content': prompt
    })
    
    with st.chat_message('user'):
        st.markdown(prompt)
    
    with st.chat_message('assistant'):
        with st.spinner('답변 생성 중...'):
            try:
                agent = get_agent()
                result = agent.query(prompt)
                
                if result['success']:
                    answer = result['answer']
                    sql_query = result['sql_queries'][0] if result['sql_queries'] else ""
                else:
                    answer = f"오류가 발생했습니다: {result['error']}"
                    sql_query = ""
                
                st.markdown(answer)
                
                if sql_query:
                    with st.expander("실행된 SQL 쿼리 보기"):
                        st.code(sql_query, language='sql')
                
                st.session_state['messages'].append({
                    'role': 'assistant',
                    'content': answer,
                    'sql': sql_query
                })
                
            except Exception as e:
                error_msg = f"오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                st.session_state['messages'].append({
                    'role': 'assistant',
                    'content': error_msg,
                    'sql': None
                })
    
    st.rerun()