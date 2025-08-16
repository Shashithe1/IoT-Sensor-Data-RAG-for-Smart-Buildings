import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression

# ---------- Anomaly Detection ----------
def detect_anomalies(df: pd.DataFrame):
    """Detect anomalies in sensor data using IsolationForest."""
    if df.empty:
        return pd.DataFrame()

    # Use numeric features only
    X = df[["value"]].values

    model = IsolationForest(contamination=0.1, random_state=42)
    df["anomaly"] = model.fit_predict(X)

    # anomaly = -1 means anomaly
    return df[df["anomaly"] == -1]

# ---------- Feature Extraction ----------
def features_last_window(df: pd.DataFrame, window_minutes=30):
    """Aggregate features for each sensor over a time window."""
    if df.empty:
        return pd.DataFrame()

    # Round timestamp to window
    df["window"] = pd.to_datetime(df["ts"]).dt.floor(f"{window_minutes}min")

    # Aggregate per sensor + metric
    feats = (
        df.groupby(["sensor_id", "metric", "window"])
        .agg(avg_value=("value", "mean"), std_value=("value", "std"))
        .reset_index()
    )

    # Pivot to wide format: each metric becomes a column
    feats = feats.pivot_table(
        index=["sensor_id", "window"], columns="metric", values="avg_value"
    ).reset_index()

    # Fill NaNs
    feats = feats.fillna(0)

    return feats

# ---------- Dummy Predictor ----------
def fit_dummy_predictor(feats: pd.DataFrame):
    """Train a dummy logistic regression predictor (with safe fallback)."""
    if feats.empty:
        # Return a dummy model if no features
        class DummyModel:
            def predict_proba(self, X_input):
                return np.array([[0.5, 0.5]] * len(X_input))
        return DummyModel()

    X = feats.drop(columns=["sensor_id", "window"]).values
    # Dummy labels (all 1)
    y = np.ones(len(feats))

    # ⚡ Safe fallback: if y has only one class
    if len(np.unique(y)) < 2:
        class DummyModel:
            def predict_proba(self, X_input):
                return np.array([[0.0, 1.0]] * len(X_input))
        return DummyModel()

    # Otherwise, fit a real model
    clf = LogisticRegression()
    clf.fit(X, y)
    return clf

# ---------- Risk Scoring ----------
def score_risk(clf, feats: pd.DataFrame):
    """Assign risk scores per sensor based on model predictions."""
    if feats.empty:
        return pd.DataFrame()

    X = feats.drop(columns=["sensor_id", "window"]).values
    probs = clf.predict_proba(X)[:, 1]

    feats = feats.copy()
    feats["risk_score"] = probs
    return feats[["sensor_id", "window", "risk_score"]]
