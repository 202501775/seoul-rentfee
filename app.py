import streamlit as st

from utils.data_loader import BUILDING_TYPES, METRIC_OPTIONS, load_metadata
from utils.styles import inject_custom_css
from views.household_page import render_household_page
from views.methodology import render_methodology
from views.overview import render_overview

st.set_page_config(
    page_title="서울 월세 가격 비교 대시보드 (1~4인가구)",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()

PAGES = [
    "📊 종합 비교 (전체 가구)",
    "👤 1인가구 (~33㎡)",
    "👥 2인가구 (33~50㎡)",
    "👨‍👩‍👦 3인가구 (50~75㎡)",
    "👨‍👩‍👧‍👦 4인가구 (75㎡ 초과)",
    "📋 데이터 출처 및 기준",
]

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.4rem 0 0.75rem 0;">
            <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">
                🏠 서울 월세 히트맵
            </div>
            <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.15rem;">
                2021~2025 서울시 전월세 실거래가
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "페이지 이동",
        PAGES,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("##### 🎛️ 분석 조건 필터")

    year_range = st.select_slider(
        "분석 연도 범위",
        options=[2021, 2022, 2023, 2024, 2025],
        value=(2024, 2025),
    )
    selected_years = list(range(year_range[0], year_range[1] + 1))

    selected_buildings = st.multiselect(
        "건물 용도",
        options=BUILDING_TYPES,
        default=BUILDING_TYPES,
    )
    if not selected_buildings:
        st.warning("최소 1개 이상의 건물 용도를 선택해 주세요.")
        selected_buildings = BUILDING_TYPES

    metric_label = st.selectbox(
        "비교 가격 지표",
        options=list(METRIC_OPTIONS.keys()),
        index=0,
        help="보증금 차이가 큰 2~4인가구 비교 시 '환산월세'를 함께 확인하면 정확합니다.",
    )

    stat_mode = st.radio(
        "집계 통계 기준",
        options=["중앙값", "평균"],
        index=0,
        horizontal=True,
        help="이상치 영향을 줄이려면 '중앙값'을 권장합니다.",
    )

    st.markdown("---")
    meta = load_metadata()
    st.caption(
        f"• 데이터 출처: 서울 열린데이터광장\n"
        f"• 분석 대상: 월세 {meta['cleaned_wolse_rows']:,}건\n"
        f"• 선택 기간: {year_range[0]}~{year_range[1]}년"
    )

# Route to selected page
if page == PAGES[0]:
    render_overview(selected_years, selected_buildings, metric_label, stat_mode)
elif page == PAGES[1]:
    render_household_page("1인가구", selected_years, selected_buildings, metric_label, stat_mode)
elif page == PAGES[2]:
    render_household_page("2인가구", selected_years, selected_buildings, metric_label, stat_mode)
elif page == PAGES[3]:
    render_household_page("3인가구", selected_years, selected_buildings, metric_label, stat_mode)
elif page == PAGES[4]:
    render_household_page("4인가구", selected_years, selected_buildings, metric_label, stat_mode)
else:
    render_methodology()
