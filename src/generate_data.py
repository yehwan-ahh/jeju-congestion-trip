"""데모용 샘플(합성) 데이터 생성 스크립트.

⚠️ 이 데이터는 실제 측정값이 아닙니다. 제주 관광의 일반적인 패턴
(성수기·주말·공휴일·시간대·날씨 영향)을 반영해 만든 가상의 시간대별 방문객 수입니다.

실행: python -m src.generate_data
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.spots import HOLIDAYS, OPEN_HOURS, WEATHERS, congestion_level, spots_df

OUT = Path(__file__).resolve().parent.parent / "data" / "jeju_congestion_sample.csv.gz"

# 월별 관광 수요 지수 (여름 휴가철·봄 유채꽃·가을 단풍 시즌 반영)
MONTH_FACTOR = {1: 0.70, 2: 0.75, 3: 0.90, 4: 1.05, 5: 1.10, 6: 0.95,
                7: 1.20, 8: 1.30, 9: 0.95, 10: 1.10, 11: 0.85, 12: 0.80}
# 월별 비 올 확률
RAIN_PROB = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25, 5: 0.25, 6: 0.40,
             7: 0.45, 8: 0.40, 9: 0.35, 10: 0.20, 11: 0.25, 12: 0.30}

# 카테고리별 시간대 패턴 (중심 시각, 폭)
HOUR_PATTERN = {
    "자연·경관": (12.5, 3.2),
    "섬·해변": (14.0, 3.0),
    "숲·오름": (11.0, 2.8),
    "테마·체험": (13.5, 2.8),
    "문화·박물관": (14.0, 2.6),
    "시장·먹거리": (17.0, 2.6),
}


def generate(start="2025-01-01", end="2025-12-31", seed=42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    spots = spots_df()
    dates = pd.date_range(start, end, freq="D")

    # 날짜별 날씨 (지역 공통)
    weather = {}
    for d in dates:
        p_rain = RAIN_PROB[d.month]
        weather[d] = rng.choice(WEATHERS, p=[(1 - p_rain) * 0.6, (1 - p_rain) * 0.4, p_rain])

    rows = []
    for d in dates:
        ds = d.strftime("%Y-%m-%d")
        is_holiday = ds in HOLIDAYS
        is_weekend = d.weekday() >= 5
        day_factor = MONTH_FACTOR[d.month] * (1.35 if is_weekend else 1.0) * (1.45 if is_holiday else 1.0)
        w = weather[d]
        for s in spots.itertuples():
            if w == "비":
                wf = 1.45 if s.indoor else 0.55
            elif w == "흐림":
                wf = 1.10 if s.indoor else 0.92
            else:
                wf = 1.0
            # 해변은 여름에 더 붐빔
            sf = 1.0
            if s.category == "섬·해변":
                sf = {6: 1.2, 7: 1.6, 8: 1.8}.get(d.month, 0.8)
            center, width = HOUR_PATTERN[s.category]
            for h in OPEN_HOURS:
                hf = np.exp(-((h - center) ** 2) / (2 * width ** 2))
                if s.spot == "성산일출봉" and h == 8:
                    hf += 0.5  # 일출 관람객
                mean = s.capacity * 1.1 * s.popularity * day_factor * wf * sf * hf
                visitors = max(0, int(rng.normal(mean, mean * 0.15 + 5)))
                rows.append((ds, d.month, d.weekday(), h, int(is_weekend), int(is_holiday), w,
                             s.spot, s.area, s.category, visitors, s.capacity))

    df = pd.DataFrame(rows, columns=["date", "month", "weekday", "hour", "is_weekend", "is_holiday",
                                     "weather", "spot", "area", "category", "visitors", "capacity"])
    df["congestion_ratio"] = (df["visitors"] / df["capacity"]).round(3)
    df["congestion"] = df["congestion_ratio"].map(congestion_level)
    return df


if __name__ == "__main__":
    df = generate()
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False, compression="gzip")
    print(f"saved {len(df):,} rows → {OUT}")
    print(df["congestion"].value_counts(normalize=True).round(3))
