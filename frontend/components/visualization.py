"""
시각화 컴포넌트
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Optional
from frontend.styles.premium import PREMIUM_COLORS


def create_chart(df: pd.DataFrame, viz_metadata: Dict[str, Any]) -> Optional[go.Figure]:
    """
    시각화 메타데이터를 기반으로 차트 생성

    Args:
        df: 데이터프레임
        viz_metadata: 시각화 메타데이터
            - type: 차트 타입 (line, bar, pie)
            - x_column: x축 컬럼명
            - y_column: y축 컬럼명
            - title: 차트 제목

    Returns:
        Plotly Figure 또는 None
    """
    try:
        print(
            f"[DEBUG create_chart] df type: {type(df)}, empty: {df.empty if hasattr(df, 'empty') else 'N/A'}"
        )
        print(f"[DEBUG create_chart] viz_metadata: {viz_metadata}")

        if df is None or df.empty or viz_metadata is None:
            print("[DEBUG create_chart] df나 viz_metadata가 None이거나 비어있음")
            return None

        chart_type = viz_metadata.get("type", "bar")
        x_col = viz_metadata.get("x_column")
        y_col = viz_metadata.get("y_column")
        title = viz_metadata.get("title", "")

        print(
            f"[DEBUG create_chart] chart_type: {chart_type}, x_col: {x_col}, y_col: {y_col}"
        )
        print(f"[DEBUG create_chart] df.columns: {list(df.columns)}")

        if x_col not in df.columns or y_col not in df.columns:
            print(
                f"[DEBUG create_chart] 컬럼이 DataFrame에 없음. x_col={x_col}, y_col={y_col}"
            )
            return None

        print(f"[DEBUG create_chart] y_col 변환 전 타입: {df[y_col].dtype}")
        df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
        print(f"[DEBUG create_chart] y_col 변환 후 타입: {df[y_col].dtype}")

        if chart_type == "line":
            fig = create_line_chart(df, x_col, y_col, title)
        elif chart_type == "pie":
            fig = create_pie_chart(df, x_col, y_col, title)
        else:
            fig = create_bar_chart(df, x_col, y_col, title)

        print(f"[DEBUG create_chart] 차트 생성 완료: {type(fig)}")
        return fig

    except Exception as e:
        print(f"[ERROR create_chart] 차트 생성 오류: {e}")
        import traceback

        traceback.print_exc()
        return None


def create_line_chart(
    df: pd.DataFrame, x_col: str, y_col: str, title: str
) -> go.Figure:
    """선 그래프 생성"""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines+markers",
            line=dict(color="#667eea", width=4, shape="spline"),
            marker=dict(size=10, color="#764ba2", line=dict(color="white", width=2)),
            fill="tonexty",
            fillcolor="rgba(102, 126, 234, 0.1)",
            hovertemplate="<b>%{x}</b><br>값: %{y:,.0f}<extra></extra>",
        )
    )

    apply_premium_layout(fig, title)
    return fig


def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """막대 그래프 생성"""
    print(f"[DEBUG create_bar_chart] 시작")
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df[x_col],
            y=df[y_col],
            marker=dict(
                color=df[y_col],
                colorscale=[[0, "#667eea"], [1, "#764ba2"]],
                line=dict(color="rgba(102, 126, 234, 0.3)", width=2),
            ),
            hovertemplate="<b>%{x}</b><br>값: %{y:,.0f}<extra></extra>",
        )
    )

    print(f"[DEBUG create_bar_chart] trace 추가 완료")
    apply_premium_layout(fig, title)
    print(f"[DEBUG create_bar_chart] layout 적용 완료")
    return fig


def create_pie_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """파이 차트 생성"""
    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=df[x_col],
            values=df[y_col],
            marker=dict(colors=PREMIUM_COLORS, line=dict(color="white", width=2)),
            textfont=dict(size=14, color="white", family="Inter"),
            hole=0.4,
            hovertemplate="<b>%{label}</b><br>값: %{value:,.0f}<br>비율: %{percent}<extra></extra>",
        )
    )

    apply_premium_layout(fig, title)
    return fig


def apply_premium_layout(fig: go.Figure, title: str):
    """프리미엄 레이아웃 적용"""
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color="#1a1a1a", family="Inter")),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13, color="#495057", family="Inter"),
        height=450,
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white", font_size=13, font_family="Inter", bordercolor="#e1e4e8"
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor="#e1e4e8",
            tickfont=dict(size=12, color="#495057"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            showline=False,
            tickfont=dict(size=12, color="#495057"),
        ),
    )


def render_visualization(chart_spec, query_result):
    """기존 차트 렌더링 함수 (호환성 유지)"""
    pass
