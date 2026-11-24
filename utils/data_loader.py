import json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SEOUL_GU_COORDS = {
    "강남구": (37.4967, 127.0630),
    "강동구": (37.5492, 127.1465),
    "강북구": (37.6396, 127.0257),
    "강서구": (37.5612, 126.8228),
    "관악구": (37.4654, 126.9438),
    "광진구": (37.5481, 127.0857),
    "구로구": (37.4954, 126.8581),
    "금천구": (37.4601, 126.9001),
    "노원구": (37.6525, 127.0750),
    "도봉구": (37.6688, 127.0318),
    "동대문구": (37.5838, 127.0507),
    "동작구": (37.4989, 126.9516),
    "마포구": (37.5593, 126.9083),
    "서대문구": (37.5778, 126.9390),
    "서초구": (37.4733, 127.0312),
    "성동구": (37.5507, 127.0409),
    "성북구": (37.6023, 127.0252),
    "송파구": (37.5048, 127.1145),
    "양천구": (37.5271, 126.8561),
    "영등포구": (37.5206, 126.9139),
    "용산구": (37.5311, 126.9811),
    "은평구": (37.6176, 126.9227),
    "종로구": (37.5949, 126.9773),
    "중구": (37.5579, 126.9941),
    "중랑구": (37.5980, 127.0927),
}

HOUSEHOLD_ORDER = ["1인가구", "2인가구", "3인가구", "4인가구"]

HOUSEHOLD_INFO = {
    "1인가구": {
        "icon": "👤",
        "title": "1인가구 월세 분석",
        "area_label": "전용면적 33㎡ 이하 (약 10평 이하)",
        "typical": "원룸 · 오피스텔 · 소형 다세대",
        "gradient": "linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%)",
        "color": "#2563EB",
        "colorscale": "YlOrRd",
        "desc": "사회초년생·대학생 중심의 원룸 및 소형 오피스텔 시장으로, 보증금 부담이 낮은 순수 월세 비중이 높습니다.",
    },
    "2인가구": {
        "icon": "👥",
        "title": "2인가구 월세 분석",
        "area_label": "전용면적 33㎡ 초과 ~ 50㎡ 이하 (약 10~15평)",
        "typical": "투룸 · 소형 아파트 · 빌라",
        "gradient": "linear-gradient(135deg, #065F46 0%, #059669 60%, #10B981 100%)",
        "color": "#059669",
        "colorscale": "YlOrRd",
        "desc": "신혼부부·직장인 2인가구 수요가 집중된 투룸 및 소형 아파트 구간으로, 보증금이 1인가구 대비 크게 높아집니다.",
    },
    "3인가구": {
        "icon": "👨‍👩‍👦",
        "title": "3인가구 월세 분석",
        "area_label": "전용면적 50㎡ 초과 ~ 75㎡ 이하 (약 15~23평)",
        "typical": "중소형 아파트(59㎡) · 쓰리룸",
        "gradient": "linear-gradient(135deg, #9A3412 0%, #D97706 60%, #F59E0B 100%)",
        "color": "#D97706",
        "colorscale": "YlOrRd",
        "desc": "전용 59㎡ 중소형 아파트가 핵심인 구간으로, 보증금 1억 원 이상의 반전세 계약 비중이 두드러집니다.",
    },
    "4인가구": {
        "icon": "👨‍👩‍👧‍👦",
        "title": "4인가구 월세 분석",
        "area_label": "전용면적 75㎡ 초과 (약 23평 초과, 국민평형 84㎡ 포함)",
        "typical": "중대형 아파트(84㎡+) · 단독주택",
        "gradient": "linear-gradient(135deg, #7C2D12 0%, #BE123C 55%, #E11D48 100%)",
        "color": "#E11D48",
        "colorscale": "YlOrRd",
        "desc": "국민평형(84㎡) 이상 중대형 주거 시장으로, 강남·서초·용산 등 핵심 학군·업무지와의 자치구 격차가 가장 큽니다.",
    },
}

METRIC_OPTIONS = {
    "월세(만원)": {"prefix": "월세", "unit": "만원", "short": "월세"},
    "환산월세(만원, 보증금 5% 환산)": {"prefix": "환산월세", "unit": "만원", "short": "환산월세"},
    "3.3㎡(평)당 월세(만원)": {"prefix": "평당월세", "unit": "만원/평", "short": "평당월세"},
    "보증금(만원)": {"prefix": "보증금", "unit": "만원", "short": "보증금"},
}

BUILDING_TYPES = ["아파트", "오피스텔", "연립다세대", "단독다가구"]


@st.cache_data(show_spinner=False)
def load_summary_gu_ym() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "rent_summary_gu_ym.csv.gz", compression="gzip")
    return df


@st.cache_data(show_spinner=False)
def load_summary_dong() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "rent_summary_dong.csv.gz", compression="gzip")
    return df


@st.cache_data(show_spinner=False)
def load_scatter_sample() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "rent_sample_scatter.csv.gz", compression="gzip")
    return df


@st.cache_data(show_spinner=False)
def load_metadata() -> dict:
    with open(DATA_DIR / "data_metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=86400, show_spinner=False)
def load_seoul_geojson():
    urls = [
        "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json",
        "https://raw.githubusercontent.com/southkorea/seoul-maps/master/juso/2015/json/seoul_municipalities_geo_simple.json",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                geo = resp.json()
                if "features" in geo and len(geo["features"]) >= 25:
                    return geo
        except Exception:
            continue
    return None


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) == 0:
        return np.nan
    sorter = np.argsort(values)
    v = values[sorter]
    w = weights[sorter]
    cum_w = np.cumsum(w)
    cutoff = cum_w[-1] / 2.0
    idx = np.searchsorted(cum_w, cutoff)
    return float(v[min(idx, len(v) - 1)])


def aggregate_metrics(df: pd.DataFrame, group_cols: list, stat_mode: str = "중앙값") -> pd.DataFrame:
    """Aggregate pre-grouped dataframe using exact weighted mean or count-weighted median."""
    if df.empty:
        return pd.DataFrame()

    records = []
    if not group_cols:
        groups = [(None, df)]
    else:
        groups = df.groupby(group_cols, observed=True)

    for key, g in groups:
        cnt = int(g["건수"].sum())
        if cnt == 0:
            continue
        w = g["건수"].to_numpy(dtype=float)
        row = {}
        if group_cols:
            if isinstance(key, tuple):
                for col, val in zip(group_cols, key):
                    row[col] = val
            else:
                row[group_cols[0]] = key

        row["건수"] = cnt
        row["평균면적"] = round(float(g["면적_합계"].sum()) / cnt, 1)

        for prefix in ["월세", "환산월세", "평당월세", "보증금"]:
            mean_val = float(g[f"{prefix}_합계"].sum()) / cnt
            med_val = weighted_median(g[f"{prefix}_중앙값"].to_numpy(dtype=float), w)
            row[f"{prefix}_평균"] = round(mean_val, 1)
            row[f"{prefix}_중앙값"] = round(med_val, 1)
            row[prefix] = round(med_val if stat_mode == "중앙값" else mean_val, 1)

        records.append(row)

    res = pd.DataFrame(records)
    if "자치구명" in res.columns:
        res["lat"] = res["자치구명"].map(lambda x: SEOUL_GU_COORDS.get(x, (37.5665, 126.9780))[0])
        res["lon"] = res["자치구명"].map(lambda x: SEOUL_GU_COORDS.get(x, (37.5665, 126.9780))[1])
    return res
