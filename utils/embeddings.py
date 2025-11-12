"""
임베딩 데이터베이스 설정 및 검색
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_upstage import UpstageEmbeddings
from langchain_chroma import Chroma
from config import settings


def setup_embedding_db():
    """ChromaDB 임베딩 초기 설정"""

    # Upstage 임베딩 모델
    embeddings = UpstageEmbeddings(
        api_key=settings.UPSTAGE_API_KEY, model="solar-embedding-1-large"
    )

    # 임베딩할 문서들
    documents = [
        "population_age_stats 테이블: 연령대별 인구 통계. 0-4세, 5-9세 등 5세 단위로 나눈 연령대별 남녀 인구수. 30대, 40대, 고령, 청년, 노인 같은 연령 관련 질문에 사용. 컬럼: 행정구역, 년월, 연령대, 항목(총인구수/남자인구수/여자인구수), 값",
        "population_gender_stats 테이블: 성별 인구 통계. 지역별 총인구수, 남자인구수, 여자인구수 정보. 전체 인구나 성별 인구 질문에 사용. 연령대 구분 없음. 컬럼: 행정구역, 년월, 항목(총인구수/남자인구수/여자인구수), 값",
        "population_stats 테이블: 세대수 통계. 지역별 세대수, 가구수 정보. 세대, 가구 관련 질문에 사용. 컬럼: 행정구역, 년월, 값",
    ]

    metadatas = [
        {
            "table_name": "population_age_stats",
            "keywords": "연령,나이,고령,청년,노인,65세이상,30대,40대,5세단위,연령대",
            "columns": "행정구역,년월,연령대,항목,값",
        },
        {
            "table_name": "population_gender_stats",
            "keywords": "총인구수,인구,남자,여자,성별,인구수,사람,거주민",
            "columns": "행정구역,년월,항목,값",
        },
        {
            "table_name": "population_stats",
            "keywords": "세대,세대수,가구,가구수,household",
            "columns": "행정구역,년월,값",
        },
    ]

    # Chroma 벡터스토어 생성
    vectorstore = Chroma.from_texts(
        texts=documents,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory="./embedding_db",
    )

    print("ChromaDB 임베딩 완료")
    print(f"저장 위치: ./embedding_db")
    print(f"문서 수: {len(documents)}")

    return vectorstore


def search_tables(query: str, n_results: int = 1) -> list:
    """
    질문으로 관련 테이블 검색

    Args:
        query: 사용자 질문
        n_results: 반환할 테이블 수

    Returns:
        list: 관련 테이블 정보 리스트
    """
    embeddings = UpstageEmbeddings(
        api_key=settings.UPSTAGE_API_KEY, model="solar-embedding-1-large"
    )

    vectorstore = Chroma(
        persist_directory="./embedding_db", embedding_function=embeddings
    )

    results = vectorstore.similarity_search(query, k=n_results)

    # 결과 포맷팅
    tables = []
    for doc in results:
        tables.append(
            {
                "table_name": doc.metadata.get("table_name"),
                "keywords": doc.metadata.get("keywords"),
                "columns": doc.metadata.get("columns"),
                "description": doc.page_content,
            }
        )

    return tables


if __name__ == "__main__":
    # 초기 설정
    setup_embedding_db()

    # 테스트
    test_queries = [
        "2020년 1월부터 2020년 12월까지 수원시의 세대수 모두 합치면 몇 세대야?",
        "서울에 60대 노인은 몇 명이야?",
        "경기도 여자 인구는?",
    ]

    print("\n" + "=" * 60)
    print("테스트 검색")
    print("=" * 60)

    for query in test_queries:
        results = search_tables(query, n_results=1)
        table_name = results[0]["table_name"]
        print(f"\n질문: {query}")
        print(f"선택된 테이블: {table_name}")
