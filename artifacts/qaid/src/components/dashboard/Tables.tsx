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
  if (n.includes("weekend"))          return Calendar
  if (n.includes("round") || n.includes("suspicious")) return CircleDot
  if (n.includes("duplicate"))        return Copy
  if (n.includes("out-of-hours") || n.includes("hours")) return Moon
  if (n.includes("imbalance") || n.includes("debit"))   return Scale
  if (n.includes("inactive"))         return UserMinus
  if (n.includes("high user") || n.includes("user"))    return Users
  if (n.includes("monthly") || n.includes("variance"))  return TrendingUp
  if (n.includes("large") || n.includes("amount"))      return Banknote
  if (n.includes("suspense"))         return Archive
  if (n.includes("critical"))         return AlertTriangle
  return ShieldAlert
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "text-red-600 dark:text-red-400 bg-red-500/10",
  HIGH:     "text-orange-600 dark:text-orange-400 bg-orange-500/10",
  MEDIUM:   "text-amber-600 dark:text-amber-400 bg-amber-500/10",
  LOW:      "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10",
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

  // Sort: critical first
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
              className="rounded-xl border bg-card p-5 flex flex-col gap-3 hover:shadow-sm transition-shadow"
            >
              {/* Header row */}
              <div className="flex items-start justify-between gap-2">
                <div className={`p-2 rounded-lg ${colorCls}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className={`text-2xl font-bold tabular-nums ${colorCls.split(" ")[0]}`}>
                  {ind.count.toLocaleString()}
                </span>
              </div>
              {/* Name */}
              <p className="text-sm font-semibold leading-tight">{ind.name}</p>
              {/* Short description */}
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                {ind.description}
              </p>
              {/* Severity badge */}
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
      <div className="flex items-center justify-between mb-4">
        <SectionLabel>{t.high_risk_entries}</SectionLabel>
      </div>

      <div className="rounded-xl border bg-card overflow-hidden">
        {/* Table header */}
        <div className="grid grid-cols-[1fr_1.6fr_1fr_1.2fr_1fr_0.8fr_0.9fr] text-xs font-semibold uppercase tracking-wider text-muted-foreground bg-muted/50 border-b px-5 py-3 gap-3 hidden md:grid">
          <span>ID</span>
          <span>{t.account}</span>
          <span>{t.date}</span>
          <span>{t.amount}</span>
          <span>{t.user}</span>
          <span>{t.score}</span>
          <span>{t.level}</span>
        </div>

        {/* Body */}
        {isLoading ? (
          <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Loading entries…</span>
          </div>
        ) : displayEntries.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground">{t.no_entries}</div>
        ) : (
          <div className="divide-y divide-border/60">
            {displayEntries.map((entry: any) => (
              <button
                key={entry.entry_id}
                className="w-full text-left px-5 py-3.5 hover:bg-muted/40 transition-colors group grid grid-cols-1 md:grid-cols-[1fr_1.6fr_1fr_1.2fr_1fr_0.8fr_0.9fr] gap-3 items-center"
                onClick={() => setSelectedEntryId(entry.entry_id)}
              >
                {/* ID */}
                <span className="font-mono text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                  {entry.entry_id.substring(0, 12)}…
                </span>
                {/* Account */}
                <span className="text-sm font-medium truncate">{entry.account}</span>
                {/* Date */}
                <span className="text-sm text-muted-foreground">
                  {new Date(entry.date).toLocaleDateString()}
                </span>
                {/* Amount */}
                <span className="text-sm font-mono font-medium">
                  ${entry.amount.toLocaleString()}
                </span>
                {/* User */}
                <span className="text-sm text-muted-foreground truncate">{entry.user || "System"}</span>
                {/* Score */}
                <span className={`text-sm font-bold tabular-nums ${
                  entry.risk_score >= 75 ? "text-red-600 dark:text-red-400" :
                  entry.risk_score >= 50 ? "text-orange-600 dark:text-orange-400" :
                  entry.risk_score >= 25 ? "text-amber-600 dark:text-amber-400" :
                  "text-emerald-600 dark:text-emerald-400"
                }`}>
                  {entry.risk_score}
                </span>
                {/* Level */}
                <div className="flex items-center justify-between">
                  <Badge variant={getRiskBadge(entry.risk_level) as any}>
                    {t[entry.risk_level.toLowerCase() as keyof typeof t] ?? entry.risk_level}
                  </Badge>
                  <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Footer: view all / show less */}
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

      {/* Detail modal */}
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

// ─── 3. IFRS Compliance Expandable Cards ─────────────────────────────────────
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

  const statusConfig: Record<string, { icon: LucideIcon; cls: string; label: string }> = {
    COMPLIANT:     { icon: CheckCircle2, cls: "text-emerald-600 dark:text-emerald-400", label: t.compliant },
    WARNING:       { icon: AlertCircle,  cls: "text-amber-600  dark:text-amber-400",   label: t.warning   },
    NON_COMPLIANT: { icon: XCircle,      cls: "text-red-600    dark:text-red-400",      label: t.non_compliant },
  }

  return (
    <section>
      <SectionLabel>{t.ifrs_compliance}</SectionLabel>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {items.map((item: any, i: number) => {
          const cfg = statusConfig[item.status] ?? statusConfig.WARNING
          const Icon = cfg.icon
          const isOpen = expanded.has(i)

          return (
            <div key={i} className="rounded-xl border bg-card overflow-hidden">
              {/* Header (always visible) */}
              <button
                className="w-full flex items-center gap-3 px-5 py-4 hover:bg-muted/40 transition-colors text-left"
                onClick={() => toggle(i)}
              >
                <Icon className={`h-5 w-5 shrink-0 ${cfg.cls}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm">{item.standard}</span>
                    <span className={`text-xs font-semibold ${cfg.cls}`}>{cfg.label}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 truncate">{item.requirement}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {item.score != null && (
                    <span className={`text-sm font-bold tabular-nums ${cfg.cls}`}>
                      {item.score.toFixed(1)}%
                    </span>
                  )}
                  <ChevronDown
                    className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                  />
                </div>
              </button>

              {/* Expandable body */}
              {isOpen && (
                <div className="border-t bg-muted/20 px-5 py-4 space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{t.details}</p>
                  <p className="text-sm leading-relaxed">{item.details}</p>
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
