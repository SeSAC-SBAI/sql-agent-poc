"""
데이터베이스 연결 관리 모듈
"""

from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
from config import settings


class DatabaseManager:
    """데이터베이스 연결 및 관리"""

    def __init__(self):
        self.db_uri = settings.DB_URI
        self.db = None
        self.engine = None

    def connect(self):
        """데이터베이스 연결"""
        try:
            # Turso용 SQLAlchemy 엔진 생성
            self.engine = create_engine(
                self.db_uri,
                connect_args={
                    "check_same_thread": False,  # 멀티스레드 지원
                    "auth_token": settings.TURSO_AUTH_TOKEN,
                },
            )

            # LangChain SQLDatabase 래퍼 생성
            self.db = SQLDatabase(self.engine)

            print(f"✅ Turso DB 연결 성공: {settings.TURSO_DATABASE_URL}")
            return self.db

        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            raise

    def get_db(self):
        """DB 인스턴스 반환"""
        if self.db is None:
            self.connect()
        return self.db

    def test_connection(self):
        """연결 테스트"""
        if self.db is None:
            self.connect()

        try:
            # 테이블 목록 조회
            tables = self.db.get_usable_table_names()
            print(f"📊 사용 가능한 테이블: {tables}")

            # 샘플 쿼리 실행
            result = self.db.run("SELECT COUNT(*) FROM population_gender_stats;")
            print(f"📈 population_gender_stats 행 수: {result}")

            return True

        except Exception as e:
            print(f"❌ 연결 테스트 실패: {e}")
            return False

    def get_schema_info(self):
        """전체 스키마 정보 조회"""
        if self.db is None:
            self.connect()

        return self.db.get_table_info()

    def close(self):
        """연결 종료"""
        if self.engine:
            self.engine.dispose()
            print("✅ DB 연결 종료")


# 전역 DB 매니저 인스턴스
db_manager = DatabaseManager()
