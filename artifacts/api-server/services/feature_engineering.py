"""
Create ML features from journal entries for fraud detection.
"""
import numpy as np
import pandas as pd
from typing import Dict


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create all features for ML and rule-based analysis."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # 1. Transaction Amount (log-normalized)
    df["feat_amount"] = df["amount"].clip(lower=1.0)
    df["feat_log_amount"] = np.log1p(df["feat_amount"])

    # 2. Debit/Credit Difference (imbalance indicator)
    df["feat_debit_credit_diff"] = (df["debit"] - df["credit"]).abs()
    df["feat_debit_credit_diff_pct"] = df["feat_debit_credit_diff"] / (df["amount"].clip(lower=1.0))

    # 3. Posting Hour (0-23)
    df["feat_posting_hour"] = df["date"].dt.hour

    # 4. Weekend Posting (1 = weekend)
    df["feat_is_weekend"] = (df["date"].dt.dayofweek >= 5).astype(int)

    # 5. Round Number (amount is divisible by 1000)
    df["feat_is_round_1000"] = ((df["amount"] % 1000) == 0).astype(int)
    df["feat_is_round_10000"] = ((df["amount"] % 10000) == 0).astype(int)

    # 6. Account Frequency (how often does this account appear)
    account_freq = df["account_code"].value_counts()
    df["feat_account_frequency"] = df["account_code"].map(account_freq).fillna(0)

    # 7. User Frequency (total entries per user)
    user_freq = df["user"].value_counts()
    df["feat_user_frequency"] = df["user"].map(user_freq).fillna(0)

    # 8. Large Transaction (amount > 95th percentile)
    p95 = df["amount"].quantile(0.95)
    df["feat_is_large_transaction"] = (df["amount"] > p95).astype(int)

    # 9. Historical Average Deviation
    account_avg = df.groupby("account_code")["amount"].transform("mean")
    df["feat_amount_vs_avg"] = (df["amount"] - account_avg).abs() / (account_avg.clip(lower=1.0))

    # 10. Monthly Change %
    monthly = df.groupby(["account_code", "period"])["amount"].sum().reset_index()
    monthly = monthly.sort_values(["account_code", "period"])
    monthly["prev_month_amount"] = monthly.groupby("account_code")["amount"].shift(1)
    monthly["monthly_change_pct"] = (
        (monthly["amount"] - monthly["prev_month_amount"]).abs()
        / monthly["prev_month_amount"].clip(lower=1.0)
    ).fillna(0)

    df = df.merge(
        monthly[["account_code", "period", "monthly_change_pct"]],
        on=["account_code", "period"],
        how="left"
    )
    df["feat_monthly_change_pct"] = df["monthly_change_pct"].fillna(0)

    # 11. Account Variance
    account_var = df.groupby("account_code")["amount"].transform("std").fillna(0)
    df["feat_account_variance"] = account_var / (df["amount"].clip(lower=1.0))

    # 12. Inactive Account (account appears < 5 times total)
    df["feat_inactive_account"] = (df["feat_account_frequency"] < 5).astype(int)

    # 13. Out-of-hours posting (before 7am or after 8pm)
    df["feat_out_of_hours"] = (
        (df["feat_posting_hour"] < 7) | (df["feat_posting_hour"] > 20)
    ).astype(int)

    # 14. Duplicate detection (same amount, account, user, date within 24h)
    df_sorted = df.sort_values("date")
    df["feat_potential_duplicate"] = 0
    key_cols = ["account_code", "user", "amount"]
    dupe_mask = df.duplicated(subset=key_cols, keep=False)
    df.loc[dupe_mask, "feat_potential_duplicate"] = 1

    return df


def get_ml_feature_columns() -> list:
    """Return the feature columns to use for ML training."""
    return [
        "feat_log_amount",
        "feat_debit_credit_diff_pct",
        "feat_posting_hour",
        "feat_is_weekend",
        "feat_is_round_1000",
        "feat_account_frequency",
        "feat_user_frequency",
        "feat_is_large_transaction",
        "feat_amount_vs_avg",
        "feat_monthly_change_pct",
        "feat_account_variance",
        "feat_inactive_account",
        "feat_out_of_hours",
        "feat_potential_duplicate",
    ]
