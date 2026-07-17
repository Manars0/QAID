import React from "react"
import { useAnalysis } from "../../contexts/AnalysisContext"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"
import { Shield, FileText, AlertTriangle, AlertOctagon, CheckCircle, BrainCircuit } from "lucide-react"

export function KPICards() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]

  if (!analysisResult) return null

  const { kpi_summary } = analysisResult

  const kpis = [
    {
      title: t.risk_score,
      value: kpi_summary.overall_risk_score.toFixed(1),
      icon: Shield,
      color: "text-primary",
      desc: `Level: ${kpi_summary.risk_level}`
    },
    {
      title: t.journal_entries,
      value: kpi_summary.total_entries.toLocaleString(),
      icon: FileText,
      color: "text-muted-foreground",
      desc: "Total analyzed"
    },
    {
      title: t.flagged_accounts,
      value: kpi_summary.flagged_accounts.toLocaleString(),
      icon: AlertTriangle,
      color: "text-amber-500",
      desc: "Requires review"
    },
    {
      title: t.suspicious_transactions,
      value: kpi_summary.suspicious_transactions.toLocaleString(),
      icon: AlertOctagon,
      color: "text-destructive",
      desc: "High probability"
    },
    {
      title: t.compliance_pct,
      value: `${kpi_summary.compliance_percentage}%`,
      icon: CheckCircle,
      color: "text-emerald-500",
      desc: "IFRS Standards"
    },
    {
      title: t.ai_confidence,
      value: `${kpi_summary.ai_confidence}%`,
      icon: BrainCircuit,
      color: "text-blue-500",
      desc: "Model accuracy"
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
      {kpis.map((kpi, i) => (
        <Card key={i} className="border-l-4" style={{ borderLeftColor: `var(--${kpi.color.replace('text-', '')})` }}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {kpi.title}
            </CardTitle>
            <kpi.icon className={`h-4 w-4 ${kpi.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpi.value}</div>
            <p className="text-xs text-muted-foreground mt-1">{kpi.desc}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
