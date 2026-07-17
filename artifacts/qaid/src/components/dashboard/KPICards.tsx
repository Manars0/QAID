import React from "react"
import { useAnalysis } from "../../contexts/AnalysisContext"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { Shield, FileText, AlertOctagon, CheckCircle2, Database, Copy } from "lucide-react"

const RISK_CARD_STYLES: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  LOW:      { bg: "bg-emerald-500/5", border: "border-emerald-500/25", text: "text-emerald-600 dark:text-emerald-400", badge: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" },
  MEDIUM:   { bg: "bg-amber-500/5",   border: "border-amber-500/25",   text: "text-amber-600  dark:text-amber-400",   badge: "bg-amber-500/10  text-amber-700  dark:text-amber-300"  },
  HIGH:     { bg: "bg-orange-500/5",  border: "border-orange-500/25",  text: "text-orange-600 dark:text-orange-400", badge: "bg-orange-500/10 text-orange-700 dark:text-orange-300" },
  CRITICAL: { bg: "bg-red-500/5",     border: "border-red-500/25",     text: "text-red-600    dark:text-red-400",    badge: "bg-red-500/10    text-red-700    dark:text-red-300"    },
}

export function KPICards() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]

  if (!analysisResult) return null

  const { kpi_summary, fraud_indicators, validation_issues } = analysisResult

  const riskStyles = RISK_CARD_STYLES[kpi_summary.risk_level] ?? RISK_CARD_STYLES.LOW

  // Data Quality derived stats
  const duplicates = fraud_indicators.find((f: any) =>
    f.name.toLowerCase().includes('duplicate')
  )?.count ?? 0

  const issueCount = (validation_issues ?? []).reduce(
    (sum: number, v: any) => sum + (v.count ?? 0), 0
  )

  const cleanRate = kpi_summary.total_entries > 0
    ? (((kpi_summary.total_entries - kpi_summary.suspicious_transactions) / kpi_summary.total_entries) * 100).toFixed(1)
    : "100.0"

  // Compliance label
  const complianceItems: any[] = analysisResult.compliance_items ?? []
  const metCount = complianceItems.filter((c: any) => c.status === 'COMPLIANT').length

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">

      {/* 1 — Risk Score */}
      <div className={`relative rounded-xl border p-5 flex flex-col gap-3 col-span-1 ${riskStyles.bg} ${riskStyles.border}`}>
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">{t.risk_score}</span>
          <Shield className={`h-4 w-4 ${riskStyles.text}`} />
        </div>
        <div className="flex items-end gap-3">
          <span className={`text-4xl font-bold tabular-nums leading-none ${riskStyles.text}`}>
            {kpi_summary.overall_risk_score.toFixed(1)}
          </span>
          <span className="text-sm text-muted-foreground mb-1">/&nbsp;100</span>
        </div>
        <span className={`self-start text-xs font-semibold px-2 py-0.5 rounded-full ${riskStyles.badge}`}>
          {t[kpi_summary.risk_level.toLowerCase() as keyof typeof t] ?? kpi_summary.risk_level}
        </span>
      </div>

      {/* 2 — Journal Entries */}
      <div className="rounded-xl border bg-card p-5 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">{t.journal_entries}</span>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </div>
        <span className="text-4xl font-bold tabular-nums leading-none">
          {kpi_summary.total_entries.toLocaleString()}
        </span>
        <span className="text-xs text-muted-foreground">Total {t.entries}</span>
      </div>

      {/* 3 — Suspicious Transactions */}
      <div className="rounded-xl border bg-card p-5 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">{t.suspicious_transactions}</span>
          <AlertOctagon className="h-4 w-4 text-destructive" />
        </div>
        <span className="text-4xl font-bold tabular-nums leading-none text-destructive">
          {kpi_summary.suspicious_transactions.toLocaleString()}
        </span>
        <span className="text-xs text-muted-foreground">
          {kpi_summary.total_entries > 0
            ? `${((kpi_summary.suspicious_transactions / kpi_summary.total_entries) * 100).toFixed(1)}% ${t.of_total}`
            : `0% ${t.of_total}`}
        </span>
      </div>

      {/* 4 — Compliance Rate */}
      <div className="rounded-xl border bg-card p-5 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">{t.compliance_pct}</span>
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
        </div>
        <span className={`text-4xl font-bold tabular-nums leading-none ${
          kpi_summary.compliance_percentage >= 90
            ? "text-emerald-600 dark:text-emerald-400"
            : kpi_summary.compliance_percentage >= 70
              ? "text-amber-600 dark:text-amber-400"
              : "text-destructive"
        }`}>
          {kpi_summary.compliance_percentage.toFixed(1)}%
        </span>
        {complianceItems.length > 0 && (
          <span className="text-xs text-muted-foreground">
            {metCount} / {complianceItems.length} {t.standards_met}
          </span>
        )}
      </div>

      {/* 5 — Data Quality */}
      <div className="rounded-xl border bg-card p-5 flex flex-col gap-3 col-span-2 md:col-span-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">{t.data_quality}</span>
          <Database className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="flex items-end gap-2">
          <span className="text-4xl font-bold tabular-nums leading-none text-primary">{cleanRate}%</span>
          <span className="text-xs text-muted-foreground mb-1">{t.clean_rate}</span>
        </div>
        <div className="grid grid-cols-3 gap-2 pt-1 border-t border-border/60">
          <div className="flex flex-col">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{t.processed_rows}</span>
            <span className="text-sm font-semibold tabular-nums">{kpi_summary.total_entries.toLocaleString()}</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1">
              <Copy className="h-2.5 w-2.5 text-amber-500" />
              <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{t.duplicate_rows}</span>
            </div>
            <span className="text-sm font-semibold tabular-nums">{duplicates.toLocaleString()}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{t.data_issues}</span>
            <span className={`text-sm font-semibold tabular-nums ${issueCount > 0 ? "text-destructive" : "text-emerald-600 dark:text-emerald-400"}`}>
              {issueCount === 0 ? "None" : issueCount.toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
