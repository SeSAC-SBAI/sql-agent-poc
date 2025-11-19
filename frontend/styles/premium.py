import streamlit as st

PREMIUM_COLORS = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe',
    '#43e97b', '#fa709a', '#fee140', '#30cfd0'
]

def apply_premium_style():
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
        
        /* 메인 컨테이너 가로 길이 확장 */
        .main .block-container {
            max-width: 95% !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
        }
        
        @media (min-width: 1200px) {
            .main .block-container {
                max-width: 1400px !important;
            }
        }
        
        /* 채팅 컨테이너 가로 길이 확장 */
        [data-testid="stChatInputContainer"] {
            max-width: 100% !important;
        }
        
        [data-testid="stChatMessage"] {
            max-width: 100% !important;
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
            height: 80px !important;
            min-height: 80px !important;
            display: flex !important;
            align-items: center !important;
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
        
        /* 추가 세련된 스타일 */
        .stMarkdown {
            max-width: 100% !important;
        }
        
        /* 스피너 스타일 개선 */
        .stSpinner > div {
            border-color: #667eea !important;
        }
        
        /* 에러 메시지 스타일 */
        .stAlert {
            border-radius: 12px;
            border: 1px solid #e1e4e8;
        }
        
        /* 성공 메시지 스타일 */
        [data-baseweb="notification"] {
            border-radius: 12px;
        }
        
        /* 메인 영역 패딩 조정 */
        section[data-testid="stMain"] {
            padding-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

