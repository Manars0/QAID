from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class KpiSummary(BaseModel):
    overall_risk_score: float
    risk_level: str  # LOW / MEDIUM / HIGH / CRITICAL
    total_entries: int
    flagged_accounts: int
    suspicious_transactions: int
    compliance_percentage: float
    ai_confidence: float


class RiskDistribution(BaseModel):
    level: str
    count: int
    percentage: float
    color: str


class RiskTrend(BaseModel):
    period: str
    avg_risk_score: float
    entry_count: int
    flagged_count: int


class RiskEntry(BaseModel):
    entry_id: str
    account: str
    account_name: Optional[str] = None
    description: Optional[str] = None
    amount: float
    debit: float
    credit: float
    date: str
    user: Optional[str] = None
    risk_score: float
    fraud_probability: float
    risk_level: str
    triggered_rules: List[str]
    ml_score: float
    rule_score: float


class RiskAccount(BaseModel):
    account_code: str
    account_name: str
    total_entries: int
    avg_risk_score: float
    risk_level: str
    total_amount: float
    max_single_amount: float


class ChangedAccount(BaseModel):
    account_code: str
    account_name: str
    monthly_change_pct: float
    current_month: float
    previous_month: float


class FraudIndicator(BaseModel):
    name: str
    severity: str  # LOW / MEDIUM / HIGH / CRITICAL
    count: int
    description: str


class ComplianceItem(BaseModel):
    standard: str
    requirement: str
    status: str  # COMPLIANT / NON_COMPLIANT / WARNING
    details: str
    score: float


class ValidationIssue(BaseModel):
    type: str
    severity: str
    count: int
    description: str


class TriggeredRule(BaseModel):
    rule_name: str
    weight: float
    description: str


class EntryDetail(BaseModel):
    entry_id: str
    account: str
    account_name: Optional[str] = None
    description: Optional[str] = None
    amount: float
    debit: float
    credit: float
    date: str
    user: Optional[str] = None
    risk_score: float
    fraud_probability: float
    risk_level: str
    triggered_rules_detail: List[TriggeredRule]
    ml_score: float
    rule_score: float
    recommendation: str
    features: Dict[str, float]


class AnalysisResult(BaseModel):
    session_id: str
    file_name: str
    kpi_summary: KpiSummary
    risk_distribution: List[RiskDistribution]
    risk_trend: List[RiskTrend]
    high_risk_entries: List[RiskEntry]
    high_risk_accounts: List[RiskAccount]
    top_changed_accounts: List[ChangedAccount]
    fraud_indicators: List[FraudIndicator]
    compliance_items: List[ComplianceItem]
    recommendations: List[str]
    ai_summary: str
    validation_issues: List[ValidationIssue]
    created_at: str
    total_entries_analyzed: int
