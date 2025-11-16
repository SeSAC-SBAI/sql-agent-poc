"""
임베딩 데이터베이스 설정 및 검색
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_upstage import UpstageEmbeddings
from langchain_chroma import Chroma
from config.settings import settings


def setup_embedding_db(db_path: str = None):
    """
    DB에서 메타데이터 읽어서 벡터 DB 생성

    Args:
        db_path: DB 파일 경로

    Returns:
        Chroma vectorstore
    """
    from database.metadata_manager import get_metadata_manager

    # 메타데이터 매니저
    manager = get_metadata_manager(db_path)

    # 짧은 문서 생성
    documents = []
    metadatas = []

    for table_name in manager.get_table_names():
        # 짧은 문서 (임베딩용)
        short_doc = manager.get_short_doc(table_name)
        documents.append(short_doc)

        # 메타데이터 (필터링용)
        meta = manager._cache[table_name]
        metadatas.append(
            {
                "table_name": table_name,
                "topic_main": meta["topic_main"],
                "topic_sub": meta["topic_sub"],
                "keywords": meta["keywords_ko"],
                "period_start": meta["period_start"],
                "period_end": meta["period_end"],
                "geo_level": meta["geo_level"],
            }
        )

    # Upstage 임베딩
    embeddings = UpstageEmbeddings(
        api_key=settings.UPSTAGE_API_KEY, model="solar-embedding-1-large"
    )

    # Chroma 벡터스토어 생성
    vectorstore = Chroma.from_texts(
        texts=documents,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory="./embedding_db",
    )

    print(f"✅ 벡터 DB 생성: {len(documents)}개 테이블")
    return vectorstore


def get_required_tables_by_rule(query: str) -> List[str]:
    """
    Rule 기반 필수 테이블 판단

    Args:
        query: 사용자 질문

    Returns:
        list: 필수 테이블명 리스트
    """
    required = []

    # Rule 1: "비중", "비율" → 분자 + 분모 필요
    if any(keyword in query for keyword in ["비중", "비율", "%", "퍼센트", "점유율"]):
        if any(
            age_word in query
            for age_word in ["연령", "나이", "세", "고령", "청년", "노인"]
        ):
            required.extend(
                [
                    "population_age_stats",  # 분자
                    "population_gender_stats",  # 분모 (총인구)
                ]
            )

    # Rule 2: "세대" 명시
    if "세대" in query or "가구" in query:
        required.append("population_stats")

    # Rule 3: "주택" 명시
    if "주택" in query or "아파트" in query or "주거" in query:
        required.append("housing_type_sido_stats")

    return list(set(required))  # 중복 제거


def detect_category(query: str) -> Optional[str]:
    """
    질문에서 카테고리 감지

    Args:
        query: 사용자 질문

    Returns:
        str: 카테고리명 ('인구', '주거' 등) 또는 None
    """
    if any(
        keyword in query
        for keyword in ["인구", "주민", "남자", "여자", "연령", "세대", "나이"]
    ):
        return "인구"

    if any(
        keyword in query for keyword in ["주택", "아파트", "주거", "연립", "다세대"]
    ):
        return "주거"

    return None


def merge_unique_tables(
    vector_results: List[Dict], required_table_names: List[str]
) -> List[Dict]:
    """
    벡터 검색 결과 + 필수 테이블 병합

    Args:
        vector_results: 벡터 검색으로 찾은 테이블 정보 리스트
        required_table_names: Rule로 추출한 필수 테이블명 리스트

    Returns:
        병합된 테이블 정보 리스트
    """
    from database.metadata_manager import get_metadata_manager

    manager = get_metadata_manager()

    # 벡터 검색 테이블명 추출
    vector_table_names = [t["table_name"] for t in vector_results]

    # 최종 결과 (벡터 검색 결과부터)
    final_tables = vector_results.copy()

    # 필수 테이블 중 누락된 것 추가
    for table_name in required_table_names:
        if table_name not in vector_table_names:
            # 상세 정보 로드
            detailed = manager.get_detailed_info(table_name)
            if detailed:
                final_tables.append(detailed)
                print(f"  ✓ Rule 추가: {table_name}")

    return final_tables


def search_tables_hierarchical(
    query: str, n_results: int = 5, category_filter: Optional[str] = None
) -> List[Dict]:
    """
    계층적 검색: 짧은 문서 검색 → 상세 정보 로드

    Args:
        query: 사용자 질문
        n_results: 반환할 테이블 수
        category_filter: 카테고리 필터 (예: "인구")

    Returns:
        상세 정보가 포함된 테이블 리스트
    """
    from database.metadata_manager import get_metadata_manager

    manager = get_metadata_manager()

    # 임베딩 & 벡터스토어 로드
    embeddings = UpstageEmbeddings(
        api_key=settings.UPSTAGE_API_KEY, model="solar-embedding-1-large"
    )

    vectorstore = Chroma(
        persist_directory="./embedding_db", embedding_function=embeddings
    )

    # 벡터 검색
    search_kwargs = {"k": n_results * 2}  # 여유있게

    # 카테고리 필터 적용
    if category_filter:
        search_kwargs["filter"] = {"topic_main": category_filter}

    results = vectorstore.similarity_search_with_score(query, **search_kwargs)

    # 임계값 필터링 (거리 2.0 이하만)
    filtered_tables = []
    for doc, distance in results:
        if distance <= 2.0:
            table_name = doc.metadata.get("table_name")
            if table_name:
                filtered_tables.append(table_name)

    # 상위 n개만
    top_tables = filtered_tables[:n_results]

    # 상세 정보 로드
    detailed_tables = []
    for table_name in top_tables:
        detailed = manager.get_detailed_info(table_name)
        if detailed:
            detailed_tables.append(detailed)

    return detailed_tables


def smart_search_tables(query: str, n_results: int = 5) -> List[Dict]:
    """
    스마트 검색: 벡터 + Rule 조합

    Args:
        query: 사용자 질문
        n_results: 반환할 테이블 수

    Returns:
        프롬프트에 넣을 상세 테이블 정보 리스트
    """
    print(f"\n{'='*60}")
    print(f"테이블 검색: {query}")
    print(f"{'='*60}")

    # 1. 카테고리 감지
    category = detect_category(query)
    if category:
        print(f"카테고리: {category}")

    # 2. 벡터 검색
    vector_results = search_tables_hierarchical(
        query, n_results=n_results, category_filter=category
    )

    print(f"벡터 검색: {len(vector_results)}개")
    for table in vector_results:
        print(f"  - {table['table_name']}")

    # 3. Rule 기반 필수 테이블
    required_tables = get_required_tables_by_rule(query)

    if required_tables:
        print(f"Rule 감지: {required_tables}")

    # 4. 병합
    final_results = merge_unique_tables(vector_results, required_tables)

    # 5. 최대 개수 제한
    final_results = final_results[:n_results]

    print(f"최종: {len(final_results)}개 테이블")
    print(f"{'='*60}\n")

    return final_results


# 기존 함수 (하위 호환성 유지)
def search_tables_from_db(
    query: str, n_results: int = 1, threshold: float = 1.5
) -> list:
    """
    질문으로 관련 테이블 검색 (기존 함수, 하위 호환용)

    Args:
        query: 사용자 질문
        n_results: 반환할 테이블 수
        threshold: 거리 임계값

    Returns:
        list: 관련 테이블 정보 리스트
    """
    embeddings = UpstageEmbeddings(
        api_key=settings.UPSTAGE_API_KEY, model="solar-embedding-1-large"
    )

    vectorstore = Chroma(
        persist_directory="./embedding_db", embedding_function=embeddings
    )

    results = vectorstore.similarity_search_with_score(query, k=n_results)

    tables = []
    for doc, distance in results:
        if distance <= threshold:
            tables.append(
                {
                    "table_name": doc.metadata.get("table_name"),
                    "keywords": doc.metadata.get("keywords"),
                    "columns": doc.metadata.get("columns"),
                    "description": doc.page_content,
                    "distance": round(distance, 3),
                }
            )

    return tables


if __name__ == "__main__":
    # 초기 설정
    print("벡터 DB 초기화는 scripts/setup_vector_db.py를 사용하세요")

    # 테스트 검색
    print("\n" + "=" * 60)
    print("테스트 검색")
    print("=" * 60)

    test_queries = [
        "경기도 0~14세 비중은?",
        "서울에 60대 노인은 몇 명이야?",
        "수원시의 세대수는?",
    ]

    for query in test_queries:
        results = smart_search_tables(query, n_results=3)
        print(f"\n질문: {query}")
        print(f"결과: {[r['table_name'] for r in results]}")
