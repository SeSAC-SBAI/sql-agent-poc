"""
벡터 DB 초기화 스크립트

최초 1회 또는 tables_metadata 업데이트 시 실행

사용법:
    python scripts/setup_vector_db.py
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.vector_db import setup_embedding_db


def main():
    """벡터 DB 초기화 메인 함수"""

    print("=" * 60)
    print("벡터 DB 초기화 시작")
    print("=" * 60)
    print()

    try:
        # 벡터 DB 생성 (1~2분 소요)
        vectorstore = setup_embedding_db()

        print()
        print("=" * 60)
        print("✅ 벡터 DB 초기화 완료!")
        print("=" * 60)
        print()

        # 테스트 검색
        print("🧪 테스트 검색 중...")
        test_query = "인구"
        results = vectorstore.similarity_search(test_query, k=3)

        print(f"검색어: '{test_query}'")
        print(f"결과: {len(results)}개")
        for i, doc in enumerate(results, 1):
            table_name = doc.metadata.get("table_name", "알 수 없음")
            print(f"  {i}. {table_name}")

        print()
        print("✅ 모든 작업 완료!")
        print()
        print("📁 생성된 파일:")
        print("  ./embedding_db/")
        print()
        print("💡 다음 단계:")
        print("  python test_run.py  # 질문 테스트")
        print("  python tests/test_dataset.py  # 벤치마크 테스트")

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 초기화 실패: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
