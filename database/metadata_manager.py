"""
database/metadata_manager.py

테이블 메타데이터 관리 모듈
- DB에서 tables_metadata 로드 및 캐싱
- 짧은 문서 생성 (임베딩용, 100~200토큰)
- 상세 정보 반환 (검색 후 사용)
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional

PERIOD_COLUMN_MAP = {
    "month": "년월",
    "year": "년도",
}


class MetadataManager:
    """테이블 메타데이터 관리 클래스"""

    def __init__(self):
        """초기화 및 전체 메타데이터 캐싱"""
        from database.connection import db_manager

        self._cache: Dict[str, Dict] = {}

        # Turso DB 연결 사용
        db = db_manager.get_db()
        conn = db._engine.raw_connection()

        # 전체 메타데이터 로드
        self._load_all_to_cache(conn)

    def _load_all_to_cache(self, conn):
        """DB에서 전체 메타데이터를 메모리에 캐싱"""
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM tables_metadata")
            rows = cursor.fetchall()

            # 컬럼명 가져오기
            column_names = [desc[0] for desc in cursor.description]

            for row in rows:
                # 튜플을 딕셔너리로 변환
                row_dict = dict(zip(column_names, row))
                table_name = row_dict["table_name"]
                self._cache[table_name] = row_dict

            print(
                f"✅ MetadataManager: {len(self._cache)}개 테이블 메타데이터 로드 완료"
            )

        except Exception as e:
            print(f"❌ 메타데이터 로드 실패: {e}")
            raise

    def get_short_doc(self, table_name: str) -> Optional[str]:
        """
        짧은 문서 생성 (임베딩용, 100~200토큰)

        Args:
            table_name: 테이블명

        Returns:
            str: 짧은 설명 문서 (임베딩용)
        """
        if table_name not in self._cache:
            return None

        meta = self._cache[table_name]

        # 여러 줄 문자열 (벡터 검색 정확도 향상)
        short_doc = f"""
테이블: {table_name}
설명: {meta['short_desc_ko']}
분류: {meta['topic_main']} > {meta['topic_sub']}
키워드: {meta['keywords_ko']}
기간: {meta['period_start']} ~ {meta['period_end']}
"""

        # ===== 디버깅 추가 =====
        if "migration" in table_name or "gender" in table_name:
            print(f"\n[임베딩 문서] {table_name}:")
            print(short_doc)
            print("-" * 60)
        # ===== 추가 끝 =====

        return short_doc.strip()

    def get_detailed_info(self, table_name: str) -> Optional[Dict]:
        """
        상세 정보 반환 (검색 후 사용)

        Args:
            table_name: 테이블명

        Returns:
            dict: 전체 메타데이터 (컬럼 스키마, 예시 쿼리, 주의사항 등)
        """
        if table_name not in self._cache:
            return None

        meta = self._cache[table_name]

        # JSON 문자열 파싱
        columns_list = json.loads(meta["columns_schema_outline"])
        column_detail = json.loads(meta["column_schema_detail"])
        time_freq = meta.get("time_freq", "month")

        return {
            "table_name": table_name,
            "description": meta["short_desc_ko"],
            "topic_main": meta["topic_main"],
            "topic_sub": meta["topic_sub"],
            "keywords": meta["keywords_ko"],
            "columns": ", ".join(columns_list),  # 리스트 → 문자열 (프롬프트용)
            "column_detail": column_detail,
            "example_queries": meta["example_queries_ko"],
            "caution": meta["caution_ko"],
            "period": f"{meta['period_start']} ~ {meta['period_end']}",
            "geo_level": meta.get("geo_level", ""),
            "time_freq": meta.get("time_freq", ""),
            "period_column": PERIOD_COLUMN_MAP.get(time_freq, "년월"),
        }

    def get_table_names(self) -> List[str]:
        """모든 테이블명 반환"""
        return list(self._cache.keys())

    def filter_by_category(self, category: str) -> List[str]:
        """
        카테고리로 필터링

        Args:
            category: 카테고리명 (예: '인구', '주거')

        Returns:
            list: 해당 카테고리의 테이블명 리스트
        """
        result = []
        for table_name, meta in self._cache.items():
            if meta["topic_main"] == category:
                result.append(table_name)
        return result

    def exists(self, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        return table_name in self._cache


# 싱글톤 인스턴스
_metadata_manager = None


def get_metadata_manager() -> MetadataManager:
    """
    MetadataManager 싱글톤 인스턴스 반환

    Returns:
        MetadataManager 인스턴스
    """
    global _metadata_manager

    if _metadata_manager is None:
        _metadata_manager = MetadataManager()

    return _metadata_manager


# 테스트 코드
if __name__ == "__main__":
    # 초기화
    manager = get_metadata_manager()

    # 테이블 목록
    print("\n📋 테이블 목록:")
    print(manager.get_table_names())

    # 짧은 문서 테스트
    print("\n📄 짧은 문서 (population_age_stats):")
    short_doc = manager.get_short_doc("population_age_stats")
    print(short_doc)
    print(f"줄 수: {short_doc.count(chr(10)) + 1}")

    # 상세 정보 테스트
    print("\n📊 상세 정보 (population_age_stats):")
    detail = manager.get_detailed_info("population_age_stats")
    print(f"- 설명: {detail['description'][:50]}...")
    print(f"- 컬럼: {detail['columns']}")
    print(f"- 기간: {detail['period']}")
    print(f"- 필드 개수: {len(detail)}")

    # 카테고리 필터링 테스트
    print("\n🏷️ 카테고리 필터링 (인구):")
    population_tables = manager.filter_by_category("인구")
    print(population_tables)

    # 검증
    print("\n✅ 검증:")
    assert len(manager.get_table_names()) >= 4, "테이블 4개 이상"
    assert short_doc.count("\n") >= 4, "짧은 문서 5줄 이상"
    assert "테이블:" in short_doc, "라벨 포함"
    assert isinstance(detail["columns"], str), "columns는 문자열"
    assert "topic_main" in detail, "topic_main 필드 필수"
    assert len(detail) == 12, "12개 필드 필수"
    print("모든 검증 통과!")
