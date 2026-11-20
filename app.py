"""제주 한적로드 — AI 혼잡도 예측 기반 한적한 제주 여행지 추천 (데모)

실행: streamlit run app.py
"""

import datetime as dt
import math

import pandas as pd
import plotly.express as px
import streamlit as st

from src.model import FEATURES, build_features, evaluate, load_data, predict, train_final
from src.spots import CONGESTION_COLORS, CONGESTION_LEVELS, OPEN_HOURS, WEATHERS, spots_df

st.set_page_config(page_title="제주 한적로드", page_icon="🍊", layout="wide")

LEVEL_ORDER = {lv: i for i, lv in enumerate(CONGESTION_LEVELS)}
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


@st.cache_data(show_spinner="샘플 데이터를 불러오는 중...")
def get_data():
    return load_data()


@st.cache_resource(show_spinner="혼잡도 예측 모델을 학습하는 중... (최초 1회, 약 10초)")
def get_model():
    return train_final(get_data())


@st.cache_data(show_spinner="모델 성능을 비교하는 중...")
def get_eval():
    res, best, fitted, (X_te, y_te, cap_te) = evaluate(get_data())
    pred = fitted[best].predict(X_te)
    sample = pd.DataFrame({"실제 방문객": y_te.values, "예측 방문객": pred.round()}).sample(2000, random_state=0)
    return res, best, sample


def haversine(lat1, lon1, lat2, lon2):
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def level_badge(level: str) -> str:
    return f"<span style='background:{CONGESTION_COLORS[level]};color:white;padding:2px 10px;border-radius:12px;font-weight:600'>{level}</span>"


spots = spots_df()
df = get_data()
model = get_model()

# ---------------- 사이드바 ----------------
st.sidebar.title("🍊 제주 한적로드")
st.sidebar.caption("AI 혼잡도 예측 기반 한적한 제주 여행지 추천")
date = st.sidebar.date_input("여행 날짜", value=dt.date.today() + dt.timedelta(days=7),
                             min_value=dt.date(2025, 1, 1), max_value=dt.date(2026, 12, 31))
hour = st.sidebar.select_slider("방문 시간", options=OPEN_HOURS, value=13, format_func=lambda h: f"{h:02d}:00")
weather = st.sidebar.radio("예상 날씨", WEATHERS, horizontal=True)
areas = st.sidebar.multiselect("지역", sorted(spots["area"].unique()), placeholder="전체 지역")
cats = st.sidebar.multiselect("관광지 유형", sorted(spots["category"].unique()), placeholder="전체 유형")
target_spot = st.sidebar.selectbox("가고 싶은 관광지", spots["spot"], index=0)
st.sidebar.divider()
st.sidebar.warning("데모 버전: 모든 수치는 **샘플(합성) 데이터** 기반이며 실제 혼잡도가 아닙니다.", icon="⚠️")

date = pd.Timestamp(date)
pred_all = predict(model, build_features(date, hour, weather, spots))
view = pred_all.copy()
if areas:
    view = view[view["area"].isin(areas)]
if cats:
    view = view[view["category"].isin(cats)]

st.title("🍊 제주 한적로드")
st.markdown(f"**{date:%Y년 %m월 %d일} ({WEEKDAYS[date.weekday()]}) {hour:02d}:00 · {weather}** 기준 예측 결과입니다.")

tab1, tab2, tab3, tab4 = st.tabs(["🔮 혼잡도 예측·추천", "📊 데이터 탐색(EDA)", "🤖 모델 성능", "ℹ️ 데이터 안내"])

# ---------------- 탭1: 예측 & 추천 ----------------
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("분석 관광지", f"{len(view)}곳")
    c2.metric("여유 관광지", f"{(view['congestion'] == '여유').sum()}곳")
    c3.metric("혼잡 예상", f"{view['congestion'].isin(['약간 혼잡', '혼잡']).sum()}곳")
    c4.metric("평균 혼잡률", f"{view['ratio'].mean() * 100:.0f}%")

    # 선택 관광지 상세
    st.subheader(f"📍 {target_spot}")
    me = pred_all[pred_all["spot"] == target_spot].iloc[0]
    st.markdown(f"예상 방문객 **{me.pred_visitors:,}명** / 시간 · 수용력 대비 **{me.ratio * 100:.0f}%** · "
                f"혼잡도 {level_badge(me.congestion)}", unsafe_allow_html=True)

    day_curve = predict(model, build_features(date, OPEN_HOURS, weather, spots[spots["spot"] == target_spot]))
    best_hour = day_curve.loc[day_curve["ratio"].idxmin()]
    left, right = st.columns([3, 2])
    with left:
        fig = px.bar(day_curve, x="hour", y="ratio", color="congestion",
                     color_discrete_map=CONGESTION_COLORS, category_orders={"congestion": CONGESTION_LEVELS},
                     labels={"hour": "시간", "ratio": "혼잡률(수용력 대비)", "congestion": "혼잡도"},
                     title=f"{target_spot} 시간대별 예상 혼잡률")
        fig.add_vline(x=hour, line_dash="dash", line_color="gray")
        fig.update_layout(height=320, yaxis_tickformat=".0%", xaxis_dtick=1, margin=dict(t=50, b=10))
        st.plotly_chart(fig, width="stretch")
    with right:
        st.markdown("#### 💡 추천")
        st.info(f"**{target_spot}**은(는) **{int(best_hour.hour):02d}:00** 무렵이 가장 한산해요 "
                f"(혼잡률 {best_hour.ratio * 100:.0f}%).")
        if LEVEL_ORDER[me.congestion] >= 2:
            st.warning("선택한 시간에는 붐빌 것으로 예상돼요. 아래 대체 여행지를 확인해 보세요.")
        else:
            st.success("선택한 시간에 방문하기 좋아요!")

    # 대체 여행지 추천: 같은 유형 or 가까운 곳 중 혼잡도가 더 낮은 곳
    st.subheader("🌿 한적한 대체 여행지 추천")
    cand = pred_all[pred_all["spot"] != target_spot].copy()
    cand["dist_km"] = cand.apply(lambda r: round(haversine(me.lat, me.lon, r.lat, r.lon), 1), axis=1)
    cand["same_cat"] = cand["category"] == me.category
    cand = cand[cand["ratio"] < me.ratio]
    calm = cand[cand["congestion"].isin(["여유", "보통"])]
    cand = calm if len(calm) >= 3 else cand  # 가능하면 '여유·보통' 관광지만 추천
    if areas:
        cand = cand[cand["area"].isin(areas)]
    if cats:
        cand = cand[cand["category"].isin(cats)]
    # 점수: 혼잡률 낮을수록, 가까울수록, 같은 유형일수록 좋음
    cand["score"] = cand["ratio"] * 1.0 + cand["dist_km"] / 60 - cand["same_cat"] * 0.25
    rec = cand.sort_values("score").head(5)
    if rec.empty:
        st.write("조건에 맞는 더 한적한 관광지가 없어요. 지금 선택이 이미 좋은 선택이에요!")
    else:
        cols = st.columns(len(rec))
        for col, r in zip(cols, rec.itertuples()):
            col.markdown(f"**{r.spot}**  \n{r.area} · {r.category}  \n"
                         f"{level_badge(r.congestion)}  \n혼잡률 {r.ratio * 100:.0f}% · {r.dist_km}km",
                         unsafe_allow_html=True)

    # 지도
    st.subheader("🗺️ 관광지별 예상 혼잡도 지도")
    view_map = view.copy()
    view_map["혼잡률(%)"] = (view_map["ratio"] * 100).round()
    view_map["size"] = view_map["ratio"].clip(0.15, 1.5) * 20
    fmap = px.scatter_map(view_map, lat="lat", lon="lon", color="congestion", size="size",
                             color_discrete_map=CONGESTION_COLORS,
                             category_orders={"congestion": CONGESTION_LEVELS},
                             hover_name="spot", hover_data={"area": True, "pred_visitors": True, "혼잡률(%)": True,
                                                            "lat": False, "lon": False, "size": False},
                             labels={"congestion": "혼잡도", "pred_visitors": "예상 방문객", "area": "지역"},
                             zoom=9, center={"lat": 33.38, "lon": 126.55}, height=480)
    fmap.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fmap, width="stretch")

    st.subheader("📋 전체 관광지 혼잡도 순위 (한적한 순)")
    table = view.sort_values("ratio")[["spot", "area", "category", "pred_visitors", "ratio", "congestion"]]
    table.columns = ["관광지", "지역", "유형", "예상 방문객(명/시간)", "혼잡률", "혼잡도"]
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"혼잡률": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1.5)})

# ---------------- 탭2: EDA ----------------
with tab2:
    st.caption("2025년 1년치 샘플 데이터 (관광지 28곳 × 365일 × 08~19시)")
    c1, c2, c3 = st.columns(3)
    c1.metric("데이터 행 수", f"{len(df):,}")
    c2.metric("관광지 수", df["spot"].nunique())
    c3.metric("평균 시간당 방문객", f"{df['visitors'].mean():.0f}명")

    a, b = st.columns(2)
    with a:
        m = df.groupby("month", as_index=False)["visitors"].mean()
        f = px.line(m, x="month", y="visitors", markers=True, title="Q1. 월별 평균 방문객 (성수기는 언제?)",
                    labels={"month": "월", "visitors": "평균 방문객"})
        f.update_layout(xaxis_dtick=1)
        st.plotly_chart(f, width="stretch")
    with b:
        w = df.groupby(["weekday", "is_holiday"], as_index=False)["visitors"].mean()
        w["요일"] = w["weekday"].map(lambda i: WEEKDAYS[i])
        w["공휴일"] = w["is_holiday"].map({0: "일반일", 1: "공휴일"})
        f = px.bar(w, x="요일", y="visitors", color="공휴일", barmode="group",
                   title="Q2. 요일·공휴일별 평균 방문객", labels={"visitors": "평균 방문객"})
        st.plotly_chart(f, width="stretch")

    a, b = st.columns(2)
    with a:
        hm = df.groupby(["category", "hour"], as_index=False)["congestion_ratio"].mean()
        f = px.density_heatmap(hm, x="hour", y="category", z="congestion_ratio", histfunc="avg",
                               color_continuous_scale="YlOrRd", title="Q3. 유형 × 시간대별 평균 혼잡률",
                               labels={"hour": "시간", "category": "유형", "congestion_ratio": "혼잡률"})
        st.plotly_chart(f, width="stretch")
    with b:
        wt = df.merge(spots[["spot", "indoor"]], on="spot")
        wt["실내/실외"] = wt["indoor"].map({True: "실내", False: "실외"})
        wt = wt.groupby(["weather", "실내/실외"], as_index=False)["visitors"].mean()
        f = px.bar(wt, x="weather", y="visitors", color="실내/실외", barmode="group",
                   category_orders={"weather": WEATHERS}, title="Q4. 날씨에 따른 실내·실외 관광지 방문객",
                   labels={"weather": "날씨", "visitors": "평균 방문객"})
        st.plotly_chart(f, width="stretch")

    top = df.groupby("spot", as_index=False)["congestion_ratio"].mean().sort_values("congestion_ratio")
    f = px.bar(top, x="congestion_ratio", y="spot", orientation="h", height=700,
               title="Q5. 관광지별 연평균 혼잡률", labels={"congestion_ratio": "평균 혼잡률", "spot": ""})
    st.plotly_chart(f, width="stretch")
    with st.expander("원본 데이터 미리보기"):
        st.dataframe(df.head(200), width="stretch")

# ---------------- 탭3: 모델 성능 ----------------
with tab3:
    st.markdown("**예측 문제**: 관광지·지역·유형·날씨·월·요일·시간·주말·공휴일 → **시간당 방문객 수(회귀)** 예측 후, "
                "수용력 대비 비율로 **혼잡도 4단계(여유/보통/약간 혼잡/혼잡)** 로 변환합니다.")
    st.markdown("Feature: `" + "`, `".join(FEATURES) + "` · Label: `visitors`")
    res, best, sample = get_eval()
    st.dataframe(res, hide_index=True, width="stretch")
    st.success(f"가장 성능이 좋은 모델: **{best}** → 앱 예측에 사용")
    f = px.scatter(sample, x="실제 방문객", y="예측 방문객", opacity=0.4, title="실제값 vs 예측값 (테스트셋 2,000건)")
    mx = sample[["실제 방문객", "예측 방문객"]].max().max()
    f.add_shape(type="line", x0=0, y0=0, x1=mx, y1=mx, line=dict(dash="dash", color="gray"))
    st.plotly_chart(f, width="stretch")
    st.caption("※ 합성 데이터라 패턴이 규칙적이어서 성능이 높게 나옵니다. 실데이터에서는 성능이 낮아질 수 있습니다.")

# ---------------- 탭4: 데이터 안내 ----------------
with tab4:
    st.markdown("""
### 이 데모의 데이터
- `data/jeju_congestion_sample.csv.gz` 는 **실제 측정값이 아닌 샘플(합성) 데이터**입니다.
- 실제 제주 관광지 28곳의 이름·위치를 사용했고, 성수기·주말·공휴일·시간대·날씨 영향을 반영해 방문객 수를 생성했습니다.

### 실데이터로 바꾸려면
| 데이터 | 출처 | 용도 |
|---|---|---|
| 관광지 혼잡도·방문객 | [제주데이터허브](https://www.jejudatahub.net) | 학습 라벨(방문객 수) |
| 관광지 집중률 예측 | [한국관광 데이터랩](https://datalab.visitkorea.or.kr) · 공공데이터포털 '관광지 집중률 방문자 추이 예측' API | 라벨/검증 |
| 관광지 정보·좌표 | 한국관광공사 TourAPI (공공데이터포털) | 관광지 목록 |
| 날씨 | 기상청 단기예보 API (공공데이터포털) | 날씨 Feature |
| 공휴일 | 한국천문연구원 특일 정보 API | 공휴일 Feature |

API 키 발급 후 `.streamlit/secrets.toml` 에 넣고, `src/generate_data.py` 대신 수집 스크립트로 같은 컬럼 구조의 CSV를 만들면 앱은 그대로 동작합니다.
""")
