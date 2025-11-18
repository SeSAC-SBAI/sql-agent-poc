"""데이터 포맷팅 유틸리티"""

import pandas as pd
from typing import List, Dict, Any, Optional


def format_sql_result(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """SQL 결과를 DataFrame으로 변환"""
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def format_number(value: Any) -> str:
    """숫자를 포맷팅"""
    if value is None:
        return "-"
    
    try:
        num = float(value)
        if num >= 1e9:
            return f"{num/1e9:.2f}B"
        elif num >= 1e6:
            return f"{num/1e6:.2f}M"
        elif num >= 1e3:
            return f"{num/1e3:.2f}K"
        else:
            return f"{num:,.0f}"
    except (ValueError, TypeError):
        return str(value)


def format_table_for_display(df: pd.DataFrame, max_rows: int = 100) -> pd.DataFrame:
    """테이블 표시용 포맷팅"""
    if df.empty:
        return df
    
    if len(df) > max_rows:
        return df.head(max_rows)
    
    return df


def extract_sql_from_response(response: str) -> Optional[str]:
    """응답에서 SQL 쿼리 추출"""
    if "```sql" in response:
        start = response.find("```sql") + 6
        end = response.find("```", start)
        if end != -1:
            return response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end != -1:
            sql = response[start:end].strip()
            if sql.upper().startswith("SELECT"):
                return sql
    return None

