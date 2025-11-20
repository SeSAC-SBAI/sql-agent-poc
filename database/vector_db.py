"""
임베딩 데이터베이스 설정 및 검색
"""

import sys
import re
import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_upstage import UpstageEmbeddings
from langchain_chroma import Chroma
from config.settings import settings


# ============================================================
# 카테고리별 키워드 사전 (메타데이터 기반)
# ============================================================

CATEGORY_KEYWORDS = {
    "노동": [
        # 경제활동 관련
        "경제활동",
        "취업",
        "실업",
        "고용",
        "일자리",
        "구직",
        "실업자",
        "취업자",
        "고용률",
        "실업률",
        "경제활동참가율",
        # 근로 관련
        "근로",
        "임금",
        "급여",
        "상용",
        "임시",
        "일용",
        "자영업",
        # 산업 관련
        "산업",
        "직종",
        "직업",
        "종사",
        "근로자",
        "노동자",
        # 농가/비농가
        "농가",
        "비농가",
        # 취업 준비
        "취업준비",
        "구직활동",
    ],
    "인구": [
        "인구",
        "주민",
        "인구수",
        "세대",
        "가구",
        "세대수",
        "가구수",
        "출생",
        "사망",
        "출산",
        "합계출산율",
        "조출생률",
        "자연증가",
        "인구이동",
        "전입",
        "전출",
        "순이동",
        "남자",
        "여자",
        "남성",
        "여성",
        # 연령 관련 (패턴 매칭과 병행)
        "연령",
        "나이",
        "연령대",
        "연령별",
        "나이대",
        "노인",
        "고령",
        "청년",
        "유아",
        "아동",
        "청소년",
        "장년",
        "중년",
        "영유아",
        "미성년",
        "성인",
        "노년",
    ],
    "주거": [
        "주택",
        "아파트",
        "주거",
        "연립",
        "다세대",
        "단독주택",
        "주택이조사",
        "주택수",
        "주택종류",
        "비주거",
    ],
    "국토이용": ["토지", "지목", "국토", "면적", "용도지역", "용도지구"],
    "경제일반·경기": ["사업체", "종사자", "사업체수", "종사자수", "전국사업체조사"],
    "무역·국제수지": ["수출", "수입", "무역", "국제수지", "무역수지", "경상수지"],
    "도소매·서비스": ["소매", "도매", "서비스", "판매", "매출"],
}

# 카테고리별 테이블 맵 캐싱용
CATEGORY_TABLE_MAP = None


# ============================================================
# 임베딩 & 벡터스토어
# ============================================================


def get_passage_embeddings():
    """
    문서 임베딩용 (벡터 DB 구축 시 사용)

    Returns:
        UpstageEmbeddings: passage 임베딩 모델
    """
    return UpstageEmbeddings(
        api_key=settings.UPSTAGE_API_KEY, model="embedding-passage"
    )


@st.cache_resource
def get_query_embeddings():
    """질문 임베딩용 (검색 시 사용) - 캐싱"""
    print("📌 Query 임베딩 모델 로드 완료")
    return UpstageEmbeddings(api_key=settings.UPSTAGE_API_KEY, model="embedding-query")


@st.cache_resource
def get_vectorstore():
    """벡터스토어 로드 (캐싱)"""
    embeddings = get_query_embeddings()
    print("📌 벡터스토어 로드 완료")
    return Chroma(persist_directory="./embedding_db", embedding_function=embeddings)


def setup_embedding_db(db_path: str = None, force_recreate: bool = False):
    """
    DB에서 메타데이터 읽어서 벡터 DB 생성

    Args:
        db_path: DB 파일 경로
        force_recreate: True면 기존 DB 삭제 후 재생성

    Returns:
        Chroma vectorstore
    """
    import shutil
    from database.metadata_manager import get_metadata_manager

    persist_dir = "./embedding_db"

    if force_recreate and Path(persist_dir).exists():
        print(f"⚠️  기존 벡터 DB 삭제 중: {persist_dir}")
        shutil.rmtree(persist_dir)
        print("✅ 삭제 완료")

    # 메타데이터 매니저
    manager = get_metadata_manager()

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
    embeddings = get_passage_embeddings()

    # Chroma 벡터스토어 생성
    vectorstore = Chroma.from_texts(
        texts=documents,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=persist_dir,
    )

    print(f"✅ 벡터 DB 생성: {len(documents)}개 테이블")
    print(f"📄 임베딩 모델: embedding-passage")
    return vectorstore


# ============================================================
# 카테고리 관련 함수
# ============================================================


def build_category_table_map() -> Dict[str, List[str]]:
    """
    메타데이터에서 카테고리별 테이블 매핑 구축

    Returns:
        {카테고리: [테이블명 리스트]}
    """
    from database.metadata_manager import get_metadata_manager

    manager = get_metadata_manager()
    all_meta = manager._cache  # get_all_tables_metadata() 대신 직접 접근

    category_map = {}
    for table_name, meta in all_meta.items():
        topic = meta.get("topic_main")
        if topic:
            if topic not in category_map:
                category_map[topic] = []
            category_map[topic].append(table_name)

    return category_map


def get_category_table_map() -> Dict[str, List[str]]:
    """카테고리별 테이블 맵 반환 (캐싱)"""
    global CATEGORY_TABLE_MAP
    if CATEGORY_TABLE_MAP is None:
        CATEGORY_TABLE_MAP = build_category_table_map()
    return CATEGORY_TABLE_MAP


def detect_age_related(query: str) -> bool:
    """
    연령 관련 질문인지 패턴으로 감지

    Args:
        query: 사용자 질문

    Returns:
        bool: 연령 관련 질문이면 True
    """

    # 패턴 1: "N세" (0세~150세)
    if re.search(r"\d+세", query):
        return True

    # 패턴 2: "N대" (10대, 20대, ...) - 연령대만 해당
    age_decade_pattern = re.search(r"(\d+)대", query)
    if age_decade_pattern:
        number = int(age_decade_pattern.group(1))

        # 10, 20, 30, ..., 90만 연령대 가능성
        if number >= 10 and number % 10 == 0 and number <= 90:
            # 문맥 확인: 순위 관련 키워드가 있으면 제외
            rank_keywords = [
                "순위",
                "위",
                "많은",
                "큰",
                "도시",
                "기업",
                "회사",
                "국가",
                "강국",
                "업체",
                "상위",
                "하위",
            ]
            if not any(kw in query for kw in rank_keywords):
                return True

    # 패턴 3: "N~N세" (0~14세)
    if re.search(r"\d+~\d+세", query):
        return True

    # 패턴 4: "N세 이상/이하/미만/초과"
    if re.search(r"\d+세\s*(이상|이하|미만|초과)", query):
        return True

    return False


def detect_category(query: str) -> Optional[str]:
    """
    질문에서 카테고리 감지 (예외 처리 포함)

    Args:
        query: 사용자 질문

    Returns:
        str: 카테고리명, 'multiple' (복합), 'meta' (메타질문), None (범위외)
    """

    # 0. 메타 질문 감지 (카테고리 분류 불필요)
    meta_keywords = [
        "무슨 데이터",
        "어떤 데이터",
        "데이터 종류",
        "테이블 목록",
        "뭐 있어",
        "뭐가 있어",
        "통계 종류",
        "어떤 통계",
    ]
    if any(kw in query for kw in meta_keywords):
        return "meta"

    # 1. 각 카테고리별 매칭 점수 계산
    category_scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query)
        if score > 0:
            category_scores[category] = score

    # 1-1. 인구 카테고리 보정: 연령 패턴 감지
    if detect_age_related(query):
        category_scores["인구"] = category_scores.get("인구", 0) + 2  # 가중치 부여
        print(f"  🔍 연령 패턴 감지 → 인구 카테고리 가중치 +2")

    # 2. 매칭된 카테고리가 없으면 None
    if not category_scores:
        return None

    # 3. 복합 카테고리 감지
    if len(category_scores) >= 2:
        # 점수가 비슷한 경우 (차이가 1 이하)
        sorted_scores = sorted(category_scores.items(), key=lambda x: -x[1])
        top_score = sorted_scores[0][1]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

        if top_score - second_score <= 1:
            print(f"  ⚠️  복합 카테고리 감지: {list(category_scores.keys())}")
            return "multiple"

    # 4. 단일 카테고리 (우선순위 적용)
    # 우선순위: 노동 > 주거 > 경제일반·경기 > 무역·국제수지 > 도소매·서비스 > 국토이용 > 인구
    priority_order = [
        "노동",
        "주거",
        "경제일반·경기",
        "무역·국제수지",
        "도소매·서비스",
        "국토이용",
        "인구",
    ]

    for category in priority_order:
        if category in category_scores:
            return category

    return None


def _validate_category_match(
    tables: List[Dict], expected_category: str, strict: bool = False
) -> List[Dict]:
    """
    테이블이 예상 카테고리와 일치하는지 검증

    Args:
        tables: 테이블 정보 리스트
        expected_category: 예상 카테고리
        strict: True면 불일치 제외, False면 경고만

    Returns:
        필터링된 테이블 리스트
    """
    validated = []

    for table in tables:
        topic = table.get("topic_main")

        if topic == expected_category:
            validated.append(table)
        else:
            if strict:
                print(f"  ⚠️  카테고리 불일치 제외: {table['table_name']} ({topic})")
            else:
                print(f"  ℹ️  다른 카테고리 포함: {table['table_name']} ({topic})")
                validated.append(table)  # 복합 질문 가능성 고려해서 포함

    return validated


# ============================================================
# Rule 기반 테이블 감지
# ============================================================


def get_required_tables_by_rule(query: str) -> List[str]:
    """
    Rule 기반 필수 테이블 판단 (복합 카테고리 고려)

    Args:
        query: 사용자 질문

    Returns:
        list: 필수 테이블명 리스트
    """
    required = []

    # Rule 0: 노동 + 연령 (단일 테이블로 해결 가능)
    if any(kw in query for kw in ["취업", "실업", "고용", "경제활동"]):
        if any(
            age in query
            for age in [
                "연령",
                "세대",
                "나이",
                "20대",
                "30대",
                "40대",
                "50대",
                "60대",
                "2030",
                "청년",
                "중년",
                "장년",
                "고령",
            ]
        ) or detect_age_related(query):
            return ["labor_economic_activity_age_stats"]

    # Rule 1: "비중", "비율" → 분자 + 분모 (복합)
    if any(keyword in query for keyword in ["비중", "비율", "%", "퍼센트", "점유율"]):
        # 인구 비중 질문
        if any(
            age_word in query for age_word in ["연령", "나이", "고령", "청년", "노인"]
        ) or detect_age_related(query):
            required.extend(
                ["population_age_stats", "population_gender_stats"]  # 분자  # 분모
            )
        # 취업자 비중 질문
        elif any(labor_word in query for labor_word in ["취업", "실업", "고용"]):
            required.extend(
                [
                    "labor_economic_activity_age_stats",  # 취업자수
                    "population_age_stats",  # 총인구수
                ]
            )

    # Rule 2: "대비" → 비교 대상 (복합)
    if "대비" in query:
        # "인구 대비 취업자"
        if "인구" in query and any(kw in query for kw in ["취업", "고용"]):
            required.extend(
                [
                    "population_gender_stats",  # 인구
                    "labor_economic_activity_age_stats",  # 취업자
                ]
            )

    # Rule 3: "세대" 명시 (단일)
    if "세대" in query or "가구" in query:
        # 노동 관련이 아닐 때만
        if not any(kw in query for kw in ["취업", "실업", "고용", "경제활동"]):
            required.append("population_stats")

    # Rule 4: "주택" 명시 (단일)
    if "주택" in query or "아파트" in query or "주거" in query:
        required.append("housing_type_sido_stats")

    # Rule 5: "밀도" → 인구 + 면적 (복합, 현재 면적 데이터 없으면 스킵)
    if "밀도" in query:
        required.append("population_gender_stats")
        # TODO: 면적 데이터 테이블 추가 시 여기 추가

    return list(set(required))  # 중복 제거


# ============================================================
# 검색 함수
# ============================================================


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

    vectorstore = get_vectorstore()

    # 벡터 검색
    search_kwargs = {"k": n_results * 2}  # 여유있게

    # 카테고리 필터 적용
    if category_filter:
        search_kwargs["filter"] = {"topic_main": category_filter}

    results = vectorstore.similarity_search_with_score(query, **search_kwargs)

    # 임계값 필터링 (거리 2.0 이하만)
    filtered_tables = []
    distance_map = {}

    for doc, distance in results:
        if distance <= 2.0:
            table_name = doc.metadata.get("table_name")
            if table_name:
                filtered_tables.append(table_name)
                distance_map[table_name] = distance

    # 상위 n개만
    top_tables = filtered_tables[:n_results]

    # 상세 정보 로드
    detailed_tables = []
    for table_name in top_tables:
        detailed = manager.get_detailed_info(table_name)
        if detailed:
            detailed["distance"] = round(distance_map[table_name], 3)
            detailed_tables.append(detailed)

    return detailed_tables


def smart_search_tables(query: str, n_results: int = 5) -> List[Dict]:
    """
    스마트 검색: 예외 상황 고려

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

    # 예외 처리
    if category == "meta":
        print("카테고리: 메타 질문 (테이블 목록 요청)")
        # 메타 질문은 특별 처리 (여기서는 전체 검색)
        category = None
    elif category == "multiple":
        print("카테고리: 복합 (여러 카테고리 필요)")
        # 복합 질문은 카테고리 필터 없이 벡터 검색
        category = None
    elif category:
        print(f"카테고리: {category}")

        # 카테고리에 해당하는 테이블 수 확인
        category_map = get_category_table_map()
        available_tables = category_map.get(category, [])
        print(f"  → 해당 카테고리 테이블 수: {len(available_tables)}개")

        # 테이블이 적으면 벡터 검색 수 조정
        if len(available_tables) <= 3:
            n_results = min(n_results, len(available_tables))
            print(f"  → 검색 수 조정: {n_results}개")
    else:
        print("카테고리: 감지 안됨 (전체 검색)")

    # 2. 벡터 검색
    vector_results = search_tables_hierarchical(
        query,
        n_results=n_results * 2,  # 여유있게 검색 (필터링 대비)
        category_filter=(
            category if category not in ["meta", "multiple", None] else None
        ),
    )

    print(f"벡터 검색: {len(vector_results)}개")
    for table in vector_results:
        distance = table.get("distance", "N/A")
        print(f"  - {table['table_name']} (거리: {distance})")

    # 3. Rule 기반 필수 테이블
    required_tables = get_required_tables_by_rule(query)

    if required_tables:
        print(f"Rule 감지: {required_tables}")

    # 4. 병합
    final_results = merge_unique_tables(vector_results, required_tables)

    # 5. 카테고리 일치도 검증 (단일 카테고리일 때만)
    if category and category not in ["meta", "multiple"]:
        final_results = _validate_category_match(
            final_results, category, strict=False  # 복합 질문 가능성 고려
        )

    # 6. 최대 개수 제한
    final_results = final_results[:n_results]

    print(f"최종: {len(final_results)}개 테이블")
    for table in final_results:
        print(f"  ✓ {table['table_name']}")
    print(f"{'='*60}\n")

    return final_results


# ============================================================
# 기존 함수 (하위 호환)
# ============================================================


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
    embeddings = get_query_embeddings()

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


# ============================================================
# 테스트 코드
# ============================================================

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
        "2023년 20대 취업자 수는?",
        "여자 취업준비자는 몇 명이야?",
        "서울 인구 대비 취업자 비율은?",
    ]

    for query in test_queries:
        results = smart_search_tables(query, n_results=3)
        print(f"\n질문: {query}")
        print(f"결과: {[r['table_name'] for r in results]}")
