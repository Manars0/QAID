import React from "react"
import { FileUp, Play, ShieldAlert, FileSearch, TrendingUp, Cpu, Server, Activity, FileCheck } from "lucide-react"
import { useLocation } from "wouter"
import { toast } from "sonner"
import { useTheme } from "../components/theme-provider"
import { translations } from "../lib/i18n"
import { useAnalysis } from "../contexts/AnalysisContext"
import { useUploadFile, useLoadDemo } from "@workspace/api-client-react"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { motion } from "framer-motion"

export function Landing() {
  const { language } = useTheme()
  const t = translations[language]
  const [, setLocation] = useLocation()
  const { setAnalysisResult } = useAnalysis()
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const uploadFile = useUploadFile({
    mutation: {
      onSuccess: (data) => {
        setAnalysisResult(data)
        setLocation("/dashboard")
        toast.success("Analysis complete")
      },
      onError: (error) => {
        toast.error("Failed to upload file")
        console.error(error)
      }
    }
  })

  const loadDemo = useLoadDemo({
    mutation: {
      onSuccess: (data) => {
        setAnalysisResult(data)
        setLocation("/dashboard")
        toast.success("Demo dataset loaded successfully")
      },
      onError: (error) => {
        toast.error("Failed to load demo")
        console.error(error)
      }
    }
  })

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) uploadFile.mutate({ data: { file: file as any } })
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadFile.mutate({ data: { file: file as any } })
  }

  const isLoading = uploadFile.isPending || loadDemo.isPending

  return (
    <div className="flex flex-col min-h-[calc(100dvh-4rem)]">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 py-20 bg-gradient-to-b from-background via-background to-[hsl(174,76%,25%)]/5">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl mx-auto space-y-8"
        >
          {/* Pill badge */}
          <span className="inline-flex items-center rounded-full border border-[hsl(174,76%,25%)]/30 bg-[hsl(174,76%,25%)]/8 px-3.5 py-1 text-sm font-semibold text-primary">
            Enterprise Grade AI Analysis
          </span>

          {/* Logo image — replaces the old text h1 */}
          <div className="flex justify-center">
            <img
              src="/qaid-logo.png"
              alt="QAID"
              className="h-24 w-auto object-contain"
              style={{ background: "transparent", border: "none", boxShadow: "none" }}
              draggable={false}
            />
          </div>

          <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            {t.tagline}
          </p>

          {/* Action cards */}
          <div className="grid sm:grid-cols-2 gap-6 max-w-3xl mx-auto pt-4">

            {/* Upload */}
            <div
              onClick={() => !isLoading && fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              className={`relative flex flex-col items-center justify-center gap-4 p-8 rounded-2xl border-2 border-dashed transition-all cursor-pointer group ${
                isLoading
                  ? 'opacity-50 pointer-events-none'
                  : 'border-border hover:border-primary hover:bg-primary/5'
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".xlsx,.csv,.zip"
                onChange={handleFileChange}
              />
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                <FileUp className="h-8 w-8" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">{t.upload_erp}</h3>
                <p className="text-sm text-muted-foreground mt-1">{t.drag_drop}</p>
              </div>
              {uploadFile.isPending && (
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center rounded-xl">
                  <Activity className="h-8 w-8 text-primary animate-pulse mb-2" />
                  <span className="font-medium text-primary">{t.analyzing}</span>
                </div>
              )}
            </div>

            {/* Demo */}
            <div
              onClick={() => !isLoading && loadDemo.mutate()}
              className={`relative flex flex-col items-center justify-center gap-4 p-8 rounded-2xl border bg-card shadow-sm transition-all cursor-pointer group ${
                isLoading
                  ? 'opacity-50 pointer-events-none'
                  : 'hover:shadow-md hover:border-primary/40'
              }`}
            >
              <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center text-foreground group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                <Play className="h-8 w-8 ml-1" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">{t.demo_data}</h3>
                <p className="text-sm text-muted-foreground mt-1">Load a realistic sample dataset</p>
              </div>
              {loadDemo.isPending && (
                <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center rounded-xl">
                  <Activity className="h-8 w-8 text-primary animate-pulse mb-2" />
                  <span className="font-medium text-primary">{t.loading_demo}</span>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section className="py-20 bg-background px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">{t.features_title}</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Cpu,        title: t.feature_1, desc: t.feature_1_desc },
              { icon: FileCheck,  title: t.feature_2, desc: t.feature_2_desc },
              { icon: ShieldAlert,title: t.feature_3, desc: t.feature_3_desc },
            ].map((f, i) => (
              <Card key={i} className="border shadow-sm bg-card hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="h-11 w-11 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                    <f.icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-lg">{f.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ── Workflow ──────────────────────────────────────────────────────── */}
      <section className="py-20 bg-muted/30 px-4 border-t border-b border-border">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-16">{t.workflow_title}</h2>
          <div className="relative">
            <div className="absolute top-8 left-0 w-full h-px bg-border hidden md:block" />
            <div className="grid md:grid-cols-4 gap-8 relative z-10">
              {[
                { icon: Server,     title: t.step_1, num: "01" },
                { icon: FileSearch, title: t.step_2, num: "02" },
                { icon: Cpu,        title: t.step_3, num: "03" },
                { icon: TrendingUp, title: t.step_4, num: "04" },
              ].map((s, i) => (
                <div key={i} className="flex flex-col items-center text-center group">
                  <div className="w-16 h-16 rounded-full bg-card border-2 border-border flex items-center justify-center mb-4 shadow-sm group-hover:border-primary group-hover:bg-primary/5 transition-all relative z-10">
                    <s.icon className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                  <span className="text-xs font-bold text-primary/60 tracking-widest mb-1">{s.num}</span>
                  <h3 className="font-semibold text-sm">{s.title}</h3>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

    </div>
  )
}
