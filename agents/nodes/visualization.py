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

        # columns를 문자열로 확실히 변환
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
            return Command(goto="generate_response", update={"chart_spec": None})

        # 리스트를 DataFrame으로 변환
        if isinstance(sql_result, list):
            print("[DEBUG] sql_result를 DataFrame으로 변환 중...")
            if not sql_result:
                return Command(goto="generate_response", update={"chart_spec": None})

            # SQL 쿼리에서 컬럼명 추출
            sql_query = state.get("sql_query", "")

            # SELECT 절에서 컬럼명 추출
            col_names = extract_column_names(sql_query, len(sql_result[0]))
            print(f"[DEBUG] 추출된 컬럼명: {col_names}")

            # DataFrame 생성 시 컬럼명 명시적으로 설정
            df = pd.DataFrame(sql_result, columns=col_names)

            # 컬럼명을 문자열로 확실히 변환
            df.columns = [str(col) for col in df.columns]

            print(f"[DEBUG] DataFrame 생성 완료: {df.shape}")
            print(f"[DEBUG] DataFrame columns (최종): {list(df.columns)}")

        elif isinstance(sql_result, pd.DataFrame):
            df = sql_result
            df.columns = [str(col) for col in df.columns]
        else:
            print(f"[DEBUG] 지원하지 않는 타입: {type(sql_result)}")
            return Command(goto="generate_response", update={"chart_spec": None})

        columns = list(df.columns)
        row_count = len(df)
        sample_data = df.head(3).values.tolist()

        print(
            f"[DEBUG] plan_visualization - columns: {columns}, row_count: {row_count}"
        )

        # 단일 컬럼인 경우 수동으로 차트 스펙 생성
        if len(columns) == 1:
            print(f"[DEBUG] 단일 컬럼 감지 - 막대 차트 생성")
            # 인덱스를 x축으로 사용
            df["항목"] = [f"값 {i+1}" for i in range(len(df))]
            viz_metadata = {
                "type": "bar",
                "x_column": "항목",
                "y_column": columns[0],
                "title": question,
                "description": "결과값",
            }
            return Command(
                goto="generate_response", update={"chart_spec": viz_metadata}
            )

        if len(columns) < 2:
            print(f"[DEBUG] 컬럼 수 부족: {len(columns)}개")
            return Command(goto="generate_response", update={"chart_spec": None})

        viz_metadata = determine_visualization(
            question=question,
            columns=columns,
            row_count=row_count,
            sample_data=sample_data,
        )

        print(f"[DEBUG] viz_metadata: {viz_metadata}")

        return Command(goto="generate_response", update={"chart_spec": viz_metadata})

    except Exception as e:
        print(f"시각화 노드 오류: {e}")
        import traceback

        traceback.print_exc()
        return Command(goto="generate_response", update={"chart_spec": None})
