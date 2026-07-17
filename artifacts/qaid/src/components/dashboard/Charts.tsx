import React from "react"
import { useAnalysis } from "../../contexts/AnalysisContext"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  RadialBarChart, RadialBar, PolarAngleAxis,
} from "recharts"

const RISK_COLORS: Record<string, string> = {
  LOW:      "hsl(var(--risk-low))",
  MEDIUM:   "hsl(var(--risk-medium))",
  HIGH:     "hsl(var(--risk-high))",
  CRITICAL: "hsl(var(--risk-critical))",
}

const RISK_SCORE_COLOR: Record<string, string> = {
  LOW:      "#10b981",
  MEDIUM:   "#f59e0b",
  HIGH:     "#f97316",
  CRITICAL: "#ef4444",
}

// ─── Gauge ────────────────────────────────────────────────────────────────────
function RiskGauge() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]
  if (!analysisResult) return null

  const { kpi_summary } = analysisResult
  const score = kpi_summary.overall_risk_score
  const color = RISK_SCORE_COLOR[kpi_summary.risk_level] ?? "#10b981"
  const gaugeData = [{ value: score, fill: color }]

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-0">
        <CardTitle className="text-base font-semibold">{t.risk_score}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col items-center justify-center pt-4 pb-6">
        <div className="relative w-full" style={{ height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%" cy="85%"
              innerRadius="70%" outerRadius="95%"
              barSize={16}
              data={gaugeData}
              startAngle={180} endAngle={0}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
              <RadialBar background={{ fill: "hsl(var(--muted))" }} dataKey="value" cornerRadius={8} />
            </RadialBarChart>
          </ResponsiveContainer>
          {/* Overlay labels */}
          <div className="absolute inset-0 flex flex-col items-center justify-end pb-3 pointer-events-none">
            <span className="text-5xl font-bold tabular-nums leading-none" style={{ color }}>
              {score.toFixed(1)}
            </span>
            <span className="text-sm font-semibold mt-1 uppercase tracking-widest text-muted-foreground">
              {kpi_summary.risk_level}
            </span>
          </div>
          {/* Scale labels */}
          <div className="absolute bottom-2 left-4 text-xs text-muted-foreground">0</div>
          <div className="absolute bottom-2 right-4 text-xs text-muted-foreground">100</div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Distribution Donut ───────────────────────────────────────────────────────
function RiskDistribution() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]
  if (!analysisResult) return null

  const { risk_distribution } = analysisResult

  const RADIAN = Math.PI / 180
  const renderLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.06) return null
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)
    return (
      <text x={x} y={y} fill="#fff" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={700}>
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-0">
        <CardTitle className="text-base font-semibold">{t.risk_distribution}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex items-center justify-center pt-4">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={risk_distribution}
              cx="50%" cy="50%"
              innerRadius={52}
              outerRadius={85}
              paddingAngle={2}
              dataKey="count"
              nameKey="level"
              labelLine={false}
              label={renderLabel}
            >
              {risk_distribution.map((entry: any, i: number) => (
                <Cell key={i} fill={RISK_COLORS[entry.level] ?? RISK_COLORS.LOW} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v: number, name: string) => [`${v.toLocaleString()} entries`, name]}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                borderColor: "hsl(var(--border))",
                color: "hsl(var(--foreground))",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              formatter={(value) => (
                <span style={{ fontSize: 12, color: "hsl(var(--muted-foreground))" }}>
                  {value}
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

// ─── Top Risk Accounts ────────────────────────────────────────────────────────
function TopRiskAccounts() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]
  if (!analysisResult) return null

  const accounts: any[] = analysisResult.high_risk_accounts ?? []
  const chartData = accounts
    .slice(0, 8)
    .map((a) => ({
      name: a.account_name
        ? `${a.account_code} · ${a.account_name.length > 16 ? a.account_name.substring(0, 16) + "…" : a.account_name}`
        : a.account_code,
      score: Math.round(a.avg_risk_score),
      level: a.risk_level,
      amount: a.total_amount,
    }))

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-0">
          <CardTitle className="text-base font-semibold">{t.top_risk_accounts}</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-48 text-muted-foreground text-sm">
          No account data available.
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-0">
        <CardTitle className="text-base font-semibold">{t.top_risk_accounts}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pt-4">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 40, left: 4, bottom: 0 }}
            barCategoryGap="30%"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={110}
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              cursor={{ fill: "hsl(var(--muted))" }}
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                borderColor: "hsl(var(--border))",
                color: "hsl(var(--foreground))",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(v: number, _name: string, props: any) => [
                `${v} / 100 — ${props.payload?.level ?? ""}`,
                t.score,
              ]}
            />
            <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={16}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={RISK_SCORE_COLOR[entry.level] ?? "#10b981"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

// ─── Financial Overview Section (exported) ────────────────────────────────────
export function DashboardCharts() {
  const { language } = useTheme()
  const t = translations[language]

  return (
    <section>
      <p className="text-xs font-semibold tracking-[0.15em] uppercase text-muted-foreground mb-4">
        {t.financial_overview}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <RiskGauge />
        <RiskDistribution />
        <TopRiskAccounts />
      </div>
    </section>
  )
}
