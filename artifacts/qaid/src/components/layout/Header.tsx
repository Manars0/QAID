import * as React from "react"
import { Link } from "wouter"
import { Moon, Sun, Globe, Activity } from "lucide-react"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { Button } from "../ui/button"

export function Header() {
  const { theme, setTheme, language, setLanguage } = useTheme()
  const t = translations[language]

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'ar' : 'en')
  }

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4 mx-auto max-w-7xl">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight">
          <Activity className="h-6 w-6 text-primary" />
          <span>{t.app_name}</span>
        </Link>

        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={toggleLanguage} className="font-medium">
            <Globe className="h-4 w-4 mr-2 rtl:ml-2 rtl:mr-0" />
            {t.language}
          </Button>
          
          <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label={t.toggle_theme}>
            {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>
        </div>
      </div>
    </header>
  )
}
