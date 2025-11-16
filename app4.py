"""
easystat Q - 프리미엄 디자인 + 고급 시각화
"""

import streamlit as st
import uuid
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from agents.langgraph_agent import langgraph_agent_manager

# 페이지 설정
st.set_page_config(
    page_title="easystat Q",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 프리미엄 디자인 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* 전체 배경 - 고급 그라데이션 */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
        color: #1a1a1a;
    }
    
    /* 사이드바 - 프리미엄 스타일 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        border-right: 1px solid #e1e4e8;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.03);
    }
    
    [data-testid="stSidebar"] * {
        color: #1a1a1a !important;
    }
    
    /* 채팅 메시지 - 프리미엄 카드 */
    .stChatMessage {
        background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
        border: 1px solid #e1e4e8;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stChatMessage:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    [data-testid="stChatMessageContent"] {
        color: #1a1a1a;
        font-size: 1rem;
        line-height: 1.7;
        font-weight: 500;
    }
    
    /* 입력창 - 프리미엄 스타일 */
    .stChatInputContainer {
        background: #ffffff;
        border: 2px solid #e1e4e8;
        border-radius: 28px;
        padding: 8px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    .stChatInputContainer:focus-within {
        border-color: #5b7cff;
        box-shadow: 0 4px 16px rgba(91, 124, 255, 0.15);
        transform: translateY(-1px);
    }
    
    /* 버튼 - 프리미엄 그라데이션 */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 28px;
        font-weight: 700;
        font-size: 0.95rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
        letter-spacing: 0.3px;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.35);
        transform: translateY(-2px);
    }
    
    /* 제목 - 모던 타이포 */
    h1 {
        color: #1a1a1a;
        font-weight: 800;
        font-size: 3rem !important;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #1a1a1a;
        font-weight: 700;
        font-size: 1.8rem;
    }
    
    h3 {
        color: #495057;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: -0.3px;
    }
    
    /* SQL 코드 블록 - 프리미엄 */
    .stCodeBlock {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%) !important;
        border: 1px solid #4a5568;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Expander - 세련된 스타일 */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border: 1px solid #dee2e6;
        border-radius: 12px;
        font-weight: 700;
        padding: 14px 18px;
        color: #495057 !important;
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
        border-color: #ced4da;
        transform: translateY(-1px);
    }
    
    /* 웰컴 카드 - 프리미엄 */
    .welcome-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e1e4e8;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        margin: 24px 0;
    }
    
    .welcome-card h2 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 0;
        font-size: 2rem;
        font-weight: 800;
    }
    
    .welcome-card p {
        color: #495057;
        line-height: 1.8;
        font-size: 1.05rem;
        font-weight: 500;
    }
    
    /* 탭 - 모던 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: transparent;
        padding: 8px;
        border-bottom: none;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 12px 24px;
        color: #495057;
        font-weight: 700;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-color: transparent;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    /* 사이드바 */
    [data-testid="stSidebar"] h1 {
        text-align: center;
        font-size: 2rem;
        margin-bottom: 32px;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    [data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #dee2e6, transparent);
        margin: 24px 0;
    }
    
    [data-testid="stSidebar"] p {
        color: #495057 !important;
        font-size: 0.9rem;
        line-height: 1.7;
        font-weight: 500;
    }
    
    /* 스크롤바 */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f3f5;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }
    
    /* 세션 ID */
    [data-testid="stSidebar"] code {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border: 1px solid #dee2e6;
        color: #495057 !important;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    
    /* 예시 질문 버튼 */
    div[data-testid="column"] .stButton button {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        color: #1a1a1a;
        border: 1px solid #e1e4e8;
        font-weight: 600;
        text-align: left;
        padding: 14px 20px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    
    div[data-testid="column"] .stButton button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
    }
    
    /* 데이터프레임 */
    .stDataFrame {
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
</style>
""", unsafe_allow_html=True)

# 프리미엄 색상 팔레트
PREMIUM_COLORS = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe',
    '#43e97b', '#fa709a', '#fee140', '#30cfd0'
]

# 예시 질문
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

def parse_sql_result(sql_result_str):
    """SQL 결과 파싱"""
    try:
        result_str = str(sql_result_str).strip()
        
        if result_str.startswith('[') and result_str.endswith(']'):
            result_str = result_str[1:-1]
            
            rows = []
            if result_str.startswith('('):
                import re
                tuples = re.findall(r'\([^)]+\)', result_str)
                for t in tuples:
                    values = t.strip('()').split(',')
                    rows.append([v.strip().strip("'\"") for v in values])
            else:
                rows = [[result_str.strip("'\"")]]
            
            return pd.DataFrame(rows) if rows else None
        
        return None
    except:
        return None

def create_premium_chart(df, question):
    """프리미엄 스타일 차트 생성"""
    if df is None or df.empty:
        return None
    
    try:
        if len(df.columns) == 2:
            df.columns = ['항목', '값']
            
            try:
                df['값'] = pd.to_numeric(df['값'])
            except:
                return None
            
            # 차트 타입 결정
            if any(word in question for word in ['추이', '변화', '년도', '년간', '월별']):
                # 프리미엄 선 그래프
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['항목'], 
                    y=df['값'],
                    mode='lines+markers',
                    line=dict(color='#667eea', width=4, shape='spline'),
                    marker=dict(size=10, color='#764ba2', 
                               line=dict(color='white', width=2)),
                    fill='tonexty',
                    fillcolor='rgba(102, 126, 234, 0.1)',
                    hovertemplate='<b>%{x}</b><br>값: %{y:,.0f}<extra></extra>'
                ))
                
            elif any(word in question for word in ['비교', '대비', '차이']):
                # 프리미엄 막대 그래프 (그라데이션)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['항목'],
                    y=df['값'],
                    marker=dict(
                        color=df['값'],
                        colorscale=[[0, '#667eea'], [1, '#764ba2']],
                        line=dict(color='rgba(102, 126, 234, 0.3)', width=2)
                    ),
                    hovertemplate='<b>%{x}</b><br>값: %{y:,.0f}<extra></extra>'
                ))
                
            elif any(word in question for word in ['비율', '분포', '구성']):
                # 프리미엄 파이 차트
                fig = go.Figure()
                fig.add_trace(go.Pie(
                    labels=df['항목'],
                    values=df['값'],
                    marker=dict(colors=PREMIUM_COLORS,
                               line=dict(color='white', width=2)),
                    textfont=dict(size=14, color='white', family='Inter'),
                    hole=0.4,
                    hovertemplate='<b>%{label}</b><br>값: %{value:,.0f}<br>비율: %{percent}<extra></extra>'
                ))
                
            else:
                # 기본 막대 그래프
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['항목'],
                    y=df['값'],
                    marker=dict(
                        color=PREMIUM_COLORS[0],
                        line=dict(color='rgba(102, 126, 234, 0.3)', width=2)
                    ),
                    hovertemplate='<b>%{x}</b><br>값: %{y:,.0f}<extra></extra>'
                ))
            
            # 프리미엄 레이아웃
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=13, color='#495057', family='Inter'),
                height=450,
                margin=dict(l=40, r=40, t=40, b=40),
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor='white',
                    font_size=13,
                    font_family='Inter',
                    bordercolor='#e1e4e8'
                ),
                xaxis=dict(
                    showgrid=False,
                    showline=True,
                    linecolor='#e1e4e8',
                    tickfont=dict(size=12, color='#495057')
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.05)',
                    showline=False,
                    tickfont=dict(size=12, color='#495057')
                )
            )
            
            return fig
            
    except Exception as e:
        print(f"차트 생성 오류: {e}")
        return None

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

# 세션 상태
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
    - 통계 데이터 질문
    - 자동 차트 생성
    - SQL 쿼리 확인
    """)
    
    st.markdown("---")
    st.markdown("### 시각화")
    st.markdown("""
    - 추이 → 선 그래프
    - 비교 → 막대 그래프
    - 비율 → 파이 차트
    """)
    
    st.markdown("---")
    st.markdown("**세션 ID**")
    st.code(st.session_state['thread_id'][:8] + "...")

# 메인
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.title("easystat Q")
    st.markdown("### AI 기반 통계 데이터 조회 + 시각화")
    st.markdown("")

# 시작 화면
if len(st.session_state['messages']) == 0:
    st.markdown("""
    <div class="welcome-card">
        <h2>환영합니다</h2>
        <p>
            질문에 맞춰 자동으로 프리미엄 차트가 생성됩니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 예시 질문")
    
    tabs = st.tabs(list(EXAMPLE_QUESTIONS.keys()))
    
    for i, (category, questions) in enumerate(EXAMPLE_QUESTIONS.items()):
        with tabs[i]:
            for question in questions:
                if st.button(question, key=f"ex_{category}_{question}", use_container_width=True):
                    st.session_state['selected_question'] = question
                    st.rerun()

# 대화 히스토리
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        
        if 'chart' in message and message['chart'] is not None:
            st.plotly_chart(message['chart'], use_container_width=True)
        
        if 'dataframe' in message and message['dataframe'] is not None:
            with st.expander("데이터 테이블 보기"):
                st.dataframe(message['dataframe'], use_container_width=True)
        
        if 'sql' in message and message['sql']:
            with st.expander("SQL 쿼리 보기"):
                st.code(message['sql'], language='sql')

# 입력 처리
if st.session_state.get('selected_question'):
    prompt = st.session_state['selected_question']
    st.session_state['selected_question'] = None
else:
    prompt = st.chat_input("질문을 입력하세요...")

if prompt:
    st.session_state['messages'].append({'role': 'user', 'content': prompt})
    
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
                    
                    chart = None
                    dataframe = None
                    
                    if hasattr(agent, 'db') and sql_query:
                        try:
                            sql_result = agent.db.run(sql_query)
                            df = parse_sql_result(sql_result)
                            
                            if df is not None and not df.empty:
                                dataframe = df
                                chart = create_premium_chart(df, prompt)
                        except Exception as e:
                            print(f"시각화 오류: {e}")
                    
                    st.markdown(answer)
                    
                    if chart is not None:
                        st.plotly_chart(chart, use_container_width=True)
                    
                    if dataframe is not None:
                        with st.expander("데이터 테이블 보기"):
                            st.dataframe(dataframe, use_container_width=True)
                    
                    if sql_query:
                        with st.expander("SQL 쿼리 보기"):
                            st.code(sql_query, language='sql')
                    
                    st.session_state['messages'].append({
                        'role': 'assistant',
                        'content': answer,
                        'sql': sql_query,
                        'chart': chart,
                        'dataframe': dataframe
                    })
                else:
                    answer = f"오류: {result['error']}"
                    st.markdown(answer)
                    st.session_state['messages'].append({
                        'role': 'assistant',
                        'content': answer,
                        'sql': None,
                        'chart': None,
                        'dataframe': None
                    })
                
            except Exception as e:
                error_msg = f"오류: {str(e)}"
                st.error(error_msg)
                st.session_state['messages'].append({
                    'role': 'assistant',
                    'content': error_msg,
                    'sql': None,
                    'chart': None,
                    'dataframe': None
                })
    
    st.rerun()