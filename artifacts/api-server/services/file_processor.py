"""
ERP Dataset Loader — QAID
Handles: single CSV, single Excel, or multi-table ERP ZIP.

Public API
----------
process_uploaded_file(content, filename)
    -> (journal_df, file_label, fraud_labels_df | None)

Both Demo Mode and Upload Mode call this function.
The ONLY difference is where `content` + `filename` come from.
"""
from __future__ import annotations

import io
import zipfile
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Table fingerprints: minimum column set required to identify each table type.
# Column names are matched after normalising to lowercase_underscore.
# ─────────────────────────────────────────────────────────────────────────────
TABLE_FINGERPRINTS: Dict[str, set] = {
    # Unique: has 'fraud' column → checked first
    "fraud_labels":      {"journal_id", "fraud"},
    # Unique: has debit + credit + account_code at line level
    "journal_lines":     {"journal_id", "account_code", "debit", "credit"},
    # Unique: has posting_date + created_by (header-level)
    "journal_header":    {"journal_id", "posting_date", "created_by"},
    "chart_of_accounts": {"account_code", "account_name", "account_type"},
    "users":             {"user_id", "role"},
    "approval_log":      {"journal_id", "approval_status"},
    "audit_log":         {"journal_id", "action", "audit_id"},
    "payment_entries":   {"payment_id", "journal_id", "payment_method"},
    "purchase_invoices": {"invoice_id", "journal_id", "vendor"},
    "sales_invoices":    {"invoice_id", "journal_id", "customer"},
    "companies":         {"company_id", "company_name"},
    "cost_centers":      {"cost_center_id", "cost_center_name"},
    "currencies":        {"currency_code", "exchange_rate_to_sar"},
}

# Detection order — more specific fingerprints first
DETECTION_PRIORITY = [
    "fraud_labels", "journal_lines", "journal_header",
    "chart_of_accounts", "users", "approval_log", "audit_log",
    "payment_entries", "purchase_invoices", "sales_invoices",
    "companies", "cost_centers", "currencies",
]

# Standard column aliases for the flat / fallback path
COLUMN_ALIASES = {
    "entry_id":     ["entry_id", "je_id", "journal_id", "id", "line_id", "ref", "reference"],
    "date":         ["date", "posting_date", "entry_date", "transaction_date", "doc_date"],
    "account_code": ["account_code", "account", "acct", "account_no", "gl_account"],
    "account_name": ["account_name", "account_description", "acct_name"],
    "debit":        ["debit", "dr", "debit_amount", "debit_amt"],
    "credit":       ["credit", "cr", "credit_amount", "credit_amt"],
    "amount":       ["amount", "net_amount", "value", "transaction_amount", "total_amount"],
    "user":         ["user", "posted_by", "created_by", "user_id", "clerk", "preparer"],
    "description":  ["description", "narration", "memo", "remarks", "particulars", "text"],
    "period":       ["period", "posting_period", "fiscal_period", "accounting_period", "month"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _norm(col: str) -> str:
    """Normalise a column name to lowercase_underscore."""
    return col.strip().lower().replace(" ", "_").replace("-", "_")


def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: _norm(c) for c in df.columns})


def _detect_table_type(df: pd.DataFrame) -> Optional[str]:
    cols = {_norm(c) for c in df.columns}
    for table_type in DETECTION_PRIORITY:
        if TABLE_FINGERPRINTS[table_type].issubset(cols):
            return table_type
    return None


def _read_csv(content: bytes, name: str) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(content), encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode CSV '{name}'")


def _read_excel(content: bytes, name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"Cannot read Excel '{name}': {exc}") from exc


def _read_file(content: bytes, name: str) -> pd.DataFrame:
    lower = name.lower()
    if lower.endswith((".xlsx", ".xls")):
        return _read_excel(content, name)
    if lower.endswith(".csv"):
        return _read_csv(content, name)
    raise ValueError(f"Unsupported format: {name}")


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def process_uploaded_file(
    content: bytes, filename: str
) -> Tuple[pd.DataFrame, str, Optional[pd.DataFrame]]:
    """
    Process an uploaded file (CSV, Excel, or ZIP).

    Returns
    -------
    journal_df : pd.DataFrame
        Standardised journal-line records ready for the analysis pipeline.
    file_label : str
        Human-readable label derived from the filename.
    fraud_labels : pd.DataFrame | None
        Ground-truth fraud table when present (ERP ZIPs only).
        Used ONLY inside the backend — never exposed to the frontend.
    """
    lower = filename.lower()
    if lower.endswith(".zip"):
        return _process_zip(content, filename)

    df = _norm_cols(_read_file(content, filename))
    return build_journal_df(df), filename, None


# ─────────────────────────────────────────────────────────────────────────────
# ZIP processing
# ─────────────────────────────────────────────────────────────────────────────

def _process_zip(
    content: bytes, zip_filename: str
) -> Tuple[pd.DataFrame, str, Optional[pd.DataFrame]]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid ZIP file") from exc

    tables: Dict[str, pd.DataFrame] = {}
    flat_dfs: list[pd.DataFrame] = []

    with zf:
        for info in zf.infolist():
            base = info.filename.split("/")[-1]
            if not base or base.startswith((".", "__")):
                continue
            if not base.lower().endswith((".csv", ".xlsx", ".xls")):
                continue
            try:
                raw = zf.read(info.filename)
                df = _norm_cols(_read_file(raw, base))
                table_type = _detect_table_type(df)
                if table_type and table_type not in tables:
                    tables[table_type] = df
                else:
                    flat_dfs.append(df)  # unknown / duplicate → flat pool
            except Exception:
                continue  # skip unreadable files without crashing

    if not tables and not flat_dfs:
        raise ValueError("No valid accounting files found in ZIP")

    label = zip_filename.rsplit(".zip", 1)[0]

    # ── ERP multi-table path ─────────────────────────────────────────────────
    if "journal_lines" in tables:
        journal_df, fraud_labels = _build_erp_journal_df(tables)
        return journal_df, label, fraud_labels

    # ── Fallback: flat concat (e.g. a ZIP of a single GL export) ────────────
    all_dfs = list(tables.values()) + flat_dfs
    merged = pd.concat(all_dfs, ignore_index=True)
    return build_journal_df(merged), label, None


# ─────────────────────────────────────────────────────────────────────────────
# ERP multi-table merge
# ─────────────────────────────────────────────────────────────────────────────

def _build_erp_journal_df(
    tables: Dict[str, pd.DataFrame],
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Merge ERP tables into a flat, line-level journal dataframe.
    Returns (journal_df, fraud_labels_df | None).
    """
    lines = tables["journal_lines"].copy()
    header = tables.get("journal_header")
    coa = tables.get("chart_of_accounts")
    users = tables.get("users")
    approval = tables.get("approval_log")
    fraud_raw = tables.get("fraud_labels")

    # ── 1. Merge Journal Header → Lines ──────────────────────────────────────
    if header is not None:
        keep = [c for c in (
            "journal_id", "posting_date", "posting_time", "posting_period",
            "voucher_type", "source_module", "created_by", "status", "company",
            "fiscal_year", "currency",
        ) if c in header.columns]
        hdr_slim = header[keep].drop_duplicates("journal_id")
        lines = lines.merge(hdr_slim, on="journal_id", how="left", suffixes=("", "_hdr"))

    # ── 2. Composite entry_id (journal + line) ────────────────────────────────
    if "line_number" in lines.columns:
        lines["entry_id"] = (
            lines["journal_id"].astype(str)
            + "_L"
            + lines["line_number"].astype(str).str.zfill(3)
        )
    else:
        lines["entry_id"] = lines["journal_id"].astype(str)

    # ── 3. Rename to standard column names ───────────────────────────────────
    renames: Dict[str, str] = {}
    if "posting_date" in lines.columns and "date" not in lines.columns:
        renames["posting_date"] = "date"
    if "created_by" in lines.columns and "user" not in lines.columns:
        renames["created_by"] = "user"
    if "posting_period" in lines.columns and "period" not in lines.columns:
        renames["posting_period"] = "period"
    if renames:
        lines = lines.rename(columns=renames)

    # ── 3b. Combine date + posting_time to get correct posting hour ───────────
    # Journal_Header stores date and time in separate columns. Combine them so
    # feat_posting_hour reflects the actual intra-day time (not midnight default).
    if "posting_time" in lines.columns and "date" in lines.columns:
        try:
            combined = pd.to_datetime(
                lines["date"].astype(str).str[:10] + " " + lines["posting_time"].astype(str),
                errors="coerce",
            )
            # Only overwrite where the combination succeeded
            valid = combined.notna()
            lines.loc[valid, "date"] = combined[valid]
        except Exception:
            pass  # keep original date if combination fails

    # ── 3c. Compute journal-level debit/credit balance flag ───────────────────
    # In double-entry accounting each LINE has either debit OR credit (not both).
    # Balance must be checked at the JOURNAL level: sum(debit) == sum(credit).
    if "journal_id" in lines.columns:
        jbal = (
            lines.groupby("journal_id")
            .agg(_j_debit=("debit", "sum"), _j_credit=("credit", "sum"))
            .reset_index()
        )
        jbal["_journal_imbalance_pct"] = (
            (jbal["_j_debit"] - jbal["_j_credit"]).abs()
            / jbal[["_j_debit", "_j_credit"]].max(axis=1).clip(lower=1)
        )
        jbal["_journal_balanced"] = jbal["_journal_imbalance_pct"] <= 0.01
        lines = lines.merge(
            jbal[["journal_id", "_journal_balanced", "_journal_imbalance_pct"]],
            on="journal_id", how="left",
        )
        lines["_journal_balanced"] = lines["_journal_balanced"].fillna(True)

    # ── 4. Enrich from Chart of Accounts ─────────────────────────────────────
    if coa is not None and "account_code" in coa.columns:
        coa_cols = [c for c in ("account_code", "account_type", "normal_balance", "is_active") if c in coa.columns]
        coa_slim = coa[coa_cols].copy()
        coa_slim["account_code"] = coa_slim["account_code"].astype(str).str.strip()
        lines["account_code"] = lines["account_code"].astype(str).str.strip()
        lines = lines.merge(
            coa_slim.drop_duplicates("account_code"),
            on="account_code", how="left", suffixes=("", "_coa"),
        )

    # ── 5. Enrich from Users ─────────────────────────────────────────────────
    if users is not None and "user_id" in users.columns:
        u_cols = [c for c in ("user_id", "user_name", "role", "department", "approval_limit") if c in users.columns]
        users_slim = users[u_cols].drop_duplicates("user_id").rename(columns={"user_id": "user"})
        if "user" in lines.columns:
            lines = lines.merge(users_slim, on="user", how="left", suffixes=("", "_usr"))
            if "role" in lines.columns:
                lines["user_role"] = lines["role"]

    # ── 6. Enrich from Approval Log ──────────────────────────────────────────
    if approval is not None and "journal_id" in approval.columns and "approval_status" in approval.columns:
        agg = (
            approval.groupby("journal_id")
            .agg(
                approval_count=("approval_status", "count"),
                is_approved=(
                    "approval_status",
                    lambda x: x.str.lower().str.contains("approved", na=False).any(),
                ),
            )
            .reset_index()
        )
        lines = lines.merge(agg, on="journal_id", how="left")
        lines["has_approval"] = lines["is_approved"].fillna(False).infer_objects(copy=False).astype(bool)
        lines["approval_count"] = lines["approval_count"].fillna(0).astype(int)
    else:
        lines["has_approval"] = True
        lines["approval_count"] = 0

    # ── 7. Fraud Labels — internal only, never serialised ────────────────────
    fraud_labels: Optional[pd.DataFrame] = None
    if fraud_raw is not None and "fraud" in fraud_raw.columns:
        fraud_labels = fraud_raw.copy()
        fraud_labels["is_fraud"] = (
            fraud_labels["fraud"].astype(str).str.lower().isin(["yes", "true", "1"])
        )
        if "journal_id" in fraud_labels.columns:
            fraud_map = fraud_labels.set_index("journal_id")["is_fraud"].to_dict()
            lines["_known_fraud"] = lines["journal_id"].astype(str).map(fraud_map).fillna(False)
        else:
            lines["_known_fraud"] = False
    else:
        lines["_known_fraud"] = False

    return build_journal_df(lines), fraud_labels


# ─────────────────────────────────────────────────────────────────────────────
# Standard normaliser (flat / fallback path)
# ─────────────────────────────────────────────────────────────────────────────

def _apply_aliases(df: pd.DataFrame) -> pd.DataFrame:
    rename_map: Dict[str, str] = {}
    for std, aliases in COLUMN_ALIASES.items():
        if std in df.columns:
            continue
        for alias in aliases:
            if alias in df.columns:
                rename_map[alias] = std
                break
    return df.rename(columns=rename_map)


def build_journal_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise a journal-entry dataframe.
    Ensures all columns required by the analysis pipeline exist and are typed.
    Safe to call on already-merged ERP data or on a raw single-file export.
    """
    df = df.copy()
    df = _apply_aliases(df)

    # entry_id
    if "entry_id" not in df.columns:
        df["entry_id"] = [f"JE{i + 1:06d}" for i in range(len(df))]
    else:
        df["entry_id"] = df["entry_id"].astype(str)

    # date
    if "date" not in df.columns:
        df["date"] = pd.Timestamp.now()
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").fillna(pd.Timestamp.now())

    # account_code
    if "account_code" not in df.columns:
        df["account_code"] = "9999"
    df["account_code"] = df["account_code"].astype(str).str.strip()

    # account_name
    if "account_name" not in df.columns:
        df["account_name"] = "Unknown Account"

    # amounts
    for col in ("debit", "credit", "amount"):
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).abs()

    # amount from debit/credit when zero
    mask = df["amount"] == 0
    df.loc[mask, "amount"] = df.loc[mask, ["debit", "credit"]].max(axis=1)

    # debit/credit from amount when both zero
    mask2 = (df["debit"] == 0) & (df["credit"] == 0)
    df.loc[mask2, "debit"] = df.loc[mask2, "amount"]
    df.loc[mask2, "credit"] = df.loc[mask2, "amount"]

    # user
    if "user" not in df.columns:
        df["user"] = "system"

    # description
    if "description" not in df.columns:
        df["description"] = ""

    # period (derive from date if not already set)
    if "period" not in df.columns:
        df["period"] = df["date"].dt.strftime("%Y-%m")

    # internal backend flag — never serialised
    if "_known_fraud" not in df.columns:
        df["_known_fraud"] = False

    return df
