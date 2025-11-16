"""
LangGraph 기반 SQL Agent
"""

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from config import settings
from database import db_manager
from utils import search_table_metadata
import operator


# State 정의
class AgentState(TypedDict):
    """Agent의 상태를 저장하는 구조"""
    question: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    table_info: str
    sql_query: str
    sql_result: str
    answer: str
    error: str


class LangGraphSQLAgent:
    """LangGraph 기반 SQL Agent"""
    
    def __init__(self):
        self.llm = None
        self.db = None
        self.graph = None
        
    def initialize(self):
        """Agent 초기화"""
        # LLM 초기화 (Gemini)
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            convert_system_message_to_human=True
        )
        print(f"LLM 초기화 완료: gemini-2.5-flash")
        
        # DB 연결
        self.db = db_manager.get_db()
        
        # Graph 구성
        self.graph = self._create_graph()
        print("LangGraph SQL Agent 생성 완료")
        
        return self.graph
    
    def visualize_graph(self, output_path="graph_visualization.png"):
        """그래프 시각화 (PNG 파일로 저장)"""
        try:
            from langgraph.graph import StateGraph
            
            if self.graph is None:
                self.initialize()
            
            # Mermaid PNG로 저장
            png_data = self.graph.get_graph().draw_mermaid_png()
            
            with open(output_path, "wb") as f:
                f.write(png_data)
            
            print(f"✅ 그래프 시각화 저장: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 시각화 실패: {e}")
            print("💡 필요한 패키지 설치: pip install pygraphviz")
            return None
    
    def _create_graph(self):
        """LangGraph 생성"""
        workflow = StateGraph(AgentState)
        
        # Node 추가
        workflow.add_node("search_metadata", self._search_metadata_node)
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("execute_sql", self._execute_sql_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        
        # Edge 설정
        workflow.set_entry_point("search_metadata")
        workflow.add_edge("search_metadata", "generate_sql")
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "generate_answer")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()
    
    def _search_metadata_node(self, state: AgentState) -> AgentState:
        """메타데이터 검색 노드"""
        question = state["question"]
        
        # 키워드 추출
        prompt = f"""
        질문: {question}
        
        이 질문에서 테이블을 찾기 위한 핵심 키워드 1개만 추출하세요.
        (인구, 세대, 연령 중 하나)
        
        키워드만 답변하세요:
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        keyword = response.content.strip()
        
        # 메타데이터 검색
        table_info = search_table_metadata.invoke({"keywords": keyword})
        
        print(f"[메타데이터 검색] 키워드: {keyword}")
        print(f"[메타데이터 검색] 결과: {table_info[:100]}...")
        
        return {
            **state,
            "table_info": table_info,
            "messages": [AIMessage(content=f"테이블 검색 완료: {keyword}")]
        }
    
    def _generate_sql_node(self, state: AgentState) -> AgentState:
        """SQL 생성 노드"""
        question = state["question"]
        table_info = state["table_info"]
        
        # 테이블 스키마 가져오기
        schema_info = self.db.get_table_info()
        
        prompt = f"""
        당신은 SQLite 전문가입니다.
        
        **질문**: {question}
        
        **사용 가능한 테이블 정보**:
        {table_info}
        
        **테이블 스키마**:
        {schema_info}
        
        **CRITICAL SQL 작성 규칙**:
        1. SQLite 문법만 사용 (MySQL, PostgreSQL 문법 금지)
        2. SELECT 쿼리 1개만 작성
        3. 집계 함수 중첩 금지 (예: AVG(SUM(...)) 절대 금지)
        4. 평균 계산: 서브쿼리 사용 (예: SELECT AVG(월별합계) FROM (SELECT 년월, SUM(값) as 월별합계 ... GROUP BY 년월))
        5. 비율 계산: CAST(값 AS FLOAT) / 값2
        6. 모든 계산은 SQL 안에서 완료
        7. 세미콜론(;) 1개로만 끝내기
        8. 설명, 주석(--), 태그 절대 포함 금지
        9. 서브쿼리에는 별칭(alias) 필수 (예: ) AS subquery)
        10. 여러 월 필터링: IN 절 사용 (예: 년월 IN ('2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06'))
        11. LIKE 패턴에서 정규표현식([]) 사용 금지
        12. CTE 사용 시: WITH 절로 시작해야 함 (예: WITH T1 AS (...), T2 AS (...) SELECT ...)
        13. 중앙값(median) 같은 복잡한 계산은 가능한 피하고, 평균이나 합계로 대체
        
        **날짜 필터링 예시**:
        잘못된 예: 년월 LIKE '2023-0[1-6]%' (SQLite에서 작동 안함!)
        올바른 예: 년월 IN ('2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06')
        올바른 예: 년월 BETWEEN '2023-01' AND '2023-06'
        
        **CTE 사용 예시**:
        올바른 예: WITH T1 AS (SELECT ...), T2 AS (SELECT ...) SELECT * FROM T1 JOIN T2 ...
        잘못된 예: SELECT ... ), T2 AS (SELECT ...) (WITH 없이 시작)
        
        **SQLite에서 사용 불가능한 함수 (절대 사용 금지)**:
        - STDEV(), STDDEV() → 대신 SQRT(AVG(값*값) - AVG(값)*AVG(값)) 사용
        - VARIANCE() → 대신 (AVG(값*값) - AVG(값)*AVG(값)) 사용
        - MEDIAN() → 대신 다른 방법 사용 또는 계산 생략
        
        **SQLite에서 사용 가능한 집계 함수**:
        - COUNT(), SUM(), AVG(), MIN(), MAX(), GROUP_CONCAT()
        - 기본 산술: +, -, *, /, SQRT(), ABS(), ROUND()
        
        **집계 함수 중첩 예시**:
        잘못된 예: SELECT AVG(SUM(값)) ... (오류!)
        올바른 예: SELECT AVG(합계) FROM (SELECT SUM(값) as 합계 ... GROUP BY 년월) AS sub
        
        CRITICAL: 실행 가능한 SQLite 쿼리 1개만 작성하세요.
        
        SQL:
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        sql_query = response.content.strip()
        
        # SQL 정리 및 검증
        # 1. 코드 블록 제거
        if "```" in sql_query:
            parts = sql_query.split("```")
            for part in parts:
                if part.strip().upper().startswith(('SELECT', 'WITH')):
                    sql_query = part
                    break
            if sql_query.startswith("sql"):
                sql_query = sql_query[3:]
            sql_query = sql_query.strip()
        
        # 2. 태그 제거
        import re
        sql_query = re.sub(r'<[^>]+>', '', sql_query)
        
        # 3. 주석 제거 (-- 이후 내용)
        lines = sql_query.split('\n')
        cleaned_lines = []
        for line in lines:
            if '--' in line:
                line = line.split('--')[0]
            if line.strip():
                cleaned_lines.append(line.strip())
        sql_query = ' '.join(cleaned_lines)
        
        # 4. 첫 번째 세미콜론까지만 추출
        if ';' in sql_query:
            sql_query = sql_query.split(';')[0] + ';'
        
        # 5. WITH 또는 SELECT로 시작하는지 확인
        sql_query = sql_query.strip()
        if not (sql_query.upper().startswith('SELECT') or sql_query.upper().startswith('WITH')):
            # SELECT 또는 WITH 찾기
            select_idx = sql_query.upper().find('SELECT')
            with_idx = sql_query.upper().find('WITH')
            
            # 둘 다 있으면 더 앞에 있는 것 사용
            if select_idx != -1 and with_idx != -1:
                start_idx = min(select_idx, with_idx)
            elif with_idx != -1:
                start_idx = with_idx
            elif select_idx != -1:
                start_idx = select_idx
            else:
                start_idx = 0
                
            if start_idx > 0:
                sql_query = sql_query[start_idx:]
        
        # 6. 연속 공백을 하나로
        sql_query = ' '.join(sql_query.split())
        
        print(f"[SQL 생성] {sql_query}")
        
        return {
            **state,
            "sql_query": sql_query,
            "messages": state["messages"] + [AIMessage(content=f"SQL 생성 완료")]
        }
    
    def _execute_sql_node(self, state: AgentState) -> AgentState:
        """SQL 실행 노드"""
        sql_query = state["sql_query"]
        
        try:
            result = self.db.run(sql_query)
            print(f"[SQL 실행] 성공: {result[:100]}...")
            
            return {
                **state,
                "sql_result": str(result),
                "messages": state["messages"] + [AIMessage(content=f"SQL 실행 완료")]
            }
        except Exception as e:
            error_msg = f"SQL 실행 오류: {str(e)}"
            print(f"[SQL 실행] 실패: {error_msg}")
            
            return {
                **state,
                "sql_result": "",
                "error": error_msg,
                "messages": state["messages"] + [AIMessage(content=error_msg)]
            }
    
    def _generate_answer_node(self, state: AgentState) -> AgentState:
        """답변 생성 노드"""
        question = state["question"]
        sql_query = state["sql_query"]
        sql_result = state["sql_result"]
        error = state.get("error", "")
        
        if error:
            return {
                **state,
                "answer": f"죄송합니다. 오류가 발생했습니다: {error}"
            }
        
        # SQL에서 테이블명 추출
        import re
        tables = re.findall(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
        table_info = f"(출처 테이블: {', '.join(set(tables))})" if tables else ""
        
        prompt = f"""
        질문: {question}
        SQL 실행 결과: {sql_result}
        
        **답변 작성 규칙**:
        1. 한국어로 답변
        2. 수치는 쉼표로 구분
        3. 2-3문장으로 간결하게
        4. SQL 결과를 그대로 사용 (직접 계산 금지)
        5. 조회 기준 시점 명시
        6. 답변 끝에 반드시 데이터 출처 테이블 명시: {table_info}
        
        답변을 작성하세요:
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        answer = response.content.strip()
        
        # 테이블 정보가 답변에 없으면 추가
        if table_info and table_info not in answer:
            answer = f"{answer} {table_info}"
        
        print(f"[답변 생성] {answer[:100]}...")
        
        return {
            **state,
            "answer": answer,
            "messages": state["messages"] + [AIMessage(content=answer)]
        }
    
    def query(self, question: str) -> dict:
        """질문 처리"""
        if self.graph is None:
            self.initialize()
        
        try:
            print(f"\n{'='*60}")
            print(f"질문: {question}")
            print(f"{'='*60}")
            
            # 초기 상태
            initial_state = {
                "question": question,
                "messages": [],
                "table_info": "",
                "sql_query": "",
                "sql_result": "",
                "answer": "",
                "error": ""
            }
            
            # Graph 실행
            result = self.graph.invoke(initial_state)
            
            return {
                "question": question,
                "answer": result["answer"],
                "sql_queries": [result["sql_query"]],
                "success": True,
                "error": None
            }
            
        except Exception as e:
            print(f"에러 발생: {e}")
            return {
                "question": question,
                "answer": None,
                "sql_queries": [],
                "success": False,
                "error": str(e)
            }


# 전역 인스턴스
langgraph_agent_manager = LangGraphSQLAgent()