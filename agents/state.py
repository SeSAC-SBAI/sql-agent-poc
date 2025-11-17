from typing import TypedDict, List, Optional, Dict, Any


class StatsChatbotState(TypedDict):
    """통계 챗봇의 전체 상태를 관리하는 State 클래스"""

    # 기본 정보
    user_query: str  # 사용자의 원본 질문
    original_query: Optional[
        str
    ]  # 원래 질문 저장용 (추가 질문 받았을 때 원본이 이곳에 저장)
    scenario_type: str  # 시나리오 타입: "single_value", "table_view", "simple_aggregation", "derived_calculation", "multi_step_analysis", "out_of_scope"
    reasoning: Optional[str]

    # 테이블 검색
    tables_info: List[
        Dict[str, Any]
    ]  # 벡터DB에서 검색된 테이블 정보 (테이블명, 스키마, 컬럼 정보)

    # SQL 관련
    sql_query: str  # 생성된 SQL 쿼리
    sql_retry_count: int  # SQL 생성 재시도 횟수
    sql_error: Optional[str]  # SQL 실행 에러 메시지

    # 데이터
    query_result: List[Dict[str, Any]]  # SQL 실행 결과 데이터
    processed_data: Optional[Dict[str, Any]]  # 후처리된 데이터 (계산 결과 등)

    # 분석 및 시각화
    insight: str  # 데이터 분석 인사이트 (경향, 패턴)
    chart_spec: Optional[Dict[str, Any]]  # 시각화 차트 스펙 (차트 타입, 데이터 등)

    # 응답
    final_response: str  # 최종 응답 메시지

    # 재시도 및 에러
    clarification_count: int  # 추가 정보 요청 재시도 횟수
    error: Optional[str]  # 일반 에러 메시지
