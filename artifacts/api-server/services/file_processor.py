"""
Process uploaded ERP files: Excel, CSV, ZIP.
Detect and load: General Ledger, Journal Entries, Chart of Accounts, etc.
"""
import io
import zipfile
import pandas as pd
from typing import Dict, Tuple, Optional


# Keywords to identify file types
FILE_TYPE_KEYWORDS = {
    "journal_entries": ["journal", "je", "journal_entry", "gl_detail", "ledger_detail"],
    "general_ledger": ["general_ledger", "gl", "trial_balance", "tb"],
    "chart_of_accounts": ["chart", "coa", "accounts", "account_list"],
    "vendors": ["vendor", "supplier", "creditor"],
    "customers": ["customer", "client", "debtor", "receivable"],
}

# Standard column name mappings
COLUMN_MAPPINGS = {
    # Entry ID
    "entry_id": ["entry_id", "je_id", "journal_id", "id", "line_id", "ref", "reference"],
    # Date
    "date": ["date", "posting_date", "entry_date", "transaction_date", "doc_date"],
    # Account
    "account_code": ["account_code", "account", "acct", "account_no", "gl_account", "ledger_account"],
    "account_name": ["account_name", "account_description", "description", "acct_name"],
    # Amounts
    "debit": ["debit", "dr", "debit_amount", "debit_amt"],
    "credit": ["credit", "cr", "credit_amount", "credit_amt"],
    "amount": ["amount", "net_amount", "value", "transaction_amount"],
    # User
    "user": ["user", "posted_by", "created_by", "user_id", "clerk", "preparer"],
    # Description
    "description": ["description", "narration", "memo", "remarks", "particulars", "text"],
    # Period
    "period": ["period", "fiscal_period", "accounting_period", "month"],
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe columns to standard names."""
    lower_cols = {c: c.lower().strip().replace(" ", "_").replace("-", "_") for c in df.columns}
    df = df.rename(columns=lower_cols)

    rename_map = {}
    for std_name, aliases in COLUMN_MAPPINGS.items():
        if std_name in df.columns:
            continue
        for alias in aliases:
            if alias in df.columns:
                rename_map[alias] = std_name
                break

    df = df.rename(columns=rename_map)
    return df


def detect_file_type(filename: str) -> str:
    """Detect the file type based on filename keywords."""
    name_lower = filename.lower().replace(" ", "_").replace("-", "_")
    for file_type, keywords in FILE_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return file_type
    return "journal_entries"  # default


def read_excel_file(content: bytes, filename: str) -> pd.DataFrame:
    """Read an Excel file and return a DataFrame."""
    try:
        # Try reading first sheet
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        return normalize_columns(df)
    except Exception as e:
        raise ValueError(f"Cannot read Excel file '{filename}': {e}")


def read_csv_file(content: bytes, filename: str) -> pd.DataFrame:
    """Read a CSV file and return a DataFrame."""
    try:
        for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                return normalize_columns(df)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode CSV file '{filename}'")
    except Exception as e:
        raise ValueError(f"Cannot read CSV file '{filename}': {e}")


def process_uploaded_file(content: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
    """
    Process an uploaded file (Excel, CSV, or ZIP).
    Returns: (journal_entries_df, file_name_label)
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".zip"):
        return process_zip_file(content, filename)
    elif filename_lower.endswith((".xlsx", ".xls")):
        df = read_excel_file(content, filename)
        return build_journal_df(df), filename
    elif filename_lower.endswith(".csv"):
        df = read_csv_file(content, filename)
        return build_journal_df(df), filename
    else:
        raise ValueError(f"Unsupported file type: {filename}. Supported: .xlsx, .csv, .zip")


def process_zip_file(content: bytes, zip_filename: str) -> Tuple[pd.DataFrame, str]:
    """Extract ZIP and merge all detected accounting files."""
    dfs = []
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for name in zf.namelist():
                name_lower = name.lower()
                if name_lower.endswith((".xlsx", ".xls", ".csv")) and not name.startswith("__"):
                    try:
                        file_content = zf.read(name)
                        base_name = name.split("/")[-1]
                        if name_lower.endswith((".xlsx", ".xls")):
                            df = read_excel_file(file_content, base_name)
                        else:
                            df = read_csv_file(file_content, base_name)
                        dfs.append(df)
                    except Exception:
                        continue
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file")

    if not dfs:
        raise ValueError("No valid accounting files found in ZIP")

    # Merge all dataframes
    merged = pd.concat(dfs, ignore_index=True)
    return build_journal_df(merged), zip_filename


def build_journal_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a standardized journal entries DataFrame from raw input.
    Ensures all required columns exist.
    """
    import numpy as np

    # Ensure entry_id
    if "entry_id" not in df.columns:
        df["entry_id"] = [f"JE{i+1:06d}" for i in range(len(df))]
    else:
        df["entry_id"] = df["entry_id"].astype(str)

    # Ensure date
    if "date" not in df.columns:
        df["date"] = pd.Timestamp.now()
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["date"] = df["date"].fillna(pd.Timestamp.now())

    # Ensure account_code
    if "account_code" not in df.columns:
        if "account" in df.columns:
            df["account_code"] = df["account"].astype(str)
        else:
            df["account_code"] = "9999"

    df["account_code"] = df["account_code"].astype(str).str.strip()

    # Ensure account_name
    if "account_name" not in df.columns:
        df["account_name"] = "Unknown Account"

    # Ensure amounts
    for col in ["debit", "credit", "amount"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).abs()

    # If amount is 0, derive from debit/credit
    mask = df["amount"] == 0
    df.loc[mask, "amount"] = df.loc[mask, ["debit", "credit"]].max(axis=1)

    # Ensure debit/credit from amount if both zero
    mask2 = (df["debit"] == 0) & (df["credit"] == 0)
    df.loc[mask2, "debit"] = df.loc[mask2, "amount"]
    df.loc[mask2, "credit"] = df.loc[mask2, "amount"]

    # Ensure user
    if "user" not in df.columns:
        df["user"] = "system"

    # Ensure description
    if "description" not in df.columns:
        df["description"] = ""

    # Ensure period
    df["period"] = df["date"].dt.strftime("%Y-%m")

    # Add _is_fraud placeholder
    df["_is_fraud"] = False

    return df
