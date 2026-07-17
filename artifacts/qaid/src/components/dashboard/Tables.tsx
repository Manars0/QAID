import React, { useState } from "react"
import { useAnalysis } from "../../contexts/AnalysisContext"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { useGetAnalysisEntries, getGetAnalysisEntriesQueryKey } from "@workspace/api-client-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table"
import { Badge } from "../ui/badge"
import { Progress } from "../ui/progress"
import { EntryDetailModal } from "./EntryDetailModal"

export function DashboardTables() {
  const { analysisResult } = useAnalysis()
  const { language } = useTheme()
  const t = translations[language]
  
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null)

  const sessionId = analysisResult?.session_id
  const { data: entries, isLoading } = useGetAnalysisEntries(sessionId!, {
    query: {
      enabled: !!sessionId,
      queryKey: getGetAnalysisEntriesQueryKey(sessionId!)
    }
  })

  if (!analysisResult) return null

  const getRiskBadgeVariant = (level: string) => {
    switch (level.toUpperCase()) {
      case 'LOW': return 'success'
      case 'MEDIUM': return 'warning'
      case 'HIGH': return 'danger'
      case 'CRITICAL': return 'critical'
      default: return 'default'
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status.toUpperCase()) {
      case 'PASS': return 'success'
      case 'WARNING': return 'warning'
      case 'FAIL': return 'critical'
      default: return 'default'
    }
  }

  return (
    <div className="space-y-6">
      {/* High Risk Accounts */}
      <Card>
        <CardHeader>
          <CardTitle>{t.high_risk_accounts}</CardTitle>
          <CardDescription>Accounts with highest aggregate risk scores</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t.account}</TableHead>
                <TableHead>Total Entries</TableHead>
                <TableHead>Total Amount</TableHead>
                <TableHead>Avg Score</TableHead>
                <TableHead>{t.level}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analysisResult.high_risk_accounts.map((account: any) => (
                <TableRow key={account.account_code}>
                  <TableCell className="font-medium">
                    {account.account_code} {account.account_name ? `- ${account.account_name}` : ''}
                  </TableCell>
                  <TableCell>{account.total_entries}</TableCell>
                  <TableCell>${account.total_amount.toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="w-8">{account.avg_risk_score.toFixed(0)}</span>
                      <Progress value={account.avg_risk_score} className="w-16" />
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getRiskBadgeVariant(account.risk_level) as any}>
                      {t[account.risk_level.toLowerCase() as keyof typeof t] || account.risk_level}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Fraud Indicators */}
      <Card>
        <CardHeader>
          <CardTitle>{t.fraud_indicators}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {analysisResult.fraud_indicators.map((indicator: any, i: number) => (
              <div key={i} className="flex flex-col p-4 border rounded-lg bg-muted/20">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-semibold">{indicator.name}</h4>
                  <Badge variant={getRiskBadgeVariant(indicator.severity) as any}>
                    {indicator.count}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{indicator.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* IFRS Compliance */}
      <Card>
        <CardHeader>
          <CardTitle>{t.ifrs_compliance}</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t.standard}</TableHead>
                <TableHead>Requirement</TableHead>
                <TableHead>{t.status}</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analysisResult.compliance_items.map((item: any, i: number) => (
                <TableRow key={i}>
                  <TableCell className="font-semibold">{item.standard}</TableCell>
                  <TableCell>{item.requirement}</TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(item.status) as any}>
                      {t[item.status.toLowerCase() as keyof typeof t] || item.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{item.details}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Full Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>{t.high_risk_entries}</CardTitle>
          <CardDescription>Click a row to view full AI analysis details</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground animate-pulse">Loading entries...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>{t.account}</TableHead>
                  <TableHead>{t.date}</TableHead>
                  <TableHead>{t.amount}</TableHead>
                  <TableHead>{t.user}</TableHead>
                  <TableHead>{t.score}</TableHead>
                  <TableHead>{t.level}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries?.slice(0, 100).map((entry) => (
                  <TableRow 
                    key={entry.entry_id} 
                    className="cursor-pointer hover:bg-muted/80"
                    onClick={() => setSelectedEntryId(entry.entry_id)}
                  >
                    <TableCell className="font-mono text-xs">{entry.entry_id.substring(0, 8)}...</TableCell>
                    <TableCell>{entry.account}</TableCell>
                    <TableCell>{new Date(entry.date).toLocaleDateString()}</TableCell>
                    <TableCell>${entry.amount.toLocaleString()}</TableCell>
                    <TableCell>{entry.user || 'System'}</TableCell>
                    <TableCell>
                      <span className="font-semibold text-primary">{entry.risk_score}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRiskBadgeVariant(entry.risk_level) as any}>
                        {t[entry.risk_level.toLowerCase() as keyof typeof t] || entry.risk_level}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedEntryId && sessionId && (
        <EntryDetailModal 
          sessionId={sessionId} 
          entryId={selectedEntryId} 
          onClose={() => setSelectedEntryId(null)} 
        />
      )}
    </div>
  )
}
