import React, { useMemo } from "react"
import { useAnalysis } from "../../contexts/AnalysisContext"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar, RadialBarChart, RadialBar, PolarAngleAxis
} from "recharts"

const RISK_COLORS = {
  LOW: "hsl(var(--risk-low))",
  MEDIUM: "hsl(var(--risk-medium))",
  HIGH: "hsl(var(--risk-high))",
  CRITICAL: "hsl(var(--risk-critical))"
}

export function DashboardCharts() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]

  if (!analysisResult) return null

  const { risk_distribution, risk_trend, top_changed_accounts, kpi_summary } = analysisResult

  const gaugeData = [{
    name: 'Risk',
    value: kpi_summary.overall_risk_score,
    fill: kpi_summary.risk_level === 'CRITICAL' ? RISK_COLORS.CRITICAL : 
          kpi_summary.risk_level === 'HIGH' ? RISK_COLORS.HIGH :
          kpi_summary.risk_level === 'MEDIUM' ? RISK_COLORS.MEDIUM : RISK_COLORS.LOW
  }]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      {/* Risk Gauge */}
      <Card>
        <CardHeader>
          <CardTitle>{t.risk_score}</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center relative">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart 
              cx="50%" cy="80%" 
              innerRadius="70%" outerRadius="90%" 
              barSize={20} data={gaugeData} 
              startAngle={180} endAngle={0}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
              <RadialBar background dataKey="value" cornerRadius={10} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center mt-12 pointer-events-none">
            <span className="text-4xl font-bold">{kpi_summary.overall_risk_score}</span>
            <span className="text-sm text-muted-foreground">{kpi_summary.risk_level}</span>
          </div>
        </CardContent>
      </Card>

      {/* Risk Distribution Pie */}
      <Card>
        <CardHeader>
          <CardTitle>{t.risk_distribution}</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={risk_distribution}
                cx="50%" cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="count"
                nameKey="level"
              >
                {risk_distribution.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.level as keyof typeof RISK_COLORS] || RISK_COLORS.LOW} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: number) => [`${value} entries`, 'Count']}
                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Risk Trend */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>{t.risk_trend}</CardTitle>
        </CardHeader>
        <CardContent className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={risk_trend} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="period" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
              />
              <Legend />
              <Line type="monotone" dataKey="avg_risk_score" name="Avg Risk Score" stroke="hsl(var(--primary))" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="flagged_count" name="Flagged Entries" stroke="hsl(var(--destructive))" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top Changed Accounts */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>{t.top_changed_accounts}</CardTitle>
        </CardHeader>
        <CardContent className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={top_changed_accounts} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="account_code" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'hsl(var(--muted))' }}
                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
                formatter={(value: number, name: string) => {
                  if (name === "monthly_change_pct") return [`${value}%`, "Change"];
                  return [`$${value.toLocaleString()}`, name];
                }}
              />
              <Legend />
              <Bar dataKey="monthly_change_pct" name="Change %" fill="hsl(var(--chart-4))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
