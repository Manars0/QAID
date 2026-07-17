import React from "react"
import { useLocation } from "wouter"
import { Download, FileDown, BrainCircuit, Lightbulb, ArrowRight, BarChart2 } from "lucide-react"
import { useAnalysis } from "../contexts/AnalysisContext"
import { useTheme } from "../components/theme-provider"
import { translations } from "../lib/i18n"
import { Button } from "../components/ui/button"
import { KPICards } from "../components/dashboard/KPICards"
import { DashboardCharts } from "../components/dashboard/Charts"
import { DashboardTables } from "../components/dashboard/Tables"
import { motion } from "framer-motion"

// ─── Section divider with fade-in ─────────────────────────────────────────────
function Section({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
    >
      {children}
    </motion.div>
  )
}

export function Dashboard() {
  const { analysisResult } = useAnalysis()
  const [, setLocation] = useLocation()
  const { language } = useTheme()
  const t = translations[language]

  React.useEffect(() => {
    if (!analysisResult) setLocation("/")
  }, [analysisResult, setLocation])

  if (!analysisResult) return null

  const sessionId = analysisResult.session_id

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 md:px-6 max-w-[1400px] py-8 space-y-12">

        {/* ── Page Header ──────────────────────────────────────────────────── */}
        <Section delay={0}>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <BarChart2 className="h-5 w-5 text-primary" />
                <h1 className="text-2xl font-bold tracking-tight">{t.dashboard}</h1>
              </div>
              <p className="text-sm text-muted-foreground">
                <span className="font-medium">{analysisResult.file_name}</span>
                <span className="mx-2 opacity-40">·</span>
                <span className="font-mono text-xs opacity-60">{sessionId}</span>
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Button variant="outline" size="sm" asChild>
                <a href={`/api/analysis/${sessionId}/report/excel`} download>
                  <FileDown className="mr-1.5 h-3.5 w-3.5" />
                  {t.download_excel}
                </a>
              </Button>
              <Button size="sm" asChild>
                <a href={`/api/analysis/${sessionId}/report/pdf`} download>
                  <Download className="mr-1.5 h-3.5 w-3.5" />
                  {t.download_pdf}
                </a>
              </Button>
            </div>
          </div>
        </Section>

        {/* ── KPI Cards ────────────────────────────────────────────────────── */}
        <Section delay={0.05}>
          <KPICards />
        </Section>

        {/* ── AI Summary + Recommendations ─────────────────────────────────── */}
        <Section delay={0.1}>
          <p className="text-xs font-semibold tracking-[0.15em] uppercase text-muted-foreground mb-4">
            {t.ai_summary}
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
            {/* Executive Summary — wider */}
            <div className="lg:col-span-3 rounded-xl border bg-card overflow-hidden flex flex-col">
              <div className="border-b bg-primary/5 px-6 py-4 flex items-center gap-2">
                <BrainCircuit className="h-4 w-4 text-primary" />
                <h2 className="text-sm font-semibold text-primary">{t.ai_summary}</h2>
              </div>
              <div className="px-6 py-5 flex-1">
                <p className="text-sm leading-[1.85] text-foreground/90">
                  {analysisResult.ai_summary}
                </p>
              </div>
            </div>

            {/* Recommended Actions */}
            <div className="lg:col-span-2 rounded-xl border bg-card overflow-hidden flex flex-col">
              <div className="border-b px-6 py-4 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <h2 className="text-sm font-semibold">{t.recommendations}</h2>
              </div>
              <div className="px-6 py-5 flex-1">
                <ul className="space-y-3">
                  {analysisResult.recommendations.map((rec: string, i: number) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm leading-snug">
                      <ArrowRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Section>

        {/* ── Financial Overview ───────────────────────────────────────────── */}
        <Section delay={0.15}>
          <DashboardCharts />
        </Section>

        {/* ── Fraud Indicators · High Risk Entries · IFRS ──────────────────── */}
        <Section delay={0.2}>
          <DashboardTables />
        </Section>

        {/* ── Footer ───────────────────────────────────────────────────────── */}
        <footer className="border-t pt-6 pb-4 flex flex-col md:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>
            <span className="font-semibold text-foreground">QAID</span>
            {" · "}Enterprise Financial Intelligence
          </span>
          <span className="font-mono opacity-60">{sessionId}</span>
        </footer>

      </div>
    </div>
  )
}
