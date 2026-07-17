import React from "react"
import { useGetEntryDetail, getGetEntryDetailQueryKey } from "@workspace/api-client-react"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../ui/dialog"
import { Badge } from "../ui/badge"
import { Progress } from "../ui/progress"
import { Separator } from "@radix-ui/react-separator"

interface EntryDetailModalProps {
  sessionId: string
  entryId: string
  onClose: () => void
}

export function EntryDetailModal({ sessionId, entryId, onClose }: EntryDetailModalProps) {
  const { language } = useTheme()
  const t = translations[language]

  const { data: detail, isLoading, error } = useGetEntryDetail(sessionId, entryId, {
    query: {
      enabled: !!sessionId && !!entryId,
      queryKey: getGetEntryDetailQueryKey(sessionId, entryId)
    }
  })

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {t.entry_details}
            <span className="font-mono text-sm text-muted-foreground bg-muted px-2 py-1 rounded">
              {entryId}
            </span>
          </DialogTitle>
          <DialogDescription>
            Detailed AI analysis and rule execution results for this journal entry.
          </DialogDescription>
        </DialogHeader>

        {isLoading && <div className="py-12 text-center animate-pulse">Loading detailed analysis...</div>}
        {error && <div className="py-12 text-center text-destructive">Failed to load entry details.</div>}
        
        {detail && (
          <div className="space-y-6 mt-4">
            {/* Top Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="text-sm text-muted-foreground">{t.score}</div>
                <div className="text-3xl font-bold text-primary">{detail.risk_score}</div>
                <Badge variant={detail.risk_level === 'CRITICAL' ? 'critical' : detail.risk_level === 'HIGH' ? 'danger' : 'warning'} className="mt-2">
                  {detail.risk_level}
                </Badge>
              </div>
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="text-sm text-muted-foreground">{t.ml_score}</div>
                <div className="text-2xl font-bold">{detail.ml_score.toFixed(1)}</div>
                <Progress value={detail.ml_score} className="mt-2" />
              </div>
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="text-sm text-muted-foreground">{t.rule_score}</div>
                <div className="text-2xl font-bold">{detail.rule_score.toFixed(1)}</div>
                <Progress value={detail.rule_score} className="mt-2" />
              </div>
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="text-sm text-muted-foreground">{t.probability}</div>
                <div className="text-2xl font-bold">{(detail.fraud_probability * 100).toFixed(1)}%</div>
              </div>
            </div>

            {/* Entry Data */}
            <div>
              <h3 className="font-semibold mb-3">Transaction Data</h3>
              <div className="grid grid-cols-2 gap-y-2 text-sm border rounded-lg p-4 bg-card">
                <div className="text-muted-foreground">{t.account}:</div>
                <div className="font-medium">{detail.account} {detail.account_name ? `- ${detail.account_name}` : ''}</div>
                
                <div className="text-muted-foreground">{t.amount}:</div>
                <div className="font-medium font-mono">${detail.amount.toLocaleString()}</div>
                
                <div className="text-muted-foreground">{t.date}:</div>
                <div>{new Date(detail.date).toLocaleString()}</div>
                
                <div className="text-muted-foreground">{t.user}:</div>
                <div>{detail.user || 'System'}</div>
                
                <div className="text-muted-foreground">{t.description}:</div>
                <div className="col-span-1">{detail.description || 'N/A'}</div>
              </div>
            </div>

            {/* Triggered Rules */}
            <div>
              <h3 className="font-semibold mb-3">{t.triggered_rules}</h3>
              <div className="space-y-2">
                {detail.triggered_rules_detail.map((rule, idx) => (
                  <div key={idx} className="flex items-start justify-between p-3 border rounded-lg bg-destructive/5 border-destructive/20">
                    <div>
                      <div className="font-medium text-destructive">{rule.rule_name}</div>
                      <div className="text-sm text-muted-foreground mt-1">{rule.description}</div>
                    </div>
                    <Badge variant="outline" className="shrink-0 bg-background">Weight: {rule.weight}</Badge>
                  </div>
                ))}
                {detail.triggered_rules_detail.length === 0 && (
                  <div className="text-muted-foreground text-sm italic">No rules triggered.</div>
                )}
              </div>
            </div>

            {/* Recommendation */}
            <div className="bg-primary/5 border border-primary/20 p-4 rounded-lg">
              <h3 className="font-semibold mb-2 text-primary">{t.recommendation}</h3>
              <p className="text-sm leading-relaxed">{detail.recommendation}</p>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
