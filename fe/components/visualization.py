"""시각화 컴포넌트"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
import plotly.express as px
import plotly.graph_objects as go


def render_visualization(chart_spec: Dict[str, Any], data: Optional[List[Dict[str, Any]]] = None):
    """차트 스펙에 따라 시각화 렌더링"""
    
    if not chart_spec or not data:
        return
    
    chart_type = chart_spec.get("chart_type", "table")
    df = pd.DataFrame(data)
    
    if df.empty:
        st.warning("시각화할 데이터가 없습니다.")
        return
    
    try:
        if chart_type == "line":
            render_line_chart(df, chart_spec)
        elif chart_type == "bar":
            render_bar_chart(df, chart_spec)
        elif chart_type == "pie":
            render_pie_chart(df, chart_spec)
        elif chart_type == "scatter":
            render_scatter_chart(df, chart_spec)
        else:
            st.dataframe(df)
    except Exception as e:
        st.error(f"시각화 오류: {str(e)}")
        st.dataframe(df)


def render_line_chart(df: pd.DataFrame, spec: Dict[str, Any]):
    """선 그래프 렌더링"""
    x_col = spec.get("x_column") or df.columns[0]
    y_col = spec.get("y_column") or df.columns[1]
    
    if x_col not in df.columns or y_col not in df.columns:
        st.dataframe(df)
        return
    
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=spec.get("title", "시계열 데이터"),
        markers=True
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)


def render_bar_chart(df: pd.DataFrame, spec: Dict[str, Any]):
    """막대 그래프 렌더링"""
    x_col = spec.get("x_column") or df.columns[0]
    y_col = spec.get("y_column") or df.columns[1]
    
    if x_col not in df.columns or y_col not in df.columns:
        st.dataframe(df)
        return
    
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=spec.get("title", "비교 데이터"),
        color=x_col
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=12),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)


def render_pie_chart(df: pd.DataFrame, spec: Dict[str, Any]):
    """파이 차트 렌더링"""
    names_col = spec.get("names_column") or df.columns[0]
    values_col = spec.get("values_column") or df.columns[1]
    
    if names_col not in df.columns or values_col not in df.columns:
        st.dataframe(df)
        return
    
    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        title=spec.get("title", "비율 데이터")
    )
    fig.update_layout(
        font=dict(family="Inter", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)


def render_scatter_chart(df: pd.DataFrame, spec: Dict[str, Any]):
    """산점도 렌더링"""
    x_col = spec.get("x_column") or df.columns[0]
    y_col = spec.get("y_column") or df.columns[1]
    
    if x_col not in df.columns or y_col not in df.columns:
        st.dataframe(df)
        return
    
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        title=spec.get("title", "산점도"),
        trendline="ols" if len(df) > 2 else None
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)

