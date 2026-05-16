import React from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { useMousePosition } from '../hooks/useMousePosition'
import { useConfig } from '../context/ConfigContext'

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { x, y } = useMousePosition()
  const { lang, setLang, theme, setTheme, t } = useConfig()
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <div
      className="app-shell"
      style={isHome ? {
        '--mx': `${x}px`,
        '--my': `${y}px`,
      } as React.CSSProperties : undefined}
    >
      {isHome && <div className="spatial-light" style={{ left: x, top: y }} />}
      <header className="app-topbar">
        <Link to="/" className="wordmark text-only" aria-label="AUGAR home">
          <span className="wordmark-text">AUGAR</span>
        </Link>

        <nav className="topnav" aria-label="Primary navigation">
          <NavLink to="/">{t('nav.ask')}</NavLink>
          <NavLink to="/readings">{t('nav.readings')}</NavLink>
          <NavLink to="/almanac">{t('nav.almanac')}</NavLink>
          <a href="#methodology">{t('nav.methodology')}</a>
        </nav>

        <div className="settings-cluster">
          <div className="segmented" aria-label="Language">
            <button className={lang === 'zh' ? 'active' : ''} onClick={() => setLang('zh')} title="Chinese">
              CN
            </button>
            <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')} title="English">
              EN
            </button>
          </div>
          <button
            className="glass-button"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          >
            {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
            <span className="mono">{theme === 'dark' ? t('theme.dark') : t('theme.light')}</span>
          </button>
        </div>
      </header>
      <main>{children}</main>
    </div>
  )
}
