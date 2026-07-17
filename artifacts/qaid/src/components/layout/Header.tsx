import * as React from "react"
import { Link } from "wouter"
import { Moon, Sun, Globe } from "lucide-react"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { Button } from "../ui/button"

/** Inline SVG Q-monogram — renders correctly at any size, no external file load needed. */
function QaidIcon({ size = 28, className = "" }: { size?: number; className?: string }) {
  const id = React.useId().replace(/:/g, "")
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width={size}
      height={size}
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={`qg-${id}`} x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0F766E" />
          <stop offset="100%" stopColor="#2563EB" />
        </linearGradient>
      </defs>
      {/* Q ring — 330° arc, gap at 4-5 o'clock */}
      <path
        d="M 27 35.1 A 11.5 11.5 0 1 0 32.1 32.1"
        stroke={`url(#qg-${id})`}
        strokeWidth="3.6"
        strokeLinecap="round"
      />
      {/* Q tail — 45° ledger-line diagonal */}
      <line
        x1="32.1" y1="32.1" x2="39.7" y2="39.7"
        stroke={`url(#qg-${id})`}
        strokeWidth="3.6"
        strokeLinecap="round"
      />
    </svg>
  )
}

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
        <Link href="/" className="flex items-center gap-2.5 font-semibold text-xl tracking-tight select-none">
          <QaidIcon size={28} />
          <span className="font-semibold tracking-[0.12em]">{t.app_name}</span>
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
