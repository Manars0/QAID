import * as React from "react"
import { Link } from "wouter"
import { Moon, Sun, Globe } from "lucide-react"
import { useTheme } from "../theme-provider"
import { translations } from "../../lib/i18n"
import { getLogoSrc } from "../../lib/logo"
import { Button } from "../ui/button"

export function Header() {
  const { theme, setTheme, language, setLanguage } = useTheme()
  const t = translations[language]

  const toggleLanguage = () => setLanguage(language === 'en' ? 'ar' : 'en')
  const toggleTheme   = () => setTheme(theme === 'dark' ? 'light' : 'dark')

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80 shadow-[0_1px_3px_rgba(0,0,0,0.06)]">
      <div className="container flex h-16 items-center justify-between px-4 mx-auto max-w-7xl">

        {/* Logo — switches automatically with theme */}
        <Link href="/" className="flex items-center select-none shrink-0">
          <img
            key={theme}
            src={getLogoSrc(theme)}
            alt="QAID"
            className="h-9 w-auto object-contain"
            style={{ background: "transparent", border: "none", boxShadow: "none" }}
            draggable={false}
          />
        </Link>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleLanguage}
            className="font-medium text-muted-foreground hover:text-foreground"
          >
            <Globe className="h-4 w-4 mr-1.5 rtl:ml-1.5 rtl:mr-0 shrink-0" />
            {t.language}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label={t.toggle_theme}
            className="text-muted-foreground hover:text-foreground"
          >
            {theme === "dark"
              ? <Sun  className="h-4 w-4" />
              : <Moon className="h-4 w-4" />}
          </Button>
        </div>

      </div>
    </header>
  )
}
