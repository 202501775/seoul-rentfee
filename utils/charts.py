import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

FONT_FAMILY = "Pretendard, -apple-system, BlinkMacSystemFont, Malgun Gothic, sans-serif"

BUILDING_COLORS = {
    "아파트": "#2563EB",
    "오피스텔": "#059669",
    "연립다세대": "#D97706",
    "단독다가구": "#E11D48",
}

HOUSEHOLD_COLORS = {
    "1인가구": "#2563EB",
    "2인가구": "#059669",
    "3인가구": "#D97706",
    "4인가구": "#E11D48",
}


def apply_base_layout(fig: go.Figure, height: int = 420, margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        font=dict(family=FONT_FAMILY, color="#0F172A", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=margin or dict(l=16, r=16, t=36, b=16),
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=12,
            font_family=FONT_FAMILY,
            font_color="#FFFFFF",
        ),
    )
    return fig


def build_seoul_map_heatmap(
    gu_df: pd.DataFrame,
    geojson: dict | None,
    metric_col: str,
    metric_label: str,
    unit: str,
    map_mode: str = "자치구 경계 히트맵 (Choropleth)",
    colorscale: str = "YlOrRd",
    highlight_gu: str | None = None,
    height: int = 530,
) -> go.Figure:
    """Render an interactive Seoul map heatmap (Choropleth or Density Heatmap)."""
    df = gu_df.copy()
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="선택한 조건에 해당하는 데이터가 없습니다.", showarrow=False)
        return apply_base_layout(fig, height=height)

    df["hover_text"] = df.apply(
        lambda r: (
            f"<b>{r['자치구명']}</b><br>"
            f"{metric_label}: <b>{r[metric_col]:,.1f} {unit}</b><br>"
            f"명목 월세: {r['월세']:,.1f} 만원<br>"
            f"환산 월세: {r['환산월세']:,.1f} 만원<br>"
            f"보증금: {r['보증금']:,.0f} 만원<br>"
            f"평균 면적: {r['평균면적']:.1f} ㎡<br>"
            f"거래 건수: {int(r['건수']):,}건"
        ),
        axis=1,
    )

    has_maplibre = hasattr(go, "Choroplethmap")
    ChoroTrace = go.Choroplethmap if has_maplibre else go.Choroplethmapbox
    DensityTrace = go.Densitymap if has_maplibre else go.Densitymapbox
    ScatterTrace = go.Scattermap if has_maplibre else go.Scattermapbox
    layout_map_key = "map" if has_maplibre else "mapbox"

    use_choropleth = (map_mode.startswith("자치구 경계")) and (geojson is not None)

    if use_choropleth:
        fig = go.Figure(
            ChoroTrace(
                geojson=geojson,
                locations=df["자치구명"],
                featureidkey="properties.name",
                z=df[metric_col],
                colorscale=colorscale,
                marker_opacity=0.82,
                marker_line_width=1.2,
                marker_line_color="#FFFFFF",
                text=df["hover_text"],
                hovertemplate="%{text}<extra></extra>",
                colorbar=dict(
                    title=dict(text=f"{metric_label}<br>({unit})", font=dict(size=11)),
                    thickness=14,
                    len=0.72,
                    x=0.98,
                    bgcolor="rgba(255,255,255,0.88)",
                    outlinewidth=0,
                ),
            )
        )

        # District name labels on map
        fig.add_trace(
            ScatterTrace(
                lat=df["lat"],
                lon=df["lon"],
                mode="text",
                text=df["자치구명"].str.replace("구$", "", regex=True),
                textfont=dict(size=10, color="#0F172A"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    else:
        # Continuous density heatmap over Seoul map
        fig = go.Figure(
            DensityTrace(
                lat=df["lat"],
                lon=df["lon"],
                z=df[metric_col],
                radius=46,
                colorscale=colorscale,
                opacity=0.80,
                hoverinfo="skip",
                colorbar=dict(
                    title=dict(text=f"{metric_label}<br>({unit})", font=dict(size=11)),
                    thickness=14,
                    len=0.72,
                    x=0.98,
                    bgcolor="rgba(255,255,255,0.88)",
                    outlinewidth=0,
                ),
            )
        )
        fig.add_trace(
            ScatterTrace(
                lat=df["lat"],
                lon=df["lon"],
                mode="markers+text",
                marker=dict(size=9, color="#0F172A", opacity=0.75),
                text=df["자치구명"].str.replace("구$", "", regex=True),
                textposition="top center",
                textfont=dict(size=10, color="#0F172A"),
                customdata=df["hover_text"],
                hovertemplate="%{customdata}<extra></extra>",
                showlegend=False,
            )
        )

    # Highlight selected district if any
    if highlight_gu and highlight_gu != "전체 (강조 안 함)":
        sub = df[df["자치구명"] == highlight_gu]
        if not sub.empty:
            fig.add_trace(
                ScatterTrace(
                    lat=sub["lat"],
                    lon=sub["lon"],
                    mode="markers+text",
                    marker=dict(size=16, color="#1D4ED8", opacity=0.95),
                    text=[f"★ {highlight_gu} ({sub.iloc[0][metric_col]:,.1f}{unit})"],
                    textposition="top center",
                    textfont=dict(size=12, color="#1E3A8A"),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    fig.update_layout(
        **{
            layout_map_key: dict(
                style="carto-positron",
                center=dict(lat=37.5642, lon=126.9890),
                zoom=10.15,
            )
        },
        margin=dict(l=0, r=0, t=8, b=0),
        height=height,
    )
    return apply_base_layout(fig, height=height, margin=dict(l=0, r=0, t=8, b=0))


def build_gu_ranking_bar(
    gu_df: pd.DataFrame,
    metric_col: str,
    metric_label: str,
    unit: str,
    accent_color: str = "#2563EB",
    highlight_gu: str | None = None,
    height: int = 530,
) -> go.Figure:
    df = gu_df.sort_values(metric_col, ascending=True).copy()
    if df.empty:
        return apply_base_layout(go.Figure(), height=height)

    seoul_avg = float(np.average(df[metric_col], weights=df["건수"]))

    colors = []
    for gu in df["자치구명"]:
        if highlight_gu and gu == highlight_gu:
            colors.append("#0F172A")
        else:
            colors.append(accent_color)

    fig = go.Figure(
        go.Bar(
            x=df[metric_col],
            y=df["자치구명"],
            orientation="h",
            marker=dict(
                color=df[metric_col] if not (highlight_gu and highlight_gu != "전체 (강조 안 함)") else colors,
                colorscale="YlOrRd" if not (highlight_gu and highlight_gu != "전체 (강조 안 함)") else None,
                line=dict(width=0),
            ),
            text=df[metric_col].map(lambda v: f"{v:,.1f}"),
            textposition="outside",
            textfont=dict(size=10, color="#334155"),
            customdata=np.stack([df["건수"], df["보증금"], df["환산월세"]], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"{metric_label}: <b>%{{x:,.1f}} {unit}</b><br>"
                "환산월세: %{customdata[2]:,.1f} 만원<br>"
                "보증금: %{customdata[1]:,.0f} 만원<br>"
                "거래건수: %{customdata[0]:,.0f}건<extra></extra>"
            ),
        )
    )

    fig.add_vline(
        x=seoul_avg,
        line_dash="dot",
        line_color="#475569",
        line_width=1.5,
        annotation_text=f"서울 전체 {seoul_avg:,.1f}",
        annotation_position="top",
        annotation_font=dict(size=11, color="#334155"),
    )

    max_val = float(df[metric_col].max())
    fig.update_xaxes(
        title_text=f"{metric_label} ({unit})",
        range=[0, max_val * 1.18],
        gridcolor="#F1F5F9",
        zeroline=False,
    )
    fig.update_yaxes(title_text="", tickfont=dict(size=11))
    return apply_base_layout(fig, height=height, margin=dict(l=8, r=24, t=28, b=36))


def build_trend_chart(
    trend_df: pd.DataFrame,
    x_col: str,
    metric_col: str,
    metric_label: str,
    unit: str,
    accent_color: str = "#2563EB",
    color_col: str | None = None,
    height: int = 360,
) -> go.Figure:
    if trend_df.empty:
        return apply_base_layout(go.Figure(), height=height)

    df = trend_df.sort_values(x_col).copy()

    if color_col:
        fig = px.line(
            df,
            x=x_col,
            y=metric_col,
            color=color_col,
            markers=True,
            color_discrete_map=HOUSEHOLD_COLORS,
            custom_data=["건수"],
        )
        fig.update_traces(
            line=dict(width=2.8),
            marker=dict(size=7),
            hovertemplate=(
                "<b>%{fullData.name}</b> (%{x})<br>"
                f"{metric_label}: <b>%{{y:,.1f}} {unit}</b><br>"
                "거래건수: %{customdata[0]:,}건<extra></extra>"
            ),
        )
    else:
        fig = go.Figure(
            go.Scatter(
                x=df[x_col],
                y=df[metric_col],
                mode="lines+markers+text" if len(df) <= 8 else "lines+markers",
                text=df[metric_col].map(lambda v: f"{v:,.1f}") if len(df) <= 8 else None,
                textposition="top center",
                textfont=dict(size=11, color="#1E293B"),
                line=dict(color=accent_color, width=3),
                marker=dict(size=7, color=accent_color, line=dict(width=1.5, color="#FFFFFF")),
                fill="tozeroy",
                fillcolor="rgba(37, 99, 235, 0.08)",
                customdata=df["건수"],
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{metric_label}: <b>%{{y:,.1f}} {unit}</b><br>"
                    "거래건수: %{customdata:,}건<extra></extra>"
                ),
            )
        )

    fig.update_xaxes(title_text="", type="category", gridcolor="#F1F5F9")
    fig.update_yaxes(title_text=f"{metric_label} ({unit})", gridcolor="#F1F5F9", rangemode="tozero")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""))
    return apply_base_layout(fig, height=height, margin=dict(l=16, r=16, t=34, b=28))


def build_building_type_chart(
    bldg_df: pd.DataFrame,
    metric_col: str,
    metric_label: str,
    unit: str,
    height: int = 360,
) -> go.Figure:
    if bldg_df.empty:
        return apply_base_layout(go.Figure(), height=height)

    df = bldg_df.sort_values(metric_col, ascending=False).copy()
    total_cnt = df["건수"].sum()
    df["비중"] = (df["건수"] / total_cnt * 100).round(1)

    fig = go.Figure(
        go.Bar(
            x=df["건물용도"],
            y=df[metric_col],
            marker_color=[BUILDING_COLORS.get(b, "#2563EB") for b in df["건물용도"]],
            text=df.apply(lambda r: f"{r[metric_col]:,.1f}{unit}<br>({r['비중']:.1f}%)", axis=1),
            textposition="outside",
            textfont=dict(size=11, color="#1E293B"),
            customdata=np.stack([df["건수"], df["보증금"], df["평균면적"]], axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{metric_label}: <b>%{{y:,.1f}} {unit}</b><br>"
                "보증금: %{customdata[1]:,.0f} 만원<br>"
                "평균 면적: %{customdata[2]:.1f} ㎡<br>"
                "거래건수: %{customdata[0]:,.0f}건<extra></extra>"
            ),
        )
    )
    max_v = float(df[metric_col].max())
    fig.update_yaxes(title_text=f"{metric_label} ({unit})", range=[0, max_v * 1.25], gridcolor="#F1F5F9")
    fig.update_xaxes(title_text="")
    return apply_base_layout(fig, height=height, margin=dict(l=16, r=16, t=28, b=28))


def build_dong_ranking_chart(
    dong_df: pd.DataFrame,
    metric_col: str,
    metric_label: str,
    unit: str,
    accent_color: str = "#2563EB",
    top_n: int = 12,
    ascending: bool = False,
    height: int = 380,
) -> go.Figure:
    if dong_df.empty:
        return apply_base_layout(go.Figure(), height=height)

    # Minimum transaction filter to avoid 1-row outliers
    filtered = dong_df[dong_df["건수"] >= 15].copy()
    if filtered.empty:
        filtered = dong_df.copy()

    filtered["표시명"] = filtered["자치구명"] + " " + filtered["법정동명"]
    sub = filtered.sort_values(metric_col, ascending=ascending).head(top_n)
    sub = sub.sort_values(metric_col, ascending=not ascending)

    fig = go.Figure(
        go.Bar(
            x=sub[metric_col],
            y=sub["표시명"],
            orientation="h",
            marker_color=accent_color,
            text=sub[metric_col].map(lambda v: f"{v:,.1f}"),
            textposition="outside",
            textfont=dict(size=10, color="#334155"),
            customdata=np.stack([sub["건수"], sub["보증금"]], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"{metric_label}: <b>%{{x:,.1f}} {unit}</b><br>"
                "보증금: %{customdata[1]:,.0f} 만원<br>"
                "거래건수: %{customdata[0]:,.0f}건<extra></extra>"
            ),
        )
    )
    max_v = float(sub[metric_col].max())
    fig.update_xaxes(title_text=f"{metric_label} ({unit})", range=[0, max_v * 1.18], gridcolor="#F1F5F9")
    fig.update_yaxes(title_text="", tickfont=dict(size=11))
    return apply_base_layout(fig, height=height, margin=dict(l=8, r=24, t=24, b=32))


def build_deposit_rent_scatter(
    sample_df: pd.DataFrame,
    height: int = 380,
) -> go.Figure:
    if sample_df.empty:
        return apply_base_layout(go.Figure(), height=height)

    # Cap extreme 99th percentile for clean visualization
    p99_dep = sample_df["보증금"].quantile(0.985)
    p99_rent = sample_df["월세"].quantile(0.985)
    df = sample_df[(sample_df["보증금"] <= p99_dep) & (sample_df["월세"] <= p99_rent)].copy()
    if len(df) > 2500:
        df = df.sample(2500, random_state=42)

    fig = px.scatter(
        df,
        x="보증금",
        y="월세",
        color="건물용도",
        color_discrete_map=BUILDING_COLORS,
        opacity=0.55,
        hover_data={
            "자치구명": True,
            "임대면적": ":.1f",
            "보증금": ":,.0f",
            "월세": ":,.0f",
            "환산월세": ":.1f",
            "건물용도": True,
        },
    )
    fig.update_traces(marker=dict(size=6))
    fig.update_xaxes(title_text="보증금 (만원)", gridcolor="#F1F5F9")
    fig.update_yaxes(title_text="월세 (만원)", gridcolor="#F1F5F9")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""))
    return apply_base_layout(fig, height=height, margin=dict(l=16, r=16, t=34, b=36))


def build_overview_matrix_heatmap(
    matrix_df: pd.DataFrame,
    metric_col: str,
    metric_label: str,
    unit: str,
    height: int = 680,
) -> go.Figure:
    if matrix_df.empty:
        return apply_base_layout(go.Figure(), height=height)

    piv = matrix_df.pivot(index="자치구명", columns="가구유형", values=metric_col)
    cols = [c for c in ["1인가구", "2인가구", "3인가구", "4인가구"] if c in piv.columns]
    piv = piv[cols]
    piv["avg_sort"] = piv.mean(axis=1)
    piv = piv.sort_values("avg_sort", ascending=True).drop(columns=["avg_sort"])

    fig = go.Figure(
        go.Heatmap(
            z=piv.values,
            x=piv.columns.tolist(),
            y=piv.index.tolist(),
            colorscale="YlOrRd",
            text=np.where(np.isnan(piv.values), "-", np.vectorize(lambda v: f"{v:,.1f}")(piv.values)),
            texttemplate="%{text}",
            textfont=dict(size=11),
            hovertemplate=(
                "<b>%{y} · %{x}</b><br>"
                f"{metric_label}: <b>%{{z:,.1f}} {unit}</b><extra></extra>"
            ),
            colorbar=dict(title=f"{unit}", thickness=14),
        )
    )
    fig.update_xaxes(side="top", tickfont=dict(size=12, color="#0F172A"))
    fig.update_yaxes(tickfont=dict(size=11))
    return apply_base_layout(fig, height=height, margin=dict(l=16, r=16, t=40, b=16))
