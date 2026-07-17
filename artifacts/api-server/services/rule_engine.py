"""
Financial Rule Engine.
Each rule has a configurable weight (0-100).
Returns triggered rules and composite rule score per entry.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple


RULES = [
    {
        "id": "debit_credit_imbalance",
        "name": "Debit/Credit Imbalance",
        "description": "Debit and credit amounts differ by more than 5%",
        "weight": 100,
        "severity": "CRITICAL",
    },
    {
        "id": "large_amount",
        "name": "Unusually Large Amount",
        "description": "Transaction amount exceeds 3x the account average",
        "weight": 70,
        "severity": "HIGH",
    },
    {
        "id": "weekend_posting",
        "name": "Weekend Posting",
        "description": "Transaction posted on Saturday or Sunday",
        "weight": 40,
        "severity": "MEDIUM",
    },
    {
        "id": "round_numbers",
        "name": "Suspicious Round Numbers",
        "description": "Transaction amount is an exact round number (multiple of 10,000)",
        "weight": 35,
        "severity": "MEDIUM",
    },
    {
        "id": "inactive_account",
        "name": "Inactive Account Activity",
        "description": "Transaction on an account with fewer than 5 total entries",
        "weight": 45,
        "severity": "HIGH",
    },
    {
        "id": "duplicate_entry",
        "name": "Potential Duplicate Entry",
        "description": "Same amount, account, and user appear more than once",
        "weight": 80,
        "severity": "HIGH",
    },
    {
        "id": "high_user_frequency",
        "name": "High User Entry Volume",
        "description": "User has posted an unusually high number of entries",
        "weight": 50,
        "severity": "MEDIUM",
    },
    {
        "id": "large_monthly_variance",
        "name": "Large Monthly Account Variance",
        "description": "Monthly account balance change exceeds 200%",
        "weight": 60,
        "severity": "HIGH",
    },
    {
        "id": "out_of_hours",
        "name": "Out-of-Hours Posting",
        "description": "Transaction posted before 7am or after 8pm",
        "weight": 30,
        "severity": "LOW",
    },
    {
        "id": "suspense_account",
        "name": "Suspense Account Usage",
        "description": "Transaction uses a suspense or clearing account",
        "weight": 55,
        "severity": "HIGH",
    },
    {
        "id": "high_debit_credit_diff",
        "name": "Extreme Debit/Credit Difference",
        "description": "Debit/Credit difference exceeds 20% of the transaction amount",
        "weight": 85,
        "severity": "CRITICAL",
    },
]

MAX_POSSIBLE_WEIGHT = sum(r["weight"] for r in RULES)

SUSPENSE_ACCOUNTS = {"9000", "9100", "9200", "9300", "8400"}


def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all rules to the dataframe. Returns df with triggered_rules and rule_score columns."""
    df = df.copy()

    # Pre-compute thresholds
    account_avg = df.groupby("account_code")["amount"].mean()
    user_freq = df["user"].value_counts()
    user_p95 = user_freq.quantile(0.95)

    triggered_rules_list = []
    rule_scores = []

    for _, row in df.iterrows():
        triggered = []
        total_weight = 0

        amount = row.get("amount", 0)
        acct = str(row.get("account_code", ""))
        user = str(row.get("user", ""))
        hour = row.get("feat_posting_hour", 12)
        is_weekend = row.get("feat_is_weekend", 0)
        acct_avg = account_avg.get(acct, amount)
        monthly_chg = row.get("feat_monthly_change_pct", 0)
        user_count = user_freq.get(user, 0)
        is_dup = row.get("feat_potential_duplicate", 0)
        acct_freq = row.get("feat_account_frequency", 10)

        # Debit/Credit imbalance — use journal-level balance when available.
        # For double-entry line format (debit=X,credit=0 or debit=0,credit=X),
        # only fire when both sides are non-zero OR when journal-level data exists.
        journal_balanced = row.get("_journal_balanced", None)
        if journal_balanced is not None:
            # Have journal-level data: use it
            dc_diff_pct = row.get("_journal_imbalance_pct", 0.0)
        else:
            # Flat format: only meaningful when both sides are populated
            debit = row.get("debit", 0)
            credit = row.get("credit", 0)
            if debit > 0 and credit > 0:
                dc_diff_pct = abs(debit - credit) / max(amount, 1)
            else:
                dc_diff_pct = 0.0

        # R1: Debit/Credit imbalance > 5%
        if dc_diff_pct > 0.05:
            rule = next(r for r in RULES if r["id"] == "debit_credit_imbalance")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R11: Extreme diff > 20%
        if dc_diff_pct > 0.20:
            rule = next(r for r in RULES if r["id"] == "high_debit_credit_diff")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R2: Amount > 3x account average
        if amount > 3 * max(acct_avg, 1):
            rule = next(r for r in RULES if r["id"] == "large_amount")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R3: Weekend
        if is_weekend:
            rule = next(r for r in RULES if r["id"] == "weekend_posting")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R4: Round numbers
        if amount >= 10000 and amount % 10000 == 0:
            rule = next(r for r in RULES if r["id"] == "round_numbers")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R5: Inactive account
        if acct_freq < 5:
            rule = next(r for r in RULES if r["id"] == "inactive_account")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R6: Duplicate
        if is_dup:
            rule = next(r for r in RULES if r["id"] == "duplicate_entry")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R7: High user frequency
        if user_count > user_p95:
            rule = next(r for r in RULES if r["id"] == "high_user_frequency")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R8: Large monthly variance > 200%
        if monthly_chg > 2.0:
            rule = next(r for r in RULES if r["id"] == "large_monthly_variance")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R9: Out of hours
        if hour < 7 or hour > 20:
            rule = next(r for r in RULES if r["id"] == "out_of_hours")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        # R10: Suspense account
        if acct in SUSPENSE_ACCOUNTS:
            rule = next(r for r in RULES if r["id"] == "suspense_account")
            triggered.append(rule["name"])
            total_weight += rule["weight"]

        rule_score = min((total_weight / MAX_POSSIBLE_WEIGHT) * 100, 100)
        triggered_rules_list.append(list(set(triggered)))
        rule_scores.append(rule_score)

    df["triggered_rules"] = triggered_rules_list
    df["rule_score"] = rule_scores
    return df


def get_rule_detail_for_entry(entry: pd.Series) -> List[Dict]:
    """Get detailed rule breakdown for a single entry."""
    details = []

    amount = entry.get("amount", 0)
    acct = str(entry.get("account_code", ""))
    hour = entry.get("feat_posting_hour", 12)
    is_weekend = entry.get("feat_is_weekend", 0)
    monthly_chg = entry.get("feat_monthly_change_pct", 0)
    is_dup = entry.get("feat_potential_duplicate", 0)
    acct_freq = entry.get("feat_account_frequency", 10)

    journal_balanced = entry.get("_journal_balanced", None)
    if journal_balanced is not None:
        dc_diff_pct = entry.get("_journal_imbalance_pct", 0.0)
    else:
        debit = entry.get("debit", 0)
        credit = entry.get("credit", 0)
        if debit > 0 and credit > 0:
            dc_diff_pct = abs(debit - credit) / max(amount, 1)
        else:
            dc_diff_pct = 0.0

    checks = [
        ("debit_credit_imbalance", dc_diff_pct > 0.05),
        ("high_debit_credit_diff", dc_diff_pct > 0.20),
        ("large_amount", amount > 50000),
        ("weekend_posting", bool(is_weekend)),
        ("round_numbers", amount >= 10000 and amount % 10000 == 0),
        ("inactive_account", acct_freq < 5),
        ("duplicate_entry", bool(is_dup)),
        ("large_monthly_variance", monthly_chg > 2.0),
        ("out_of_hours", hour < 7 or hour > 20),
        ("suspense_account", acct in SUSPENSE_ACCOUNTS),
    ]

    for rule_id, triggered in checks:
        if triggered:
            rule = next((r for r in RULES if r["id"] == rule_id), None)
            if rule:
                details.append({
                    "rule_name": rule["name"],
                    "weight": rule["weight"],
                    "description": rule["description"],
                })

    return details
