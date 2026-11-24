import numpy as np
import pandas as pd
import streamlit as st

from utils.charts import (
    build_overview_matrix_heatmap,
    build_seoul_map_heatmap,
    build_trend_chart,
)
from utils.data_loader import (
    HOUSEHOLD_INFO,
    HOUSEHOLD_ORDER,
    METRIC_OPTIONS,
    aggregate_metrics,
    load_seoul_geojson,
    load_summary_gu_ym,
)


def render_overview(selected_years: list[int], selected_buildings: list[str], metric_label: str, stat_mode: str):
    metric_info = METRIC_OPTIONS[metric_label]
    metric_col = metric_info["prefix"]
    unit = metric_info["unit"]
    short_label = metric_info["short"]

    st.markdown(
        """
        <div class="hero-banner" style="background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 55%, #2563EB 100%);">
            <div class="hero-badge">서울특별시 전월세 실거래가 분석 · 2021~2025</div>
            <div class="hero-title">🏠 서울 월세 가격 비교 대시보드 (1~4인가구)</div>
            <div class="hero-subtitle">
                핵심 질문: <b>“서울시 25개 자치구의 월세 부담은 가구 규모(1~4인가구)와 입지에 따라 얼마나 다르게 나타날까?”</b><br>
                왼쪽 사이드바에서 가구별 전용 페이지로 이동하거나, 아래에서 전체 가구 규모를 한눈에 비교해 보세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = load_summary_gu_ym()
    df_filt = df_all[
        df_all["연도"].isin(selected_years) & df_all["건물용도"].isin(selected_buildings)
    ].copy()

    if df_filt.empty:
        st.warning("선택한 필터 조건에 해당하는 데이터가 없습니다. 사이드바에서 연도와 건물용도를 선택해 주세요.")
        return

    # 1) Household KPI Summary Cards (4 columns)
    hh_agg = aggregate_metrics(df_filt, ["가구유형"], stat_mode=stat_mode)
    hh_map = {r["가구유형"]: r for _, r in hh_agg.iterrows()}
    total_tx = int(hh_agg["건수"].sum())

    cols = st.columns(4)
    for idx, hh in enumerate(HOUSEHOLD_ORDER):
        info = HOUSEHOLD_INFO[hh]
        row = hh_map.get(hh)
        with cols[idx]:
            if row is not None:
                share = row["건수"] / total_tx * 100 if total_tx > 0 else 0
                st.markdown(
                    f"""
                    <div class="hh-card" style="border-top-color: {info['color']};">
                        <div class="hh-card-title">{info['icon']} {hh}</div>
                        <div class="hh-card-area">{info['area_label']}</div>
                        <div class="hh-card-price" style="color: {info['color']};">{row[metric_col]:,.1f} <span style="font-size:0.9rem;font-weight:600;color:#475569;">{unit}</span></div>
                        <div class="hh-card-meta">
                            보증금 {stat_mode}: <b>{row['보증금']:,.0f}만원</b><br>
                            환산월세: <b>{row['환산월세']:,.1f}만원</b><br>
                            거래량: {int(row['건수']):,}건 ({share:.1f}%)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info(f"{hh} 데이터 없음")

    # Dynamic overview insight
    if "1인가구" in hh_map and "4인가구" in hh_map:
        v1 = hh_map["1인가구"][metric_col]
        v4 = hh_map["4인가구"][metric_col]
        ratio = v4 / v1 if v1 > 0 else 0
        dep1 = hh_map["1인가구"]["보증금"]
        dep4 = hh_map["4인가구"]["보증금"]
        st.markdown(
            f"""
            <div class="insight-box">
                💡 <b>핵심 요약 ({min(selected_years)}~{max(selected_years)}년 · {stat_mode} 기준)</b>:
                서울 전체 <b>{short_label}</b>은 1인가구 <b>{v1:,.1f}{unit}</b>에서 4인가구 <b>{v4:,.1f}{unit}</b>로
                약 <b>{ratio:.2f}배</b> 상승합니다. 특히 보증금은 1인가구({dep1:,.0f}만원) 대비 4인가구({dep4:,.0f}만원)가
                크게 높아지므로, 보증금을 월세로 환산한 <b>환산월세</b> 지표와 함께 비교하는 것이 정확합니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2) Interactive Seoul Map Heatmap with Household Switcher
    st.markdown('<div class="section-title">🗺️ 서울 지도 위 가구별 월세 히트맵</div>', unsafe_allow_html=True)
    c_ctrl1, c_ctrl2 = st.columns([1.4, 1.6])
    with c_ctrl1:
        map_hh = st.radio(
            "지도에 표시할 가구 유형",
            ["전체 가구"] + HOUSEHOLD_ORDER,
            horizontal=True,
            key="overview_map_hh",
        )
    with c_ctrl2:
        map_mode = st.radio(
            "히트맵 표현 방식",
            ["자치구 경계 히트맵 (Choropleth)", "연속 열지도 히트맵 (Density)"],
            horizontal=True,
            key="overview_map_mode",
        )

    map_src = df_filt if map_hh == "전체 가구" else df_filt[df_filt["가구유형"] == map_hh]
    gu_agg = aggregate_metrics(map_src, ["자치구명"], stat_mode=stat_mode)
    geojson = load_seoul_geojson()

    fig_map = build_seoul_map_heatmap(
        gu_df=gu_agg,
        geojson=geojson,
        metric_col=metric_col,
        metric_label=f"{map_hh} {short_label} ({stat_mode})",
        unit=unit,
        map_mode=map_mode,
        colorscale="YlOrRd",
        height=540,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")

    # 3) Matrix Heatmap (25 Gu x 4 Households) + Yearly Trend Comparison
    col_left, col_right = st.columns([1.25, 1.0])

    with col_left:
        st.markdown('<div class="section-title">🔥 25개 자치구 × 가구유형 가격 히트맵 매트릭스</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-caption">각 자치구에서 1~4인가구로 커질수록 {short_label}({unit})이 어떻게 상승하는지 한눈에 비교합니다.</div>',
            unsafe_allow_html=True,
        )
        matrix_df = aggregate_metrics(df_filt, ["자치구명", "가구유형"], stat_mode=stat_mode)
        fig_matrix = build_overview_matrix_heatmap(matrix_df, metric_col, short_label, unit, height=650)
        st.plotly_chart(fig_matrix, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-title">📈 연도별 가구유형 월세 추이 (2021~2025)</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">전체 연도 흐름을 기준으로 가구 규모별 가격 상승 폭을 비교합니다.</div>',
            unsafe_allow_html=True,
        )
        df_bldg = df_all[df_all["건물용도"].isin(selected_buildings)]
        trend_hh = aggregate_metrics(df_bldg, ["연도", "가구유형"], stat_mode=stat_mode)
        trend_hh["연도_str"] = trend_hh["연도"].astype(str) + "년"
        fig_trend = build_trend_chart(
            trend_hh,
            x_col="연도_str",
            metric_col=metric_col,
            metric_label=short_label,
            unit=unit,
            color_col="가구유형",
            height=340,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown('<div class="section-title">🏆 가구유형별 최고가 · 최저가 자치구 요약</div>', unsafe_allow_html=True)
        summary_rows = []
        for hh in HOUSEHOLD_ORDER:
            sub = matrix_df[matrix_df["가구유형"] == hh]
            if not sub.empty:
                top_r = sub.loc[sub[metric_col].idxmax()]
                bot_r = sub.loc[sub[metric_col].idxmin()]
                gap = top_r[metric_col] / bot_r[metric_col] if bot_r[metric_col] > 0 else 0
                summary_rows.append(
                    {
                        "가구유형": hh,
                        "최고가 자치구": f"{top_r['자치구명']} ({top_r[metric_col]:,.1f})",
                        "최저가 자치구": f"{bot_r['자치구명']} ({bot_r[metric_col]:,.1f})",
                        "지역 격차": f"{gap:.2f}배",
                    }
                )
        if summary_rows:
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
