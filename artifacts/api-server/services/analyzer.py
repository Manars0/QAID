"""
Main QAID analysis orchestrator.
Combines file processing, feature engineering, rule engine, and ML.
"""
import uuid
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any

from services.feature_engineering import engineer_features
from services.rule_engine import apply_rules, get_rule_detail_for_entry
from services.ml_analyzer import (
    run_isolation_forest,
    compute_fraud_probability,
    compute_final_risk_score,
    assign_risk_level,
)
from models.schemas import (
    AnalysisResult, KpiSummary, RiskDistribution, RiskTrend, RiskEntry,
    RiskAccount, ChangedAccount, FraudIndicator, ComplianceItem,
    ValidationIssue, EntryDetail, TriggeredRule,
)

# In-memory session storage
_sessions: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str) -> Dict[str, Any]:
    return _sessions.get(session_id)


def run_analysis(
    df: pd.DataFrame,
    file_name: str,
    fraud_labels: "pd.DataFrame | None" = None,
) -> AnalysisResult:
    """Run the full QAID analysis pipeline.

    Parameters
    ----------
    df : pd.DataFrame
        Standardised journal-line records from the dataset loader.
    file_name : str
        Human-readable label for the source file.
    fraud_labels : pd.DataFrame | None
        Ground-truth fraud table (ERP ZIPs only).
        Used ONLY internally to validate model performance and enrich the
        executive summary. Never exposed to the frontend.
    """
    session_id = str(uuid.uuid4())[:8]
    created_at = datetime.utcnow().isoformat() + "Z"

    # === DATA VALIDATION ===
    validation_issues = _validate_data(df)

    # === FEATURE ENGINEERING ===
    df = engineer_features(df)

    # === RULE ENGINE ===
    df = apply_rules(df)

    # === MACHINE LEARNING ===
    ml_scores = run_isolation_forest(df)
    df["ml_score"] = ml_scores

    # === COMBINED SCORING ===
    df["risk_score"] = df.apply(
        lambda r: compute_final_risk_score(r["ml_score"], r["rule_score"]), axis=1
    )
    df["fraud_probability"] = df.apply(
        lambda r: compute_fraud_probability(r["ml_score"], r["rule_score"]), axis=1
    )
    df["risk_level"] = df["risk_score"].apply(assign_risk_level)

    # === GROUND-TRUTH VALIDATION (internal, never exposed) ===
    fraud_info = _compute_fraud_info(df, fraud_labels)

    # === BUILD OUTPUT ===
    kpi = _compute_kpi(df)
    risk_dist = _compute_risk_distribution(df)
    risk_trend = _compute_risk_trend(df)
    high_risk_entries = _get_high_risk_entries(df)
    high_risk_accounts = _get_high_risk_accounts(df)
    top_changed = _get_top_changed_accounts(df)
    fraud_indicators = _get_fraud_indicators(df)
    compliance = _check_ifrs_compliance(df, kpi)
    recommendations = _generate_recommendations(df, kpi, fraud_indicators, compliance, fraud_info)
    ai_summary = _generate_ai_summary(kpi, fraud_indicators, compliance, fraud_info)

    result = AnalysisResult(
        session_id=session_id,
        file_name=file_name,
        kpi_summary=kpi,
        risk_distribution=risk_dist,
        risk_trend=risk_trend,
        high_risk_entries=high_risk_entries,
        high_risk_accounts=high_risk_accounts,
        top_changed_accounts=top_changed,
        fraud_indicators=fraud_indicators,
        compliance_items=compliance,
        recommendations=recommendations,
        ai_summary=ai_summary,
        validation_issues=validation_issues,
        created_at=created_at,
        total_entries_analyzed=len(df),
    )

    # Store session for later queries
    _sessions[session_id] = {"df": df, "result": result}
    return result


def get_entries_for_session(session_id: str, limit: int = 200, min_risk: float = 0) -> list:
    session = _sessions.get(session_id)
    if not session:
        return None
    df = session["df"]
    filtered = df[df["risk_score"] >= min_risk].sort_values("risk_score", ascending=False).head(limit)
    return [_row_to_risk_entry(row) for _, row in filtered.iterrows()]


def get_entry_detail_for_session(session_id: str, entry_id: str) -> EntryDetail:
    session = _sessions.get(session_id)
    if not session:
        return None
    df = session["df"]
    matches = df[df["entry_id"] == entry_id]
    if matches.empty:
        return None
    row = matches.iloc[0]
    return _row_to_entry_detail(row)


def get_raw_df(session_id: str) -> pd.DataFrame:
    session = _sessions.get(session_id)
    if not session:
        return None
    return session["df"]


# ===== PRIVATE HELPERS =====

def _compute_fraud_info(df: pd.DataFrame, fraud_labels: "pd.DataFrame | None") -> dict | None:
    """
    Compute internal model-performance metrics against ground-truth Fraud_Labels.
    Returns a dict used only in executive summary and recommendations.
    Never exposed to the frontend.
    """
    has_known = "_known_fraud" in df.columns and df["_known_fraud"].any()
    if not has_known:
        return None

    known_mask = df["_known_fraud"].astype(bool)
    total_known = int(known_mask.sum())

    caught_high = int((known_mask & (df["risk_score"] >= 50)).sum())
    caught_critical = int((known_mask & (df["risk_score"] >= 75)).sum())
    recall_high = round(caught_high / max(total_known, 1), 4)

    # Derive unique fraud types from fraud_labels if available
    fraud_types: list[str] = []
    if fraud_labels is not None and "fraud_type" in fraud_labels.columns:
        fraud_types = (
            fraud_labels[fraud_labels.get("is_fraud", fraud_labels["fraud"].str.lower().isin(["yes","true","1"]))]
            ["fraud_type"]
            .dropna()
            .unique()
            .tolist()[:5]
        )

    return {
        "total_known": total_known,
        "caught_high": caught_high,
        "caught_critical": caught_critical,
        "recall": recall_high,
        "fraud_types": fraud_types,
    }


def _validate_data(df: pd.DataFrame) -> list:
    issues = []

    # Missing values
    for col in ["account_code", "date", "amount"]:
        missing = df[col].isna().sum() if col in df.columns else 0
        if missing > 0:
            issues.append(ValidationIssue(
                type="MISSING_VALUES",
                severity="HIGH",
                count=int(missing),
                description=f"Missing values in column '{col}'",
            ))

    # Duplicate rows
    dup_count = df.duplicated(subset=["entry_id"]).sum()
    if dup_count > 0:
        issues.append(ValidationIssue(
            type="DUPLICATE_ROWS",
            severity="HIGH",
            count=int(dup_count),
            description="Duplicate journal entry IDs detected",
        ))

    # Invalid dates
    invalid_dates = df["date"].isna().sum() if "date" in df.columns else 0
    if invalid_dates > 0:
        issues.append(ValidationIssue(
            type="INVALID_DATES",
            severity="MEDIUM",
            count=int(invalid_dates),
            description="Entries with unparseable or missing dates",
        ))

    # Debit/Credit imbalance — check at journal level for double-entry format
    if "_journal_balanced" in df.columns:
        imbalance = int((~df["_journal_balanced"].astype(bool)).sum())
    else:
        both = (df["debit"] > 0) & (df["credit"] > 0)
        imbalance = int(((df.loc[both, "debit"] - df.loc[both, "credit"]).abs()
                         > df.loc[both, "amount"] * 0.05).sum())
    if imbalance > 0:
        issues.append(ValidationIssue(
            type="DEBIT_CREDIT_INCONSISTENCY",
            severity="HIGH",
            count=imbalance,
            description="Journal entries where debits and credits do not balance",
        ))

    # Zero amounts
    zero_amount = (df["amount"] <= 0).sum()
    if zero_amount > 0:
        issues.append(ValidationIssue(
            type="ZERO_AMOUNT",
            severity="MEDIUM",
            count=int(zero_amount),
            description="Entries with zero or negative amounts",
        ))

    return issues


def _compute_kpi(df: pd.DataFrame) -> KpiSummary:
    avg_risk = float(df["risk_score"].mean())
    overall_risk = round(avg_risk, 2)
    risk_level = assign_risk_level(overall_risk)

    suspicious = int((df["risk_score"] >= 50).sum())
    flagged_accounts = int(
        df[df["risk_score"] >= 50]["account_code"].nunique()
    )

    # Compliance: percentage of entries with no rule triggered
    compliant = int((df["rule_score"] == 0).sum())
    compliance_pct = round(compliant / len(df) * 100, 2)

    # AI confidence: based on dataset size and feature quality
    n = len(df)
    confidence = min(98.0, 50 + min(n / 100, 40) + (10 if n > 500 else 0))
    confidence = round(confidence, 1)

    return KpiSummary(
        overall_risk_score=overall_risk,
        risk_level=risk_level,
        total_entries=len(df),
        flagged_accounts=flagged_accounts,
        suspicious_transactions=suspicious,
        compliance_percentage=compliance_pct,
        ai_confidence=confidence,
    )


def _compute_risk_distribution(df: pd.DataFrame) -> list:
    n = len(df)
    levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    colors = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#f97316", "CRITICAL": "#ef4444"}
    dist = []
    for level in levels:
        count = int((df["risk_level"] == level).sum())
        dist.append(RiskDistribution(
            level=level,
            count=count,
            percentage=round(count / n * 100, 2),
            color=colors[level],
        ))
    return dist


def _compute_risk_trend(df: pd.DataFrame) -> list:
    if "period" not in df.columns:
        return []
    monthly = df.groupby("period").agg(
        avg_risk_score=("risk_score", "mean"),
        entry_count=("entry_id", "count"),
        flagged_count=("risk_score", lambda x: (x >= 50).sum()),
    ).reset_index()
    monthly = monthly.sort_values("period")
    return [
        RiskTrend(
            period=row["period"],
            avg_risk_score=round(float(row["avg_risk_score"]), 2),
            entry_count=int(row["entry_count"]),
            flagged_count=int(row["flagged_count"]),
        )
        for _, row in monthly.iterrows()
    ]


def _get_high_risk_entries(df: pd.DataFrame, top_n: int = 50) -> list:
    top = df.nlargest(top_n, "risk_score")
    return [_row_to_risk_entry(row) for _, row in top.iterrows()]


def _row_to_risk_entry(row) -> RiskEntry:
    return RiskEntry(
        entry_id=str(row.get("entry_id", "")),
        account=str(row.get("account_code", "")),
        account_name=str(row.get("account_name", "")) if pd.notna(row.get("account_name")) else None,
        description=str(row.get("description", "")) if pd.notna(row.get("description")) else None,
        amount=float(row.get("amount", 0)),
        debit=float(row.get("debit", 0)),
        credit=float(row.get("credit", 0)),
        date=str(row.get("date", ""))[:10] if pd.notna(row.get("date")) else "",
        user=str(row.get("user", "")) if pd.notna(row.get("user")) else None,
        risk_score=round(float(row.get("risk_score", 0)), 2),
        fraud_probability=round(float(row.get("fraud_probability", 0)), 4),
        risk_level=str(row.get("risk_level", "LOW")),
        triggered_rules=list(row.get("triggered_rules", [])),
        ml_score=round(float(row.get("ml_score", 0)), 2),
        rule_score=round(float(row.get("rule_score", 0)), 2),
    )


def _get_high_risk_accounts(df: pd.DataFrame, top_n: int = 20) -> list:
    acct_stats = df.groupby("account_code").agg(
        account_name=("account_name", "first"),
        total_entries=("entry_id", "count"),
        avg_risk_score=("risk_score", "mean"),
        total_amount=("amount", "sum"),
        max_single_amount=("amount", "max"),
    ).reset_index()
    acct_stats["risk_level"] = acct_stats["avg_risk_score"].apply(assign_risk_level)
    top = acct_stats.nlargest(top_n, "avg_risk_score")
    return [
        RiskAccount(
            account_code=str(row["account_code"]),
            account_name=str(row["account_name"]) if pd.notna(row["account_name"]) else str(row["account_code"]),
            total_entries=int(row["total_entries"]),
            avg_risk_score=round(float(row["avg_risk_score"]), 2),
            risk_level=str(row["risk_level"]),
            total_amount=round(float(row["total_amount"]), 2),
            max_single_amount=round(float(row["max_single_amount"]), 2),
        )
        for _, row in top.iterrows()
    ]


def _get_top_changed_accounts(df: pd.DataFrame, top_n: int = 10) -> list:
    if "period" not in df.columns:
        return []
    monthly = df.groupby(["account_code", "period"])["amount"].sum().reset_index()
    monthly = monthly.sort_values(["account_code", "period"])
    monthly["prev"] = monthly.groupby("account_code")["amount"].shift(1)
    monthly = monthly.dropna(subset=["prev"])
    monthly["change_pct"] = (monthly["amount"] - monthly["prev"]).abs() / monthly["prev"].clip(lower=1)

    acct_name_map = df.groupby("account_code")["account_name"].first().to_dict()
    top = monthly.nlargest(top_n, "change_pct")
    return [
        ChangedAccount(
            account_code=str(row["account_code"]),
            account_name=acct_name_map.get(row["account_code"], str(row["account_code"])),
            monthly_change_pct=round(float(row["change_pct"]) * 100, 2),
            current_month=round(float(row["amount"]), 2),
            previous_month=round(float(row["prev"]), 2),
        )
        for _, row in top.iterrows()
    ]


def _get_fraud_indicators(df: pd.DataFrame) -> list:
    indicators = []

    # Weekend posting count
    wknd = int(df["feat_is_weekend"].sum()) if "feat_is_weekend" in df.columns else 0
    if wknd > 0:
        indicators.append(FraudIndicator(
            name="Weekend Posting",
            severity="MEDIUM",
            count=wknd,
            description=f"{wknd} transactions posted on weekends outside normal business hours",
        ))

    # Round numbers
    rounds = int((df.get("feat_is_round_10000", pd.Series(dtype=int)) == 1).sum()) if "feat_is_round_10000" in df.columns else 0
    if rounds > 0:
        indicators.append(FraudIndicator(
            name="Suspiciously Round Amounts",
            severity="MEDIUM",
            count=rounds,
            description=f"{rounds} transactions are exact round multiples of 10,000",
        ))

    # Duplicates
    dups = int(df.get("feat_potential_duplicate", pd.Series(dtype=int)).sum()) if "feat_potential_duplicate" in df.columns else 0
    if dups > 0:
        indicators.append(FraudIndicator(
            name="Duplicate Entries",
            severity="HIGH",
            count=dups,
            description=f"{dups} entries share the same account, amount, and user",
        ))

    # Debit/Credit imbalance — journal level for double-entry format
    if "_journal_balanced" in df.columns:
        imbal = int((~df["_journal_balanced"].astype(bool)).sum())
    else:
        both = (df["debit"] > 0) & (df["credit"] > 0)
        imbal = int(((df.loc[both, "debit"] - df.loc[both, "credit"]).abs()
                     > df.loc[both, "amount"] * 0.05).sum())
    if imbal > 0:
        indicators.append(FraudIndicator(
            name="Debit/Credit Imbalance",
            severity="CRITICAL",
            count=imbal,
            description=f"{imbal} entries belong to journals where debits and credits do not balance",
        ))

    # Suspicious accounts
    susp_accts = {"9000", "9100", "9200", "9300"}
    susp_count = int(df["account_code"].isin(susp_accts).sum())
    if susp_count > 0:
        indicators.append(FraudIndicator(
            name="Suspense/Clearing Account Usage",
            severity="HIGH",
            count=susp_count,
            description=f"{susp_count} entries posted to suspense or clearing accounts",
        ))

    # Large transactions
    large_n = int((df["risk_score"] >= 75).sum())
    if large_n > 0:
        indicators.append(FraudIndicator(
            name="Critical Risk Transactions",
            severity="CRITICAL",
            count=large_n,
            description=f"{large_n} transactions have a critical risk score (≥75)",
        ))

    # Out-of-hours
    ooh = int(df.get("feat_out_of_hours", pd.Series(dtype=int)).sum()) if "feat_out_of_hours" in df.columns else 0
    if ooh > 0:
        indicators.append(FraudIndicator(
            name="Out-of-Hours Posting",
            severity="LOW",
            count=ooh,
            description=f"{ooh} entries posted outside business hours (before 7am or after 8pm)",
        ))

    return indicators


def _check_ifrs_compliance(df: pd.DataFrame, kpi: KpiSummary) -> list:
    items = []
    n = len(df)

    # IAS 1: Debit/Credit balance — check at journal level for double-entry format
    if "_journal_balanced" in df.columns:
        imbal = int((~df["_journal_balanced"].astype(bool)).sum())
    else:
        both = (df["debit"] > 0) & (df["credit"] > 0)
        imbal = int(((df.loc[both, "debit"] - df.loc[both, "credit"]).abs()
                     > df.loc[both, "amount"] * 0.05).sum())
    bal_pct = round((1 - imbal / max(n, 1)) * 100, 1)
    items.append(ComplianceItem(
        standard="IAS 1",
        requirement="Presentation of Financial Statements – Debit/Credit Balance",
        status="COMPLIANT" if imbal == 0 else ("WARNING" if imbal < n * 0.02 else "NON_COMPLIANT"),
        details=f"{imbal} entries have debit/credit imbalances. Balance rate: {bal_pct}%",
        score=bal_pct,
    ))

    # IFRS 9: Impairment indicators (entries to suspense/clearing)
    susp = df["account_code"].isin({"9000", "9100"}).sum()
    susp_pct = round((1 - susp / max(n, 1)) * 100, 1)
    items.append(ComplianceItem(
        standard="IFRS 9",
        requirement="Financial Instruments – Suspense Account Management",
        status="COMPLIANT" if susp == 0 else ("WARNING" if susp < 20 else "NON_COMPLIANT"),
        details=f"{int(susp)} entries use suspense accounts. Compliance rate: {susp_pct}%",
        score=susp_pct,
    ))

    # IAS 8: Consistency – no large unexplained variances
    high_variance = (df.get("feat_monthly_change_pct", pd.Series(dtype=float)) > 2.0).sum() if "feat_monthly_change_pct" in df.columns else 0
    var_pct = round((1 - high_variance / max(n, 1)) * 100, 1)
    items.append(ComplianceItem(
        standard="IAS 8",
        requirement="Accounting Policies – Consistency of Accounting Estimates",
        status="COMPLIANT" if high_variance == 0 else ("WARNING" if high_variance < 10 else "NON_COMPLIANT"),
        details=f"{int(high_variance)} accounts show >200% month-over-month variance. Consistency rate: {var_pct}%",
        score=var_pct,
    ))

    # IAS 24: Related party – duplicate entries
    dups = int(df.get("feat_potential_duplicate", pd.Series(dtype=int)).sum()) if "feat_potential_duplicate" in df.columns else 0
    dup_pct = round((1 - dups / max(n, 1)) * 100, 1)
    items.append(ComplianceItem(
        standard="IAS 24",
        requirement="Related Party Disclosures – Duplicate Transaction Detection",
        status="COMPLIANT" if dups == 0 else ("WARNING" if dups < 5 else "NON_COMPLIANT"),
        details=f"{dups} potential duplicate entries detected. Uniqueness rate: {dup_pct}%",
        score=dup_pct,
    ))

    # IFRS 15: Revenue recognition – weekend posting to revenue accounts
    rev_weekend = df[
        (df["account_code"].str.startswith("4")) & (df.get("feat_is_weekend", 0) == 1)
    ].shape[0] if "feat_is_weekend" in df.columns else 0
    rev_pct = round((1 - rev_weekend / max(n, 1)) * 100, 1)
    items.append(ComplianceItem(
        standard="IFRS 15",
        requirement="Revenue from Contracts with Customers – Posting Controls",
        status="COMPLIANT" if rev_weekend == 0 else ("WARNING" if rev_weekend < 5 else "NON_COMPLIANT"),
        details=f"{rev_weekend} revenue entries posted on weekends. Control compliance: {rev_pct}%",
        score=rev_pct,
    ))

    return items


def _generate_recommendations(df, kpi, fraud_indicators, compliance, fraud_info=None) -> list:
    recs = []
    score = kpi.overall_risk_score

    if score >= 75:
        recs.append("URGENT: Freeze high-risk accounts and initiate immediate internal investigation.")
    elif score >= 50:
        recs.append("HIGH PRIORITY: Escalate suspicious transactions to internal audit for review.")

    if any(f.name == "Debit/Credit Imbalance" for f in fraud_indicators):
        recs.append("Investigate all debit/credit imbalances — these may indicate unauthorized adjustments.")

    if any(f.name == "Weekend Posting" and f.count > 10 for f in fraud_indicators):
        recs.append("Implement approval workflow for weekend and out-of-hours journal postings.")

    if any(f.name == "Duplicate Entries" for f in fraud_indicators):
        recs.append("Run a full duplicate-entry audit and implement system-level duplicate prevention controls.")

    if any(f.name == "Suspense/Clearing Account Usage" for f in fraud_indicators):
        recs.append("Review and clear all suspense account balances — aged items should be escalated to management.")

    non_compliant = [c for c in compliance if c.status == "NON_COMPLIANT"]
    if non_compliant:
        stds = ", ".join(c.standard for c in non_compliant)
        recs.append(f"Address IFRS non-compliance items ({stds}) before the next reporting period.")

    if kpi.compliance_percentage < 80:
        recs.append("Consider implementing automated pre-posting validation rules in the ERP system.")

    recs.append("Schedule quarterly fraud risk assessments and update rule engine weights based on audit findings.")
    recs.append("Enforce multi-level approval for transactions exceeding materiality thresholds.")

    if fraud_info:
        recall_pct = round(fraud_info["recall"] * 100, 1)
        uncaught = fraud_info["total_known"] - fraud_info["caught_high"]
        if uncaught > 0:
            recs.append(
                f"Internal validation: {uncaught} known fraud entries scored below the 50-point detection threshold. "
                "Review and tighten rule weights to close detection gaps."
            )
        if recall_pct >= 80:
            recs.append(
                f"Rule engine recall against ground-truth fraud cases is {recall_pct}%. "
                "Maintain current detection thresholds and monitor for drift."
            )

    return recs[:8]


def _generate_ai_summary(kpi, fraud_indicators, compliance, fraud_info=None) -> str:
    score = kpi.overall_risk_score
    level = kpi.risk_level
    total = kpi.total_entries
    suspicious = kpi.suspicious_transactions
    compliance_pct = kpi.compliance_percentage

    critical_indicators = [f for f in fraud_indicators if f.severity == "CRITICAL"]
    high_indicators = [f for f in fraud_indicators if f.severity == "HIGH"]
    non_compliant = [c for c in compliance if c.status == "NON_COMPLIANT"]

    summary = (
        f"QAID AI Analysis — Overall Risk Score: {score:.1f}/100 ({level}). "
        f"Analyzed {total:,} journal entries. "
        f"{suspicious} transactions ({suspicious/max(total,1)*100:.1f}%) flagged as suspicious. "
        f"IFRS Compliance Rate: {compliance_pct:.1f}%. "
    )

    if critical_indicators:
        names = ", ".join(f.name for f in critical_indicators)
        summary += f"Critical fraud indicators detected: {names}. Immediate action required. "

    if high_indicators:
        names = ", ".join(f.name for f in high_indicators[:3])
        summary += f"High-severity indicators: {names}. "

    if non_compliant:
        stds = ", ".join(c.standard for c in non_compliant)
        summary += f"IFRS non-compliance detected in: {stds}. "

    if score < 25:
        summary += "Overall financial data quality is high with minimal fraud risk."
    elif score < 50:
        summary += "Moderate risk profile detected. Targeted review of flagged entries is recommended."
    elif score < 75:
        summary += "Elevated fraud risk detected across multiple dimensions. Internal audit engagement is recommended."
    else:
        summary += "Critical risk level — potential systemic fraud or data integrity issues. Escalate to senior management immediately."

    if fraud_info:
        types_str = (", ".join(fraud_info["fraud_types"]) + ".") if fraud_info["fraud_types"] else ""
        summary += (
            f" Ground-truth validation: {fraud_info['caught_high']} of {fraud_info['total_known']} "
            f"known fraud entries detected (recall {fraud_info['recall']*100:.1f}%)."
        )
        if types_str:
            summary += f" Embedded fraud patterns include: {types_str}"

    return summary


def _row_to_entry_detail(row) -> EntryDetail:
    from services.rule_engine import get_rule_detail_for_entry
    rules_detail = get_rule_detail_for_entry(row)
    triggered_details = [
        TriggeredRule(
            rule_name=r["rule_name"],
            weight=r["weight"],
            description=r["description"],
        )
        for r in rules_detail
    ]

    feat_cols = [c for c in row.index if c.startswith("feat_")]
    features = {c.replace("feat_", ""): float(row[c]) for c in feat_cols if pd.notna(row[c])}

    risk_score = float(row.get("risk_score", 0))
    if risk_score >= 75:
        rec = "CRITICAL: Immediately freeze this entry pending investigation and notify the fraud control team."
    elif risk_score >= 50:
        rec = "HIGH: Escalate to internal audit. Obtain supporting documentation and approval records."
    elif risk_score >= 25:
        rec = "MEDIUM: Request additional documentation. Flag for next audit cycle review."
    else:
        rec = "LOW: Monitor for recurring patterns. No immediate action required."

    return EntryDetail(
        entry_id=str(row.get("entry_id", "")),
        account=str(row.get("account_code", "")),
        account_name=str(row.get("account_name", "")) if pd.notna(row.get("account_name")) else None,
        description=str(row.get("description", "")) if pd.notna(row.get("description")) else None,
        amount=float(row.get("amount", 0)),
        debit=float(row.get("debit", 0)),
        credit=float(row.get("credit", 0)),
        date=str(row.get("date", ""))[:10] if pd.notna(row.get("date")) else "",
        user=str(row.get("user", "")) if pd.notna(row.get("user")) else None,
        risk_score=round(float(row.get("risk_score", 0)), 2),
        fraud_probability=round(float(row.get("fraud_probability", 0)), 4),
        risk_level=str(row.get("risk_level", "LOW")),
        triggered_rules_detail=triggered_details,
        ml_score=round(float(row.get("ml_score", 0)), 2),
        rule_score=round(float(row.get("rule_score", 0)), 2),
        recommendation=rec,
        features=features,
    )
