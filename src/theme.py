"""제주 테마 디자인 (감귤·바다·현무암·유채꽃 색상, 한라산·파도 배너)."""

import plotly.express as px
import plotly.io as pio
import streamlit as st

TANGERINE = "#f5821f"
TANGERINE_DARK = "#d9650a"
SEA = "#1495a8"
SEA_DEEP = "#0b5d6b"
EMERALD = "#3cc3b4"
BASALT = "#3b3a39"
CANOLA = "#f6d23c"
SAND = "#fffaf1"

JEJU_PALETTE = [TANGERINE, SEA, CANOLA, SEA_DEEP, EMERALD, "#8a6f5a", "#e85d75"]

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&display=swap');

.stApp {{
  background:
    radial-gradient(circle at 92% 4%, rgba(246,210,60,.18) 0, transparent 28%),
    linear-gradient(180deg, #fff6e8 0%, {SAND} 35%, #f2fbfa 100%);
}}
h1, h2, h3, [data-testid="stHeading"] h3 {{ font-family: 'Jua', sans-serif !important; color: {BASALT}; letter-spacing: .3px; }}

/* 사이드바: 현무암 돌담 */
[data-testid="stSidebar"] {{
  background:
    radial-gradient(circle at 20% 15%, rgba(255,255,255,.05) 0 6px, transparent 7px),
    radial-gradient(circle at 70% 40%, rgba(255,255,255,.05) 0 4px, transparent 5px),
    radial-gradient(circle at 40% 75%, rgba(255,255,255,.05) 0 5px, transparent 6px),
    linear-gradient(180deg, #45433f 0%, #2f2e2c 100%);
  background-size: 60px 60px, 45px 45px, 70px 70px, 100% 100%;
}}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"],
[data-testid="stSidebar"] [data-testid="stSliderTickBarMin"],
[data-testid="stSidebar"] [data-testid="stSliderTickBarMax"] {{ color: #f4efe6 !important; }}
[data-testid="stSidebar"] h1 {{ color: {TANGERINE} !important; font-size: 1.9rem; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div {{
  background: rgba(255,255,255,.95) !important; border-radius: 12px !important; border: none !important;
}}

/* 헤더 배너 */
.jeju-hero {{
  position: relative; overflow: hidden; border-radius: 22px; padding: 30px 34px 86px;
  background: linear-gradient(180deg, #8fd3e8 0%, #c9ecf2 55%, #fff1d6 100%);
  box-shadow: 0 8px 24px rgba(11,93,107,.15); margin-bottom: 14px;
}}
.jeju-hero h1 {{ font-family: 'Jua', sans-serif; font-size: 2.7rem; margin: 0; color: {SEA_DEEP}; padding: 0; }}
.jeju-hero .sub {{ font-family: 'Gowun Dodum', sans-serif; font-size: 1.1rem; color: {BASALT}; margin-top: 4px; }}
.jeju-hero .cond {{ display:inline-block; margin-top: 14px; background: rgba(255,255,255,.85); padding: 6px 14px;
  border-radius: 999px; font-weight: 700; color: {SEA_DEEP}; }}
.jeju-hero svg {{ position: absolute; left: 0; bottom: 0; width: 100%; height: 120px; }}
.jeju-hero .sun {{ position: absolute; right: 60px; top: 26px; width: 70px; height: 70px; border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #ffd37a, {TANGERINE}); box-shadow: 0 0 40px rgba(245,130,31,.55); }}
.jeju-hero .sun::after {{ content: ''; position: absolute; top: -9px; left: 30px; width: 14px; height: 10px;
  background: #3e9b48; border-radius: 10px 10px 0 10px; transform: rotate(-20deg); }}

/* 지표 카드 */
[data-testid="stMetric"] {{
  background: #ffffff; border-radius: 16px; padding: 14px 18px;
  border-left: 6px solid {TANGERINE}; box-shadow: 0 3px 12px rgba(59,58,57,.08);
}}
[data-testid="stMetricValue"] {{ font-family: 'Jua', sans-serif; color: {SEA_DEEP}; }}

/* 탭 */
[role="tablist"] {{ gap: 6px; }}
[role="tab"] {{ margin-right: 6px; background: rgba(255,255,255,.75); border-radius: 12px 12px 0 0;
  padding: 8px 16px !important; }}
[role="tab"][aria-selected="true"] {{ background: {TANGERINE}; }}
[role="tab"][aria-selected="true"] p {{ color: #fff !important; font-weight: 700; }}

/* 추천 카드 */
.rec-card {{ background: #fff; border-radius: 16px; padding: 14px 16px; height: 100%;
  border-top: 5px solid {SEA}; box-shadow: 0 3px 12px rgba(11,93,107,.10); }}
.rec-card .name {{ font-family: 'Jua', sans-serif; font-size: 1.15rem; color: {SEA_DEEP}; }}
.rec-card .meta {{ color: #6b6660; font-size: .88rem; margin: 2px 0 8px; }}

[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {{
  background: #fff; border-radius: 16px; box-shadow: 0 3px 12px rgba(59,58,57,.06);
}}
</style>
"""

HERO_SVG = f"""
<svg viewBox="0 0 1200 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M0,80 C120,78 220,70 330,52 C430,36 520,14 600,10 C680,14 770,36 870,52 C980,70 1080,78 1200,80 L1200,120 L0,120 Z" fill="#5f8f6a" opacity=".85"/>
  <path d="M560,14 C580,8 620,8 640,14 L628,18 C612,15 590,15 572,18 Z" fill="#ffffff" opacity=".7"/>
  <path d="M0,96 C150,84 300,108 450,96 C600,84 750,108 900,96 C1050,84 1130,100 1200,94 L1200,120 L0,120 Z" fill="{SEA}" />
  <path d="M0,106 C150,96 300,116 450,106 C600,96 750,116 900,106 C1050,96 1130,110 1200,104 L1200,120 L0,120 Z" fill="{SEA_DEEP}" />
</svg>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)
    tpl = pio.templates["plotly_white"]
    tpl.layout.colorway = JEJU_PALETTE
    tpl.layout.font.family = "Gowun Dodum, sans-serif"
    tpl.layout.title.font.family = "Jua, sans-serif"
    tpl.layout.paper_bgcolor = "rgba(0,0,0,0)"
    tpl.layout.plot_bgcolor = "rgba(0,0,0,0)"
    pio.templates.default = "plotly_white"
    px.defaults.template = "plotly_white"
    px.defaults.color_discrete_sequence = JEJU_PALETTE
    px.defaults.color_continuous_scale = ["#fff3d6", CANOLA, TANGERINE, "#c0392b"]


def hero(title: str, subtitle: str, condition: str):
    st.markdown(f"""<div class="jeju-hero"><div class="sun"></div><h1>{title}</h1>
<div class="sub">{subtitle}</div><div class="cond">{condition}</div>{HERO_SVG}</div>""", unsafe_allow_html=True)
