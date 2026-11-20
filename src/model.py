"""혼잡도 예측 모델 (방문객 수 회귀 → 수용력 대비 비율 → 혼잡도 단계).

실행: python -m src.model   (모델 비교 결과를 출력하고 models/ 에 저장)
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

from src.spots import HOLIDAYS, congestion_level, spots_df

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "jeju_congestion_sample.csv.gz"
MODEL_PATH = ROOT / "models" / "congestion_model.joblib"

CAT_FEATURES = ["spot", "area", "category", "weather"]
NUM_FEATURES = ["month", "weekday", "hour", "is_weekend", "is_holiday"]
FEATURES = CAT_FEATURES + NUM_FEATURES
TARGET = "visitors"


def load_data() -> pd.DataFrame:
    if not DATA.exists():
        from src.generate_data import generate
        DATA.parent.mkdir(exist_ok=True)
        generate().to_csv(DATA, index=False, compression="gzip")
    return pd.read_csv(DATA)


def make_models() -> dict:
    ohe = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
                             ("num", "passthrough", NUM_FEATURES)])
    ord_enc = ColumnTransformer([("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                                  CAT_FEATURES), ("num", "passthrough", NUM_FEATURES)])
    return {
        "LinearRegression": Pipeline([("prep", ohe), ("model", LinearRegression())]),
        "RandomForest": Pipeline([("prep", ord_enc),
                                  ("model", RandomForestRegressor(n_estimators=60, max_depth=18,
                                                                  min_samples_leaf=3, n_jobs=-1, random_state=42))]),
        "HistGradientBoosting": Pipeline([("prep", ord_enc),
                                          ("model", HistGradientBoostingRegressor(
                                              max_iter=300, learning_rate=0.1,
                                              categorical_features=list(range(len(CAT_FEATURES))),
                                              random_state=42))]),
    }


def evaluate(df: pd.DataFrame, sample: int | None = 60000):
    """모델 비교. 반환: (결과표, 최적 모델 이름, 학습된 모델 dict, 테스트셋)."""
    data = df.sample(sample, random_state=42) if sample and len(df) > sample else df
    X, y = data[FEATURES], data[TARGET]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    cap_te = data.loc[X_te.index, "capacity"]
    true_level = (y_te / cap_te).map(congestion_level)

    results, fitted = [], {}
    for name, m in make_models().items():
        m.fit(X_tr, y_tr)
        pred = np.clip(m.predict(X_te), 0, None)
        pred_level = pd.Series(pred / cap_te.values, index=X_te.index).map(congestion_level)
        results.append({"모델": name,
                        "MAE(명)": round(mean_absolute_error(y_te, pred), 1),
                        "R²": round(r2_score(y_te, pred), 3),
                        "혼잡도 단계 정확도": round(accuracy_score(true_level, pred_level), 3)})
        fitted[name] = m
    res = pd.DataFrame(results).sort_values("MAE(명)").reset_index(drop=True)
    return res, res.loc[0, "모델"], fitted, (X_te, y_te, cap_te)


def train_final(df: pd.DataFrame) -> Pipeline:
    m = make_models()["HistGradientBoosting"]
    m.fit(df[FEATURES], df[TARGET])
    return m


def build_features(date: pd.Timestamp, hour: int | list[int], weather: str,
                   spots: pd.DataFrame | None = None) -> pd.DataFrame:
    """예측용 입력 테이블 (관광지 × 시간)."""
    spots = spots_df() if spots is None else spots
    hours = [hour] if isinstance(hour, int) else list(hour)
    ds = date.strftime("%Y-%m-%d")
    rows = []
    for s in spots.itertuples():
        for h in hours:
            rows.append({"spot": s.spot, "area": s.area, "category": s.category, "weather": weather,
                         "month": date.month, "weekday": date.weekday(), "hour": h,
                         "is_weekend": int(date.weekday() >= 5), "is_holiday": int(ds in HOLIDAYS),
                         "capacity": s.capacity, "lat": s.lat, "lon": s.lon, "indoor": s.indoor})
    return pd.DataFrame(rows)


def predict(model, feats: pd.DataFrame) -> pd.DataFrame:
    out = feats.copy()
    out["pred_visitors"] = np.clip(model.predict(out[FEATURES]), 0, None).round().astype(int)
    out["ratio"] = (out["pred_visitors"] / out["capacity"]).round(2)
    out["congestion"] = out["ratio"].map(congestion_level)
    return out


if __name__ == "__main__":
    df = load_data()
    res, best, _, _ = evaluate(df)
    print(res.to_string(index=False))
    print("best:", best)
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(train_final(df), MODEL_PATH)
    print("saved", MODEL_PATH)
