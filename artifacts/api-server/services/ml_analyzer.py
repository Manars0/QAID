"""
Isolation Forest ML model for anomaly detection.
Returns anomaly scores normalized to 0-100 (higher = more suspicious).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
from services.feature_engineering import get_ml_feature_columns


def run_isolation_forest(df: pd.DataFrame) -> np.ndarray:
    """
    Run Isolation Forest on the feature columns.
    Returns an array of ML scores (0-100) for each row.
    """
    feature_cols = get_ml_feature_columns()

    # Ensure all feature columns exist and are numeric
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0

    X = df[feature_cols].fillna(0).values.astype(float)

    # Handle edge case: too few samples
    n_samples = len(X)
    if n_samples < 10:
        return np.zeros(n_samples)

    # Adjust contamination based on dataset size
    contamination = min(0.15, max(0.05, 100.0 / n_samples))

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples=min(256, n_samples),
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    # decision_function returns negative values for anomalies
    # More negative = more anomalous
    decision_scores = model.decision_function(X)

    # Invert and normalize to 0-100 (higher = more anomalous)
    inverted = -decision_scores  # more positive = more anomalous
    scaler = MinMaxScaler(feature_range=(0, 100))
    ml_scores = scaler.fit_transform(inverted.reshape(-1, 1)).flatten()

    return ml_scores


def compute_fraud_probability(ml_score: float, rule_score: float) -> float:
    """
    Compute fraud probability by combining ML and rule scores.
    Rule Engine: 60%, ML: 40%
    """
    combined = 0.60 * rule_score + 0.40 * ml_score
    # Convert to probability (0-1)
    return min(combined / 100.0, 1.0)


def compute_final_risk_score(ml_score: float, rule_score: float) -> float:
    """Final risk score: 60% rule + 40% ML, normalized to 0-100."""
    return min(0.60 * rule_score + 0.40 * ml_score, 100.0)


def assign_risk_level(risk_score: float) -> str:
    """Assign a risk level label based on the score."""
    if risk_score >= 75:
        return "CRITICAL"
    elif risk_score >= 50:
        return "HIGH"
    elif risk_score >= 25:
        return "MEDIUM"
    else:
        return "LOW"
