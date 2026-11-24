import streamlit as st


def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

        html, body, [class*="css"] {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1440px;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }

        /* Hero banner */
        .hero-banner {
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.25rem;
            color: #FFFFFF;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12);
        }
        .hero-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(6px);
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            margin-bottom: 0.5rem;
        }
        .hero-title {
            font-size: 1.75rem;
            font-weight: 800;
            margin: 0.15rem 0 0.4rem 0;
            line-height: 1.25;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            font-size: 0.96rem;
            opacity: 0.93;
            margin: 0;
            line-height: 1.5;
        }

        /* KPI Card */
        .kpi-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            height: 100%;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
        }
        .kpi-label {
            font-size: 0.82rem;
            font-weight: 600;
            color: #64748B;
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }
        .kpi-value {
            font-size: 1.65rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }
        .kpi-sub {
            font-size: 0.8rem;
            color: #64748B;
            margin-top: 0.4rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            flex-wrap: wrap;
        }
        .delta-up {
            background: #FEE2E2;
            color: #B91C1C;
            padding: 0.12rem 0.45rem;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.75rem;
        }
        .delta-down {
            background: #DCFCE7;
            color: #15803D;
            padding: 0.12rem 0.45rem;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.75rem;
        }
        .delta-neutral {
            background: #F1F5F9;
            color: #475569;
            padding: 0.12rem 0.45rem;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.75rem;
        }

        /* Insight box */
        .insight-box {
            background: #EFF6FF;
            border-left: 4px solid #2563EB;
            border-radius: 0 12px 12px 0;
            padding: 0.9rem 1.2rem;
            margin: 0.75rem 0 1.25rem 0;
            color: #1E3A8A;
            font-size: 0.92rem;
            line-height: 1.6;
        }
        .insight-box b {
            color: #1E40AF;
        }

        /* Section card header */
        .section-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #0F172A;
            margin: 0.25rem 0 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.45rem;
        }
        .section-caption {
            font-size: 0.83rem;
            color: #64748B;
            margin-bottom: 0.75rem;
        }

        /* Household summary card on overview */
        .hh-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-top: 4px solid #2563EB;
            border-radius: 14px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }
        .hh-card-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #0F172A;
        }
        .hh-card-area {
            font-size: 0.78rem;
            color: #64748B;
            margin-bottom: 0.65rem;
        }
        .hh-card-price {
            font-size: 1.5rem;
            font-weight: 800;
            color: #1E293B;
        }
        .hh-card-meta {
            font-size: 0.8rem;
            color: #475569;
            margin-top: 0.35rem;
            line-height: 1.45;
        }

        /* Clean tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background-color: #F1F5F9;
            padding: 0.3rem;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.45rem 1rem;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, sub_html: str = "", accent_color: str = "#2563EB"):
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top: 3px solid {accent_color};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
