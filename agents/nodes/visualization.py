"""
시각화 노드
"""

import json
import pandas as pd
from typing import Dict, Any, Optional, Literal
from langgraph.types import Command
from config.settings import settings
from utils.prompts import (
    VISUALIZATION_SYSTEM_PROMPT,
    VISUALIZATION_PROMPT,
    VISUALIZATION_ERROR_PROMPT,
)
from frontend.utils.format import extract_column_names
from agents.helpers import get_llm


def determine_visualization(
    question: str, columns: list, row_count: int, sample_data: list
) -> Optional[Dict[str, Any]]:
    """
    질문과 데이터를 분석하여 시각화 메타데이터 생성
    """
    try:
        if row_count == 0 or len(columns) < 2:
            return None

        columns = [str(col) for col in columns]

        llm = get_llm()

        prompt = VISUALIZATION_PROMPT.format(
            question=question,
            columns=", ".join(columns),
            row_count=row_count,
            sample_data=str(sample_data[:3]),
        )

        messages = [
            {"role": "system", "content": VISUALIZATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = llm.invoke(messages)
        result_text = response.content.strip()

        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        viz_metadata = json.loads(result_text.strip())

        required_keys = ["type", "x_column", "y_column", "title"]
        if not all(key in viz_metadata for key in required_keys):
            return None

        if (
            viz_metadata["x_column"] not in columns
            or viz_metadata["y_column"] not in columns
        ):
            return None

        return viz_metadata

    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"LLM 응답: {result_text if 'result_text' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"시각화 메타데이터 생성 오류: {e}")
        print(f"columns 타입: {type(columns)}, 값: {columns}")
        return None


def plan_visualization(state: Dict[str, Any]) -> Command[Literal["generate_response"]]:
    """
    시각화 노드
    """
    try:
        question = state.get("user_query", "")
        sql_result = state.get("query_result", None)

        print(f"[DEBUG] sql_result 타입: {type(sql_result)}")

        if sql_result is None or not sql_result:
            return Command(
                goto="generate_response",
                update={
                    "chart_spec": None,
                    "chart_data": None,
                    "extended_sql": None,
                    "target_value": None,
                },
            )

        # 단일 값인 경우 SQL 확장
        chart_data = None
        extended_sql_used = None
        target_value = None

        if len(sql_result) == 1:
            print("[DEBUG] 단일 값 감지 - SQL 확장 시도")
            extended_sql, target = expand_sql_time_range(state.get("sql_query", ""))

            if extended_sql:
                from database.connection import db_manager

                db = db_manager.get_db()
                try:
                    extended_result_str = db.run(extended_sql)
                    import ast

                    extended_result = (
                        ast.literal_eval(extended_result_str)
                        if extended_result_str
                        else []
                    )

                    if len(extended_result) > 1:
                        print(f"[DEBUG] SQL 확장 성공: {len(extended_result)}개 데이터")
                        sql_result = extended_result
                        chart_data = extended_result
                        extended_sql_used = extended_sql
                        target_value = target
                    else:
                        print("[DEBUG] SQL 확장 결과 1개 이하, 원본 사용")
                        chart_data = sql_result
                except Exception as e:
                    print(f"[DEBUG] SQL 확장 실패: {e}")
                    chart_data = sql_result
            else:
                print("[DEBUG] SQL 확장 불가 (패턴 미일치)")
                chart_data = sql_result
        else:
            chart_data = sql_result

        # DataFrame 변환
        if isinstance(sql_result, list):
            print("[DEBUG] sql_result를 DataFrame으로 변환 중...")
            if not sql_result:
                return Command(
                    goto="generate_response",
                    update={
                        "chart_spec": None,
                        "chart_data": None,
                        "extended_sql": None,
                        "target_value": None,
                    },
                )

            # 확장 SQL 사용했으면 그걸로 컬럼명 추출
            sql_for_columns = extended_sql_used or state.get("sql_query", "")

            col_names = extract_column_names(sql_for_columns, len(sql_result[0]))
            print(f"[DEBUG] 추출된 컬럼명: {col_names}")

            df = pd.DataFrame(sql_result, columns=col_names)
            df.columns = [str(col) for col in df.columns]

            print(f"[DEBUG] DataFrame 생성 완료: {df.shape}")
            print(f"[DEBUG] DataFrame columns (최종): {list(df.columns)}")

        elif isinstance(sql_result, pd.DataFrame):
            df = sql_result
            df.columns = [str(col) for col in df.columns]
        else:
            print(f"[DEBUG] 지원하지 않는 타입: {type(sql_result)}")
            return Command(
                goto="generate_response",
                update={
                    "chart_spec": None,
                    "chart_data": None,
                    "extended_sql": None,
                    "target_value": None,
                },
            )

        columns = list(df.columns)
        row_count = len(df)
        sample_data = df.head(3).values.tolist()

        print(
            f"[DEBUG] plan_visualization - columns: {columns}, row_count: {row_count}"
        )

        if len(columns) < 2:
            print(f"[DEBUG] 컬럼 수 부족: {len(columns)}개")
            return Command(
                goto="generate_response",
                update={
                    "chart_spec": None,
                    "chart_data": None,
                    "extended_sql": None,
                    "target_value": None,
                },
            )

        viz_metadata = determine_visualization(
            question=question,
            columns=columns,
            row_count=row_count,
            sample_data=sample_data,
        )

        print(f"[DEBUG] viz_metadata: {viz_metadata}")

        return Command(
            goto="generate_response",
            update={
                "chart_spec": viz_metadata,
                "chart_data": chart_data,
                "extended_sql": extended_sql_used,
                "target_value": target_value,
            },
        )

    except Exception as e:
        print(f"시각화 노드 오류: {e}")
        import traceback

        traceback.print_exc()
        return Command(
            goto="generate_response",
            update={
                "chart_spec": None,
                "chart_data": None,
                "extended_sql": None,
                "target_value": None,
            },
        )


def expand_sql_time_range(sql_query: str) -> tuple[Optional[str], Optional[str]]:
    """
    단일 값 SQL을 시계열 범위로 확장

    Returns:
        (확장된 SQL, 타겟 값)
    """
    import re

    # 년월 패턴
    pattern_month = r"년월\s*=\s*['\"](\d{4}-\d{2})['\"]"
    match_month = re.search(pattern_month, sql_query)

    # 년도 패턴
    pattern_year = r"년도\s*=\s*['\"](\d{4})['\"]"
    match_year = re.search(pattern_year, sql_query)

    if match_month:
        # 월 단위 확장
        target_value = match_month.group(1)
        year, month = target_value.split("-")
        year = int(year)

        start = f"{year-1}-{month}"
        end = f"{year+1}-{month}"

        if "SELECT 년월" not in sql_query:
            sql_query = sql_query.replace("SELECT ", "SELECT 년월, ", 1)

        expanded_sql = re.sub(
            pattern_month, f"년월 BETWEEN '{start}' AND '{end}'", sql_query
        )

        if "ORDER BY" not in expanded_sql:
            expanded_sql = expanded_sql.rstrip(";") + " ORDER BY 년월;"

    elif match_year:
        # 년도 단위 확장
        target_value = match_year.group(1)
        year = int(target_value)

        start = f"{year-2}"
        end = f"{year+2}"

        if "SELECT 년도" not in sql_query:
            sql_query = sql_query.replace("SELECT ", "SELECT 년도, ", 1)

        expanded_sql = re.sub(
            pattern_year, f"년도 BETWEEN '{start}' AND '{end}'", sql_query
        )

        if "ORDER BY" not in expanded_sql:
            expanded_sql = expanded_sql.rstrip(";") + " ORDER BY 년도;"
    else:
        print("[DEBUG] 년월/년도 패턴을 찾을 수 없음")
        return None, None

    print(f"[DEBUG] 타겟 값: {target_value}")
    print(f"[DEBUG] 원본 SQL: {sql_query}")
    print(f"[DEBUG] 확장 SQL: {expanded_sql}")

    return expanded_sql, target_value
