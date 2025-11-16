"""
데이터베이스 연결 관리 모듈 (Turso 지원)
"""

from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
from config import settings


class DatabaseManager:
    """데이터베이스 연결 및 관리"""

    def __init__(self):
        # Turso DB 사용 여부 확인
        if hasattr(settings, 'TURSO_DATABASE_URL') and settings.TURSO_DATABASE_URL:
            # libsql 드라이버 사용
            self.db_uri = f"{settings.TURSO_DATABASE_URL}?authToken={settings.TURSO_AUTH_TOKEN}"
        else:
            # 로컬 SQLite
            self.db_uri = settings.DB_URI
        
        self.db = None
        self.engine = None

    def connect(self):
        """데이터베이스 연결"""
        try:
            # SQLAlchemy 엔진 생성
            connect_args = {}
            if "https://" not in self.db_uri:
                connect_args["check_same_thread"] = False
            
            self.engine = create_engine(
                self.db_uri,
                connect_args=connect_args
            )

            # LangChain SQLDatabase 래퍼 생성
            self.db = SQLDatabase(self.engine)

            db_name = "Turso DB" if "turso.io" in self.db_uri else settings.DB_PATH
            print(f"✅ DB 연결 성공: {db_name}")
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

            # 샘플 쿼리 실행 (테이블이 있을 경우)
            if tables:
                first_table = tables[0]
                result = self.db.run(f"SELECT COUNT(*) FROM {first_table};")
                print(f"📈 {first_table} 행 수: {result}")

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