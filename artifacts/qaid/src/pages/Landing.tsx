import React from "react"
import { FileUp, Play, ShieldAlert, FileSearch, TrendingUp, Cpu, Server, Activity, FileCheck, CheckCircle } from "lucide-react"
import { useLocation } from "wouter"
import { toast } from "sonner"
import { useTheme } from "../components/theme-provider"
import { translations } from "../lib/i18n"
import { useAnalysis } from "../contexts/AnalysisContext"
import { useUploadFile, useLoadDemo } from "@workspace/api-client-react"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
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
    if (file) {
      uploadFile.mutate({ data: { file: file as any } })
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadFile.mutate({ data: { file: file as any } })
    }
  }

  const isLoading = uploadFile.isPending || loadDemo.isPending

  return (
    <div className="flex flex-col min-h-[calc(100dvh-4rem)]">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 py-20 bg-gradient-to-b from-background to-muted/30">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl mx-auto space-y-8"
        >
          <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-secondary text-secondary-foreground">
            Enterprise Grade AI Analysis
          </div>
          
          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
            <span className="text-primary">{t.app_name}</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            {t.tagline}
          </p>

          <div className="grid sm:grid-cols-2 gap-6 max-w-3xl mx-auto pt-8">
            <div 
              onClick={() => !isLoading && fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              className={`relative flex flex-col items-center justify-center gap-4 p-8 rounded-2xl border-2 border-dashed transition-colors cursor-pointer group ${isLoading ? 'opacity-50 pointer-events-none' : 'hover:border-primary hover:bg-primary/5'}`}
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

            <div 
              onClick={() => !isLoading && loadDemo.mutate()}
              className={`relative flex flex-col items-center justify-center gap-4 p-8 rounded-2xl border bg-card transition-all cursor-pointer shadow-sm ${isLoading ? 'opacity-50 pointer-events-none' : 'hover:shadow-md hover:border-primary/50'}`}
            >
              <div className="h-16 w-16 rounded-full bg-secondary flex items-center justify-center text-foreground">
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

      {/* Features Section */}
      <section className="py-20 bg-background px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">{t.features_title}</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Cpu, title: t.feature_1, desc: t.feature_1_desc },
              { icon: FileCheck, title: t.feature_2, desc: t.feature_2_desc },
              { icon: ShieldAlert, title: t.feature_3, desc: t.feature_3_desc },
            ].map((f, i) => (
              <Card key={i} className="border-none shadow-md bg-muted/20">
                <CardHeader>
                  <f.icon className="h-10 w-10 text-primary mb-4" />
                  <CardTitle>{f.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section className="py-20 bg-muted/30 px-4 border-t border-b">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-16">{t.workflow_title}</h2>
          <div className="relative">
            <div className="absolute top-1/2 left-0 w-full h-1 bg-border -translate-y-1/2 hidden md:block"></div>
            <div className="grid md:grid-cols-4 gap-8 relative z-10">
              {[
                { icon: Server, title: t.step_1 },
                { icon: FileSearch, title: t.step_2 },
                { icon: Cpu, title: t.step_3 },
                { icon: TrendingUp, title: t.step_4 },
              ].map((s, i) => (
                <div key={i} className="flex flex-col items-center text-center group">
                  <div className="w-16 h-16 rounded-full bg-background border-2 border-primary flex items-center justify-center mb-6 shadow-sm group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <s.icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-semibold">{s.title}</h3>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
