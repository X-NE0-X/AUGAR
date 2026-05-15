import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

type Language = 'zh' | 'en'
type Theme = 'dark' | 'light'

interface ConfigContextType {
  lang: Language
  theme: Theme
  setLang: (language: Language) => void
  setTheme: (theme: Theme) => void
  t: (key: string) => string
}

const copy: Record<Language, Record<string, string>> = {
  zh: {
    'nav.ask': '提问',
    'nav.readings': '读数',
    'nav.almanac': '历书',
    'nav.methodology': '方法',
    'ask.headline': '问宇宙，取一则读数。',
    'ask.subline': '输入一个资产，让六个神谕引擎同时给出周期读数。',
    'ask.placeholder': '输入 SPX、HSI、NDX、VIX...',
    'ask.suggested': '推荐',
    'ask.button': '查看读数',
    'ask.empty': '这个资产还没有现成读数。',
    'ask.loading': '神谕核心正在校准',
    'reading.back': '返回提问',
    'reading.composite': '综合读数',
    'reading.engines': '神谕引擎',
    'theme.dark': '深色',
    'theme.light': '浅色',
  },
  en: {
    'nav.ask': 'Ask',
    'nav.readings': 'Readings',
    'nav.almanac': 'Almanac',
    'nav.methodology': 'Methodology',
    'ask.headline': 'Ask Universe, Get A Reading.',
    'ask.subline': 'Enter an asset and let six oracle engines read the cycle.',
    'ask.placeholder': 'Ask about SPX, HSI, NDX, VIX...',
    'ask.suggested': 'Suggested',
    'ask.button': '',
    'ask.empty': 'No reading exists for this symbol yet.',
    'ask.loading': 'Oracle core is aligning',
    'reading.back': 'Back to Ask',
    'reading.composite': 'Composite Reading',
    'reading.engines': 'Oracle Engines',
    'theme.dark': 'Dark',
    'theme.light': 'Light',
  },
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined)

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<Language>(() => (localStorage.getItem('augar-lang') as Language) || 'en')
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('augar-theme') as Theme) || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('augar-theme', theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem('augar-lang', lang)
  }, [lang])

  const value = useMemo<ConfigContextType>(() => ({
    lang,
    theme,
    setLang,
    setTheme,
    t: (key: string) => copy[lang][key] || key,
  }), [lang, theme])

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>
}

export const useConfig = () => {
  const context = useContext(ConfigContext)
  if (!context) throw new Error('useConfig must be used within ConfigProvider')
  return context
}
