import React from "react"
import { useLocation } from "wouter"
import { Download, FileDown, BrainCircuit, Lightbulb, AlertTriangle } from "lucide-react"
import { useAnalysis } from "../contexts/AnalysisContext"
import { useTheme } from "../components/theme-provider"
import { translations } from "../lib/i18n"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { KPICards } from "../components/dashboard/KPICards"
import { DashboardCharts } from "../components/dashboard/Charts"
import { DashboardTables } from "../components/dashboard/Tables"
import { motion } from "framer-motion"

export function Dashboard() {
  const { analysisResult } = useAnalysis()
  const [, setLocation] = useLocation()
  const { language } = useTheme()
  const t = translations[language]

  React.useEffect(() => {
    if (!analysisResult) {
      setLocation("/")
    }
  }, [analysisResult, setLocation])

  if (!analysisResult) return null

  const sessionId = analysisResult.session_id

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="container mx-auto p-4 max-w-[1600px] space-y-6"
    >
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 py-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t.dashboard}</h1>
          <p className="text-muted-foreground mt-1">
            Analysis Session: <span className="font-mono text-xs">{sessionId}</span> | 
            File: {analysisResult.file_name}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <a href={`/api/analysis/${sessionId}/report/excel`} download>
              <FileDown className="mr-2 h-4 w-4" />
              {t.download_excel}
            </a>
          </Button>
          <Button asChild>
            <a href={`/api/analysis/${sessionId}/report/pdf`} download>
              <Download className="mr-2 h-4 w-4" />
              {t.download_pdf}
            </a>
          </Button>
        </div>
      </div>

      <KPICards />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-2 bg-primary/5 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <BrainCircuit className="h-5 w-5" />
              {t.ai_summary}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="leading-relaxed text-sm md:text-base">
              {analysisResult.ai_summary}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-amber-500" />
              {t.recommendations}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {analysisResult.recommendations.map((rec: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {analysisResult.validation_issues.length > 0 && (
        <Card className="border-destructive/50 bg-destructive/5 mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Data Validation Issues
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {analysisResult.validation_issues.map((issue: any, i: number) => (
                <li key={i} className="text-sm">
                  <span className="font-semibold mr-2">{issue.type}:</span>
                  {issue.description} ({issue.count} occurrences)
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <DashboardCharts />
      
      <DashboardTables />
      
    </motion.div>
  )
}
