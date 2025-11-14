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
    
    # Google API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # LangSmith
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "sql-agent-poc")

    # Database
    DB_PATH: str = os.getenv("DB_PATH")
    DB_URI: str = f"sqlite:///{BASE_DIR / DB_PATH}"

    # LLM 설정
    MODEL_NAME: str = "solar-pro2"
    TEMPERATURE: float = 0.0

    def validate(self):
        """필수 설정 값 검증"""
        if not self.UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY가 설정되지 않았습니다.")

        db_full_path = BASE_DIR / self.DB_PATH
        if not db_full_path.exists():
            raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다: {db_full_path}")

        print("✅ 설정 검증 완료")
        print(f"   - DB 경로: {db_full_path}")
        print(f"   - LangSmith 추적: {self.LANGCHAIN_TRACING_V2}")
        print(f"   - 모델: {self.MODEL_NAME}")


# 전역 설정 객체
settings = Settings()