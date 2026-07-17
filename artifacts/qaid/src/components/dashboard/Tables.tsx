import React, { useState } from "react"
import { useAnalysis } from "../../contexts/AnalysisContext"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { useGetAnalysisEntries, getGetAnalysisEntriesQueryKey } from "@workspace/api-client-react"
import { Badge } from "../ui/badge"
import { EntryDetailModal } from "./EntryDetailModal"
import {
  Calendar, CircleDot, Copy, Moon, Scale, UserMinus, Users,
  TrendingUp, Banknote, Archive, AlertTriangle, ShieldAlert,
  CheckCircle2, AlertCircle, XCircle, ChevronDown, ChevronRight,
  ArrowUpRight, Loader2,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getRiskBadge(level: string): "success" | "warning" | "danger" | "critical" | "default" {
  switch (level.toUpperCase()) {
    case "LOW":      return "success"
    case "MEDIUM":   return "warning"
    case "HIGH":     return "danger"
    case "CRITICAL": return "critical"
    default:         return "default"
  }
}

function getFraudIcon(name: string): LucideIcon {
  const n = name.toLowerCase()
  if (n.includes("weekend"))                                return Calendar
  if (n.includes("round") || n.includes("suspicious"))     return CircleDot
  if (n.includes("duplicate"))                             return Copy
  if (n.includes("out-of-hours") || n.includes("hours"))  return Moon
  if (n.includes("imbalance") || n.includes("debit"))     return Scale
  if (n.includes("inactive"))                             return UserMinus
  if (n.includes("high user") || n.includes("user"))      return Users
  if (n.includes("monthly") || n.includes("variance"))    return TrendingUp
  if (n.includes("large") || n.includes("amount"))        return Banknote
  if (n.includes("suspense"))                             return Archive
  if (n.includes("critical"))                             return AlertTriangle
  return ShieldAlert
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "text-red-600 dark:text-red-400 bg-red-500/10",
  HIGH:     "text-orange-600 dark:text-orange-400 bg-orange-500/10",
  MEDIUM:   "text-amber-600 dark:text-amber-400 bg-amber-500/10",
  LOW:      "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10",
}

// ─── IFRS status → human label ────────────────────────────────────────────────
interface ComplianceConfig {
  label: string
  icon: LucideIcon
  textCls: string
  bgCls: string
  borderCls: string
  badgeBg: string
  impactLevel: string
}

function getComplianceConfig(status: string, score: number): ComplianceConfig {
  if (status === "COMPLIANT") {
    return {
      label: "Compliant",
      icon: CheckCircle2,
      textCls: "text-emerald-600 dark:text-emerald-400",
      bgCls: "bg-emerald-500/5",
      borderCls: "border-emerald-500/20",
      badgeBg: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
      impactLevel: "None",
    }
  }
  if (status === "WARNING" || (status === "NON_COMPLIANT" && score >= 97)) {
    return {
      label: "Needs Review",
      icon: AlertCircle,
      textCls: "text-amber-600 dark:text-amber-400",
      bgCls: "bg-amber-500/5",
      borderCls: "border-amber-500/20",
      badgeBg: "bg-amber-500/10 text-amber-700 dark:text-amber-300",
      impactLevel: "Low",
    }
  }
  if (status === "NON_COMPLIANT" && score >= 90) {
    return {
      label: "Potential Issue",
      icon: AlertTriangle,
      textCls: "text-orange-600 dark:text-orange-400",
      bgCls: "bg-orange-500/5",
      borderCls: "border-orange-500/20",
      badgeBg: "bg-orange-500/10 text-orange-700 dark:text-orange-300",
      impactLevel: "Medium",
    }
  }
  return {
    label: "High Risk",
    icon: XCircle,
    textCls: "text-red-600 dark:text-red-400",
    bgCls: "bg-red-500/5",
    borderCls: "border-red-500/20",
    badgeBg: "bg-red-500/10 text-red-700 dark:text-red-300",
    impactLevel: "High",
  }
}

// ─── Section Label ─────────────────────────────────────────────────────────────
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold tracking-[0.15em] uppercase text-muted-foreground mb-4">
      {children}
    </p>
  )
}

// ─── 1. Fraud Indicators ──────────────────────────────────────────────────────
function FraudIndicatorsSection() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]
  if (!analysisResult) return null

  const indicators: any[] = analysisResult.fraud_indicators ?? []
  if (indicators.length === 0) return null

  const severityOrder: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }
  const sorted = [...indicators].sort(
    (a, b) => (severityOrder[a.severity] ?? 4) - (severityOrder[b.severity] ?? 4)
  )

  return (
    <section>
      <SectionLabel>{t.fraud_indicators}</SectionLabel>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {sorted.map((ind: any, i: number) => {
          const Icon = getFraudIcon(ind.name)
          const colorCls = SEVERITY_COLORS[ind.severity] ?? SEVERITY_COLORS.LOW
          return (
            <div
              key={i}
              className="rounded-xl border bg-card p-4 sm:p-5 flex flex-col gap-3 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between gap-2">
                <div className={`p-2 rounded-lg ${colorCls}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className={`text-2xl font-bold tabular-nums ${colorCls.split(" ")[0]}`}>
                  {ind.count.toLocaleString()}
                </span>
              </div>
              <p className="text-sm font-semibold leading-tight">{ind.name}</p>
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                {ind.description}
              </p>
              <span className={`self-start text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${colorCls}`}>
                {ind.severity}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}

// ─── 2. High Risk Journal Entries ─────────────────────────────────────────────
function HighRiskEntriesSection() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)

  const sessionId = analysisResult?.session_id
  const { data: entries, isLoading } = useGetAnalysisEntries(sessionId!, {
    query: {
      enabled: !!sessionId,
      queryKey: getGetAnalysisEntriesQueryKey(sessionId!),
    },
  })

  if (!analysisResult) return null

  const displayEntries = showAll ? (entries ?? []) : (entries ?? []).slice(0, 10)
  const hasMore = (entries?.length ?? 0) > 10

  return (
    <section>
      <SectionLabel>{t.high_risk_entries}</SectionLabel>

      <div className="rounded-xl border bg-card overflow-hidden">
        {/* Desktop table header */}
        <div className="hidden md:grid grid-cols-[1fr_1.6fr_1fr_1.2fr_1fr_0.8fr_0.9fr] text-xs font-semibold uppercase tracking-wider text-muted-foreground bg-muted/50 border-b px-5 py-3 gap-3">
          <span>ID</span>
          <span>{t.account}</span>
          <span>{t.date}</span>
          <span>{t.amount}</span>
          <span>{t.user}</span>
          <span>{t.score}</span>
          <span>{t.level}</span>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Loading entries…</span>
          </div>
        ) : displayEntries.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground">{t.no_entries}</div>
        ) : (
          <div className="divide-y divide-border/60">
            {displayEntries.map((entry: any) => {
              const scoreColor =
                entry.risk_score >= 75 ? "text-red-600 dark:text-red-400" :
                entry.risk_score >= 50 ? "text-orange-600 dark:text-orange-400" :
                entry.risk_score >= 25 ? "text-amber-600 dark:text-amber-400" :
                "text-emerald-600 dark:text-emerald-400"

              return (
                <button
                  key={entry.entry_id}
                  className="w-full text-left hover:bg-muted/40 transition-colors group"
                  onClick={() => setSelectedEntryId(entry.entry_id)}
                >
                  {/* Desktop row */}
                  <div className="hidden md:grid grid-cols-[1fr_1.6fr_1fr_1.2fr_1fr_0.8fr_0.9fr] gap-3 items-center px-5 py-3.5">
                    <span className="font-mono text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                      {entry.entry_id.substring(0, 12)}…
                    </span>
                    <span className="text-sm font-medium truncate">{entry.account}</span>
                    <span className="text-sm text-muted-foreground">
                      {new Date(entry.date).toLocaleDateString()}
                    </span>
                    <span className="text-sm font-mono font-medium">
                      ${entry.amount.toLocaleString()}
                    </span>
                    <span className="text-sm text-muted-foreground truncate">{entry.user || "System"}</span>
                    <span className={`text-sm font-bold tabular-nums ${scoreColor}`}>
                      {entry.risk_score}
                    </span>
                    <div className="flex items-center justify-between">
                      <Badge variant={getRiskBadge(entry.risk_level) as any}>
                        {t[entry.risk_level.toLowerCase() as keyof typeof t] ?? entry.risk_level}
                      </Badge>
                      <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>

                  {/* Mobile stacked card */}
                  <div className="md:hidden px-4 py-3.5 space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold truncate flex-1">{entry.account}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`text-sm font-bold tabular-nums ${scoreColor}`}>
                          {entry.risk_score}
                        </span>
                        <Badge variant={getRiskBadge(entry.risk_level) as any}>
                          {t[entry.risk_level.toLowerCase() as keyof typeof t] ?? entry.risk_level}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                      <span>{new Date(entry.date).toLocaleDateString()}</span>
                      <span className="opacity-40">·</span>
                      <span className="font-mono font-medium text-foreground">${entry.amount.toLocaleString()}</span>
                      <span className="opacity-40">·</span>
                      <span>{entry.user || "System"}</span>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        )}

        {hasMore && !isLoading && (
          <div className="border-t px-5 py-3 bg-muted/30">
            <button
              className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline transition-colors"
              onClick={() => setShowAll((v) => !v)}
            >
              {showAll ? (
                <><ChevronDown className="h-3.5 w-3.5" />{t.view_less}</>
              ) : (
                <><ChevronRight className="h-3.5 w-3.5" />{t.view_all_entries} ({entries?.length?.toLocaleString()})</>
              )}
            </button>
          </div>
        )}
      </div>

      {selectedEntryId && sessionId && (
        <EntryDetailModal
          sessionId={sessionId}
          entryId={selectedEntryId}
          onClose={() => setSelectedEntryId(null)}
        />
      )}
    </section>
  )
}

// ─── 3. IFRS Compliance Cards ─────────────────────────────────────────────────
function IFRSComplianceSection() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  if (!analysisResult) return null

  const items: any[] = analysisResult.compliance_items ?? []
  if (items.length === 0) return null

  const toggle = (i: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })

  return (
    <section>
      <SectionLabel>{t.ifrs_compliance}</SectionLabel>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map((item: any, i: number) => {
          const cfg = getComplianceConfig(item.status, item.score ?? 100)
          const Icon = cfg.icon
          const isOpen = expanded.has(i)

          return (
            <div
              key={i}
              className={`rounded-xl border overflow-hidden transition-all duration-200 ${cfg.bgCls} ${cfg.borderCls}`}
            >
              {/* Always-visible summary */}
              <button
                className="w-full text-left px-5 py-4 flex flex-col gap-3"
                onClick={() => toggle(i)}
              >
                {/* Top row: standard + status badge + chevron */}
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon className={`h-4 w-4 shrink-0 ${cfg.textCls}`} />
                    <span className="text-base font-bold tracking-tight">{item.standard}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${cfg.badgeBg}`}>
                      {cfg.label}
                    </span>
                    <ChevronDown
                      className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                    />
                  </div>
                </div>

                {/* Reason */}
                <div className="space-y-0.5">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {t.reason}
                  </p>
                  <p className={`text-sm leading-snug ${isOpen ? "" : "line-clamp-2"} text-foreground/80`}>
                    {item.details || item.requirement}
                  </p>
                </div>

                {/* Compliance score */}
                {item.score != null && (
                  <div className="flex items-center justify-between pt-1 border-t border-border/40">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                      {t.compliance_score}
                    </p>
                    <span className={`text-lg font-bold tabular-nums ${cfg.textCls}`}>
                      {item.score.toFixed(1)}%
                    </span>
                  </div>
                )}
              </button>

              {/* Expandable details panel */}
              {isOpen && (
                <div className="border-t border-border/40 bg-background/60 px-5 py-4 space-y-4">
                  {/* Why triggered */}
                  <div className="space-y-1">
                    <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                      {t.why_triggered}
                    </p>
                    <p className="text-sm leading-relaxed">{item.requirement}</p>
                  </div>

                  {/* Metadata row */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-muted/50 px-3 py-2.5 space-y-0.5">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                        {t.impact_level}
                      </p>
                      <p className={`text-sm font-semibold ${cfg.textCls}`}>{cfg.impactLevel}</p>
                    </div>
                    <div className="rounded-lg bg-muted/50 px-3 py-2.5 space-y-0.5">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                        {t.status}
                      </p>
                      <p className="text-sm font-semibold">{cfg.label}</p>
                    </div>
                  </div>

                  {/* Recommendation */}
                  <div className="space-y-1">
                    <p className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                      {t.recommendation}
                    </p>
                    <p className="text-sm leading-relaxed text-foreground/80">
                      {cfg.impactLevel === "None"
                        ? "No action required. This standard is fully met."
                        : cfg.impactLevel === "Low"
                        ? `Review flagged entries for ${item.standard} and confirm accounting estimates are within acceptable ranges.`
                        : cfg.impactLevel === "Medium"
                        ? `Escalate to the accounting team. Duplicate or related-party entries under ${item.standard} require review and approval documentation.`
                        : `Immediate review required. Revenue recognition or approval workflow gaps under ${item.standard} must be resolved before the next reporting period.`
                      }
                    </p>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}

// ─── Public Export ─────────────────────────────────────────────────────────────
export function DashboardTables() {
  return (
    <div className="space-y-12">
      <FraudIndicatorsSection />
      <HighRiskEntriesSection />
      <IFRSComplianceSection />
    </div>
  )
}
