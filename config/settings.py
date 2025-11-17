"""
설정 관리 모듈
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일 로드
load_dotenv(BASE_DIR / ".env")


class Settings:
    """애플리케이션 설정"""

    # Solar API
    UPSTAGE_API_KEY: str = os.getenv("UPSTAGE_API_KEY", "")

    # Google Gemini API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # LangSmith
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "sql-agent-poc")

    # Turso Database
    TURSO_DATABASE_URL: str = os.getenv("TURSO_DATABASE_URL", "")
    TURSO_AUTH_TOKEN: str = os.getenv("TURSO_AUTH_TOKEN", "")

    # Database
    # DB_PATH: str = os.getenv("DB_PATH", "population.db")
    # DB_URI: str = f"sqlite:///{BASE_DIR / DB_PATH}"

    # LLM 설정
    LLM_PROVIDER: str = "gemini"
    MODEL_NAME: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.0

    @property
    def DB_URI(self):
        """DB URI 동적 생성"""
        return f"sqlite+{self.TURSO_DATABASE_URL}?secure=true"

    def validate(self):
        """필수 설정 값 검증"""
        if not self.UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")

        if not self.TURSO_DATABASE_URL:
            raise ValueError("TURSO_DATABASE_URL이 설정되지 않았습니다.")
        if not self.TURSO_AUTH_TOKEN:
            raise ValueError("TURSO_AUTH_TOKEN이 설정되지 않았습니다.")

        print("✅ 설정 검증 완료")
        print(f"   - DB URL: {self.TURSO_DATABASE_URL}")
        print(f"   - DB URI: {self.DB_URI}")
        print(f"   - LangSmith 추적: {self.LANGCHAIN_TRACING_V2}")
        print(f"   - LLM Provider: {self.LLM_PROVIDER}")
        print(f"   - 모델: {self.MODEL_NAME}")


# 전역 설정 객체
settings = Settings()
