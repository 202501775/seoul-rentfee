import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.charts import apply_base_layout
from utils.data_loader import load_metadata


def render_methodology():
    meta = load_metadata()

    st.markdown(
        """
        <div class="hero-banner" style="background: linear-gradient(135deg, #334155 0%, #475569 60%, #64748B 100%);">
            <div class="hero-badge">데이터 출처 · 전처리 · 집계 기준 · 분석의 한계</div>
            <div class="hero-title">📋 데이터 출처 및 분석 방법론</div>
            <div class="hero-subtitle">
                공공데이터 기반의 투명한 집계 기준과 해석 시 유의해야 할 한계점을 정리했습니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("원본 CSV 전체 행 수", f"{meta['raw_total_rows']:,}건", "2021~2025년 전월세")
    with c2:
        st.metric("월세 추출 행 수", f"{meta['raw_wolse_rows']:,}건", "전월세구분 = 월세")
    with c3:
        st.metric("최종 분석 유효 데이터", f"{meta['cleaned_wolse_rows']:,}건", "이상치·결측치 정제 완료")

    st.markdown("---")

    col_a, col_b = st.columns([1.1, 1.0])
    with col_a:
        st.markdown("### 1. 데이터 출처 및 전처리 기준")
        st.markdown(
            """
            * **원본 출처**: 서울 열린데이터광장 · 국토교통부 실거래가 공개시스템 「서울특별시 부동산 전월세가 정보 (2021~2025)」
            * **대상 건물유형**: 아파트, 오피스텔, 연립다세대, 단독다가구 (서울시 25개 자치구 전체)
            * **정제 규칙**:
              1. `전월세구분 == "월세"` 계약만 추출 (전세 제외)
              2. 계약일 기준 2021~2025년 정상 계약일자 필터링
              3. 극단적 오기입·상업용 이상치 제외 (`월세` 1~3,000만원, `임대면적` 10~300㎡, `보증금` 0~50억 원)
              4. 웹 배포(Streamlit Cloud) 속도와 메모리 최적화를 위해 자치구·연월·가구유형·건물용도별로 사전 집계(gzip 압축)
            """
        )

        st.markdown("### 2. 가구유형 면적 분류 기준")
        hh_table = pd.DataFrame(
            [
                {"가구유형": "1인가구", "전용면적 구간": "33㎡ 이하 (약 10평 이하)", "대표 주거 형태": "원룸, 소형 오피스텔, 다세대", "분석 건수": f"{meta['household_counts'].get('1인가구', 0):,}건"},
                {"가구유형": "2인가구", "전용면적 구간": "33㎡ 초과 ~ 50㎡ 이하 (10~15평)", "대표 주거 형태": "투룸, 소형 아파트, 빌라", "분석 건수": f"{meta['household_counts'].get('2인가구', 0):,}건"},
                {"가구유형": "3인가구", "전용면적 구간": "50㎡ 초과 ~ 75㎡ 이하 (15~23평)", "대표 주거 형태": "중소형 아파트(59㎡), 쓰리룸", "분석 건수": f"{meta['household_counts'].get('3인가구', 0):,}건"},
                {"가구유형": "4인가구", "전용면적 구간": "75㎡ 초과 (23평 초과, 84㎡ 포함)", "대표 주거 형태": "국민평형(84㎡+) 중대형 아파트", "분석 건수": f"{meta['household_counts'].get('4인가구', 0):,}건"},
            ]
        )
        st.dataframe(hh_table, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("### 3. 주요 지표 정의")
        st.markdown(
            """
            * **명목 월세 (만원)**: 계약서상 매월 납부하는 순수 임대료
            * **환산월세 (만원)**: 보증금 규모 차이를 보정하기 위해 연 5% 전월세전환율을 적용한 실질 월 주거비용
              $$\text{환산월세} = \text{월세} + \frac{\text{보증금} \times 0.05}{12}$$
            * **3.3㎡(평)당 월세 (만원/평)**: 면적 차이를 보정한 단위 면적당 임대료
            * **중앙값 vs 평균**: 고가 주택의 영향(오른쪽 꼬리 분포)을 줄이기 위해 **중앙값(Median)**을 기본값으로 제공하며, 사이드바에서 평균과 전환 비교할 수 있습니다.
            """
        )

        st.markdown("### 4. 2025년 부분 수집 현황 및 분석의 한계")
        m25 = meta.get("month_2025_counts", {})
        months = list(range(1, 13))
        counts = [m25.get(str(m), 0) for m in months]
        colors = ["#2563EB" if c >= 1000 else "#CBD5E1" for c in counts]
        fig_m25 = go.Figure(
            go.Bar(
                x=[f"{m}월" for m in months],
                y=counts,
                marker_color=colors,
                text=[f"{c:,}" if c > 0 else "미수집" for c in counts],
                textposition="outside",
                textfont=dict(size=10),
            )
        )
        fig_m25.update_yaxes(title_text="거래 건수 (건)", gridcolor="#F1F5F9", range=[0, max(counts) * 1.2])
        fig_m25.update_xaxes(title_text="2025년 계약월")
        st.plotly_chart(apply_base_layout(fig_m25, height=260), use_container_width=True)

        st.warning(
            "**해석 시 유의사항 (데이터의 한계)**\n"
            "1. **2025년 부분 집계**: 제공된 2025년 분할 CSV(`part03, 04, 05, 07, 08`)에는 3월(8건)과 9~12월 데이터가 누락되어 있어, 2025년 거래량은 연간 총량이 아닌 부분 집계치입니다.\n"
            "2. **전용면적 기반 대리 변수**: 실거래가 데이터에는 실제 거주 인원수가 기록되지 않으므로, 전용면적 구간을 1~4인가구의 대리 변수(Proxy)로 사용했습니다.\n"
            "3. **관리비·입지 세부 요인 미반영**: 관리비, 역세권 여부, 리모델링 상태 등은 원천 데이터에 포함되지 않아 가격 차이에 일부 반영되지 않을 수 있습니다."
        )
