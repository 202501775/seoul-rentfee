import numpy as np
import pandas as pd
import streamlit as st

from utils.charts import (
    build_building_type_chart,
    build_deposit_rent_scatter,
    build_dong_ranking_chart,
    build_gu_ranking_bar,
    build_seoul_map_heatmap,
    build_trend_chart,
)
from utils.data_loader import (
    HOUSEHOLD_INFO,
    METRIC_OPTIONS,
    aggregate_metrics,
    load_scatter_sample,
    load_seoul_geojson,
    load_summary_dong,
    load_summary_gu_ym,
)
from utils.styles import render_kpi_card


def render_household_page(
    household_type: str,
    selected_years: list[int],
    selected_buildings: list[str],
    metric_label: str,
    stat_mode: str,
):
    info = HOUSEHOLD_INFO[household_type]
    metric_info = METRIC_OPTIONS[metric_label]
    metric_col = metric_info["prefix"]
    unit = metric_info["unit"]
    short_label = metric_info["short"]

    # Hero Banner
    st.markdown(
        f"""
        <div class="hero-banner" style="background: {info['gradient']};">
            <div class="hero-badge">{info['area_label']} · {info['typical']}</div>
            <div class="hero-title">{info['icon']} {info['title']}</div>
            <div class="hero-subtitle">{info['desc']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_all = load_summary_gu_ym()
    df_hh_all_years = df_all[
        (df_all["가구유형"] == household_type) & (df_all["건물용도"].isin(selected_buildings))
    ].copy()
    df_filt = df_hh_all_years[df_hh_all_years["연도"].isin(selected_years)].copy()

    if df_filt.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다. 사이드바 필터를 조정해 주세요.")
        return

    # Aggregate overall & per-district
    overall_df = aggregate_metrics(df_filt, [], stat_mode=stat_mode)
    overall = overall_df.iloc[0]
    gu_df = aggregate_metrics(df_filt, ["자치구명"], stat_mode=stat_mode)

    # YoY delta calculation (latest selected year vs previous year)
    latest_yr = max(selected_years)
    prev_yr = latest_yr - 1
    delta_html = '<span class="delta-neutral">선택 기간 종합</span>'
    if prev_yr in df_hh_all_years["연도"].unique():
        cur_agg = aggregate_metrics(df_hh_all_years[df_hh_all_years["연도"] == latest_yr], [], stat_mode=stat_mode)
        prv_agg = aggregate_metrics(df_hh_all_years[df_hh_all_years["연도"] == prev_yr], [], stat_mode=stat_mode)
        if not cur_agg.empty and not prv_agg.empty and prv_agg.iloc[0][metric_col] > 0:
            cur_v = cur_agg.iloc[0][metric_col]
            prv_v = prv_agg.iloc[0][metric_col]
            pct = (cur_v - prv_v) / prv_v * 100
            cls = "delta-up" if pct > 0 else ("delta-down" if pct < 0 else "delta-neutral")
            sign = "+" if pct > 0 else ""
            delta_html = f'<span class="{cls}">{sign}{pct:.1f}%</span> <span>{latest_yr}년 vs {prev_yr}년</span>'

    top_gu = gu_df.loc[gu_df[metric_col].idxmax()]
    bot_gu = gu_df.loc[gu_df[metric_col].idxmin()]
    gap_ratio = top_gu[metric_col] / bot_gu[metric_col] if bot_gu[metric_col] > 0 else 0

    # 4 KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            f"서울 {household_type} {short_label} ({stat_mode})",
            f"{overall[metric_col]:,.1f} {unit}",
            delta_html,
            accent_color=info["color"],
        )
    with k2:
        render_kpi_card(
            "최고가 자치구",
            f"{top_gu['자치구명']} {top_gu[metric_col]:,.1f}{unit}",
            f"<span>서울 전체 대비 <b>+{(top_gu[metric_col]/overall[metric_col]-1)*100:.1f}%</b></span>",
            accent_color="#DC2626",
        )
    with k3:
        render_kpi_card(
            "최저가 자치구",
            f"{bot_gu['자치구명']} {bot_gu[metric_col]:,.1f}{unit}",
            f"<span>최고가 대비 <b>{gap_ratio:.2f}배</b> 지역 격차</span>",
            accent_color="#16A34A",
        )
    with k4:
        render_kpi_card(
            f"보증금 ({stat_mode}) · 거래량",
            f"{overall['보증금']:,.0f} 만원",
            f"<span>총 <b>{int(overall['건수']):,}건</b> · 평균 {overall['평균면적']:.1f}㎡</span>",
            accent_color="#475569",
        )

    # Dynamic Insight Banner
    st.markdown(
        f"""
        <div class="insight-box" style="border-left-color: {info['color']};">
            💡 <b>{household_type} 데이터 인사이트 ({min(selected_years)}~{max(selected_years)}년)</b>:
            선택된 조건에서 서울 {household_type}의 {short_label} {stat_mode}은 <b>{overall[metric_col]:,.1f}{unit}</b>입니다.
            가장 높은 자치구는 <b>{top_gu['자치구명']}({top_gu[metric_col]:,.1f}{unit})</b>,
            가장 낮은 자치구는 <b>{bot_gu['자치구명']}({bot_gu[metric_col]:,.1f}{unit})</b>으로
            자치구 간 최대 <b>{gap_ratio:.2f}배</b>의 격차가 확인됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main Visualization Row: Seoul Map Heatmap + 25 Gu Ranking Bar
    c_opt1, c_opt2 = st.columns([1.3, 1.0])
    with c_opt1:
        map_mode = st.radio(
            "서울 지도 히트맵 유형",
            ["자치구 경계 히트맵 (Choropleth)", "연속 열지도 히트맵 (Density)"],
            horizontal=True,
            key=f"map_mode_{household_type}",
        )
    with c_opt2:
        gu_list = ["전체 (강조 안 함)"] + sorted(gu_df["자치구명"].unique().tolist())
        highlight_gu = st.selectbox(
            "관심 자치구 강조 (지도·순위 연동)",
            gu_list,
            key=f"hl_gu_{household_type}",
        )

    col_map, col_bar = st.columns([1.45, 1.0])
    geojson = load_seoul_geojson()

    with col_map:
        st.markdown(f'<div class="section-title">🗺️ 서울 지도 위 {household_type} {short_label} 히트맵</div>', unsafe_allow_html=True)
        fig_map = build_seoul_map_heatmap(
            gu_df=gu_df,
            geojson=geojson,
            metric_col=metric_col,
            metric_label=f"{household_type} {short_label}",
            unit=unit,
            map_mode=map_mode,
            colorscale=info["colorscale"],
            highlight_gu=highlight_gu,
            height=540,
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_bar:
        st.markdown(f'<div class="section-title">📊 25개 자치구별 {short_label} 순위</div>', unsafe_allow_html=True)
        fig_bar = build_gu_ranking_bar(
            gu_df=gu_df,
            metric_col=metric_col,
            metric_label=short_label,
            unit=unit,
            accent_color=info["color"],
            highlight_gu=highlight_gu,
            height=540,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Second Row: Time-Series Trend + Building Type Comparison
    col_tr, col_bd = st.columns([1.2, 1.0])

    with col_tr:
        tr_head_l, tr_head_r = st.columns([1.4, 1.0])
        with tr_head_l:
            st.markdown(f'<div class="section-title">📈 {household_type} 시계열 추이</div>', unsafe_allow_html=True)
        with tr_head_r:
            trend_gran = st.radio(
                "추이 단위",
                ["연도별", "월별"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"trend_gran_{household_type}",
            )

        trend_src = df_hh_all_years.copy()
        if highlight_gu != "전체 (강조 안 함)":
            trend_src = trend_src[trend_src["자치구명"] == highlight_gu]
            st.caption(f"※ 강조 자치구 **{highlight_gu}** 기준 시계열 추이입니다.")
        else:
            st.caption("※ 서울 전체 기준 시계열 추이입니다. (2025년은 부분 집계 기간)")

        if trend_gran == "연도별":
            tr_df = aggregate_metrics(trend_src, ["연도"], stat_mode=stat_mode)
            tr_df["기간"] = tr_df["연도"].astype(str) + "년"
        else:
            tr_df = aggregate_metrics(trend_src, ["연도", "월"], stat_mode=stat_mode)
            # Exclude sparse months (<30 tx, e.g. 2025-03 partial file) to prevent visual distortion
            tr_df = tr_df[tr_df["건수"] >= 30].copy()
            tr_df = tr_df.sort_values(["연도", "월"])
            tr_df["기간"] = tr_df["연도"].astype(str) + "-" + tr_df["월"].astype(str).str.zfill(2)

        fig_tr = build_trend_chart(
            tr_df,
            x_col="기간",
            metric_col=metric_col,
            metric_label=short_label,
            unit=unit,
            accent_color=info["color"],
            height=350,
        )
        st.plotly_chart(fig_tr, use_container_width=True)

    with col_bd:
        st.markdown(f'<div class="section-title">🏢 건물용도별 {short_label} 및 거래 비중</div>', unsafe_allow_html=True)
        bldg_src = df_filt if highlight_gu == "전체 (강조 안 함)" else df_filt[df_filt["자치구명"] == highlight_gu]
        st.caption(f"※ {'서울 전체' if highlight_gu == '전체 (강조 안 함)' else highlight_gu} 기준 건물유형 비교")
        bldg_df = aggregate_metrics(bldg_src, ["건물용도"], stat_mode=stat_mode)
        fig_bd = build_building_type_chart(bldg_df, metric_col, short_label, unit, height=350)
        st.plotly_chart(fig_bd, use_container_width=True)

    st.markdown("---")

    # Third Row: Deep-Dive Tabs (Dong Ranking / Deposit-Rent Scatter / Data Table)
    tab1, tab2, tab3 = st.tabs(["📍 법정동별 TOP 순위", "💸 보증금-월세 구조 (산점도)", "📋 자치구별 상세 데이터표"])

    with tab1:
        dong_all = load_summary_dong()
        dong_filt = dong_all[
            (dong_all["가구유형"] == household_type)
            & (dong_all["연도"].isin(selected_years))
            & (dong_all["건물용도"].isin(selected_buildings))
        ].copy()

        d_c1, d_c2 = st.columns([1.0, 1.0])
        with d_c1:
            dong_gu_opt = ["서울 전체"] + sorted(dong_filt["자치구명"].dropna().unique().tolist())
            default_idx = dong_gu_opt.index(highlight_gu) if highlight_gu in dong_gu_opt else 0
            sel_dong_gu = st.selectbox("법정동 조회 범위", dong_gu_opt, index=default_idx, key=f"dong_gu_{household_type}")
        with d_c2:
            rank_dir = st.radio("정렬 기준", ["상위 (고가 TOP 12)", "하위 (저가 TOP 12)"], horizontal=True, key=f"dong_dir_{household_type}")

        if sel_dong_gu != "서울 전체":
            dong_filt = dong_filt[dong_filt["자치구명"] == sel_dong_gu]

        dong_agg = aggregate_metrics(dong_filt, ["자치구명", "법정동명"], stat_mode=stat_mode)
        st.caption("※ 거래 건수 15건 이상인 법정동만 집계하여 소수 이상치에 의한 왜곡을 방지했습니다.")
        fig_dong = build_dong_ranking_chart(
            dong_agg,
            metric_col=metric_col,
            metric_label=short_label,
            unit=unit,
            accent_color=info["color"],
            top_n=12,
            ascending=rank_dir.startswith("하위"),
            height=400,
        )
        st.plotly_chart(fig_dong, use_container_width=True)

    with tab2:
        sample_all = load_scatter_sample()
        sample_filt = sample_all[
            (sample_all["가구유형"] == household_type)
            & (sample_all["연도"].isin(selected_years))
            & (sample_all["건물용도"].isin(selected_buildings))
        ].copy()
        if highlight_gu != "전체 (강조 안 함)":
            sample_filt = sample_filt[sample_filt["자치구명"] == highlight_gu]
        st.caption(
            "보증금이 높을수록 명목 월세가 낮아지는 반전세 트레이드오프 구조를 건물용도별로 확인할 수 있습니다. "
            "(시각화 성능을 위해 층화 표본을 표시합니다.)"
        )
        fig_sc = build_deposit_rent_scatter(sample_filt, height=400)
        st.plotly_chart(fig_sc, use_container_width=True)

    with tab3:
        tbl = gu_df[["자치구명", "월세", "환산월세", "평당월세", "보증금", "평균면적", "건수"]].copy()
        tbl = tbl.sort_values(metric_col, ascending=False).reset_index(drop=True)
        tbl.index = tbl.index + 1
        tbl.columns = [
            "자치구명",
            f"월세 {stat_mode}(만원)",
            f"환산월세 {stat_mode}(만원)",
            f"평당월세 {stat_mode}(만원)",
            f"보증금 {stat_mode}(만원)",
            "평균면적(㎡)",
            "거래건수(건)",
        ]
        st.dataframe(tbl, use_container_width=True)
        csv_bytes = tbl.to_csv(index_label="순위", encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label=f"📥 {household_type} 자치구별 통계 CSV 다운로드",
            data=csv_bytes,
            file_name=f"seoul_rent_{household_type}.csv",
            mime="text/csv",
        )
