import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

type Language = 'zh' | 'en'
type Theme = 'dark' | 'light'

interface ConfigContextType {
  lang: Language
  theme: Theme
  setLang: (language: Language) => void
  setTheme: (theme: Theme) => void
  t: (key: string) => string
  label: (key: string) => string
}

const copy: Record<Language, Record<string, string>> = {
  zh: {
    'nav.ask': '\u95ee\u5366',
    'nav.readings': '\u5366\u8c61',
    'nav.almanac': '\u5386\u4e66',
    'nav.methodology': '\u6e90\u6d41',
    'ask.headline': '\u5411\u5b87\u5b99\u53d1\u95ee\uff0c\u4ee5\u516d\u8c61\u4e3a\u7b54\u3002',
    'ask.subline': '当你在K线里找不到答案，也许答案写在星星里。',
    'ask.placeholder': '\u8f93\u5165 SPX\u3001HSI\u3001NDX\u3001VIX...',
    'ask.suggested': '\u901f\u89c8',
    'ask.button': '',
    'ask.empty': '\u8fd9\u4e2a\u8d44\u4ea7\u8fd8\u6ca1\u6709\u73b0\u6210\u8bfb\u6570\u3002',
    'ask.loading': '\u5929\u5e02\u6d41\u8f6c\uff0c\u6b63\u5728\u6821\u51c6\u661f\u56fe',
    'idx.kicker': '\u5366\u8c61\u5e93',
    'idx.headline': '\u62e9\u4e00\u6807\u7684\uff0c\u7ec6\u5bdf\u5929\u673a\u3002',
    'idx.headline.first': '\u62e9\u4e00\u6807\u7684\uff0c',
    'idx.headline.second': '\u7ec6\u5bdf\u5929\u673a\u3002',
    'idx.subline': '\u8fd9\u91cc\u662f\u5df2\u751f\u6210\u516c\u5f00\u8bfb\u6570\u7684\u8d44\u4ea7\u5165\u53e3\uff0c\u4e0d\u9700\u8981\u8d26\u6237\uff0c\u4e5f\u4e0d\u9884\u8bbe\u9ed8\u8ba4\u8d44\u4ea7\u3002',
    'idx.period': '\u5468\u671f',
    'idx.loading': '\u6b63\u5728\u6821\u51c6\u661f\u56fe...',
    'alm.title': '\u5468\u671f\u5386\u4e66',
    'alm.subtext': '\u672c\u5468\u671f\u5168\u8d44\u4ea7\u7efc\u5408\u6392\u5e8f\u4e0e\u795e\u8c15\u8bfb\u6570',
    'alm.rank': '\u6392\u4f4d',
    'alm.asset': '\u6807\u7684',
    'alm.score': '\u8bc4\u5206',
    'alm.change': '24H \u53d8\u52a8',
    'reading.back': '\u8fd4\u56de\u95ee\u5366',
    'reading.composite': '\u7efc\u5408\u89e3\u8bfb',
    'reading.engines': '\u795e\u8c15\u5f15\u64ce',
    'reading.pulse': '\u5e02\u573a\u8109\u51b2\u4e0a\u4e0b\u6587',
    'reading.polarity': '\u503e\u5411',
    'reading.intensity': '\u5f3a\u5ea6',
    'reading.period': '\u5468\u671f',
    'reading.openPulse': '\u5c55\u5f00\u8109\u51b2',
    'reading.reconciled': '\u4e2a\u5f15\u64ce\u5df2\u5408\u6210',
    'reading.compositeLead': '\u516d\u8c61\u5408\u53c2\uff0c\u503e\u5411',
    'reading.compositeMiddle': '\uff0c\u5f3a\u5ea6',
    'reading.synthesis': '\u8fd9\u662f\u7efc\u5408\u5c42\uff0c\u4e0d\u662f\u9884\u6d4b\u6807\u7b7e\u3002',
    'reading.modelConfig': '\u6a21\u578b\u914d\u7f6e',
    'reading.askAgain': '\u518d\u6b21\u63a8\u6f14',
    'reading.share': '\u5206\u4eab',
    'reading.provider': '\u8c03\u7528\u6e20\u9053',
    'reading.model': '\u6a21\u578b',
    'reading.reasoning': '\u63a8\u7406\u5f3a\u5ea6',
    'reading.apiKey': 'API Key \u73af\u5883\u53d8\u91cf',
    'reading.baseUrl': 'Base URL',
    'reading.run': '\u6309\u6b64\u914d\u7f6e\u91cd\u65b0\u751f\u6210',
    'reading.providerPlaceholder': '\u9009\u62e9\u8c03\u7528\u6e20\u9053...',
    'reading.reasoningPlaceholder': '\u9009\u62e9\u63a8\u7406\u5f3a\u5ea6...',
    'reading.customReasoning': '\u81ea\u5b9a\u4e49\u63a8\u7406\u5f3a\u5ea6',
    'reading.codexMissing': 'ChatGPT OAuth \u9700\u8981 Codex CLI\u3002\u8bf7\u5148\u5728\u7ec8\u7aef\u8fd0\u884c codex login\u3002',
    'reading.genTimeout': '\u751f\u6210\u8d85\u65f6\uff0c\u8bf7\u68c0\u67e5 provider \u914d\u7f6e\u540e\u91cd\u8bd5\u3002',
    'reading.genComplete': '\u91cd\u65b0\u751f\u6210\u5b8c\u6210',
    'reading.genFailed': '\u751f\u6210\u5931\u8d25',
    'reading.generating': '\u751f\u6210\u4e2d...',
    'reading.genCodex': 'Codex CLI \u8c03\u7528\u4e2d',
    'reading.genAPI': 'API \u8bf7\u6c42\u4e2d',
    'reading.notFound': '\u6ca1\u6709\u627e\u5230\u8bfb\u6570\u3002',
    'reading.shareCopied': '\u8bfb\u6570\u94fe\u63a5\u5df2\u590d\u5236\u3002',
    'reading.shareReady': '\u5206\u4eab\u94fe\u63a5\u5728\u5730\u5740\u680f\u91cc\u3002',
    'detail.loading': '\u6b63\u5728\u89e3\u7801\u795e\u8c15\u4fe1\u53f7...',
    'detail.overview': '\u603b\u89c8',
    'detail.raw': '\u539f\u59cb',
    'detail.visual': '\u89c6\u89c9',
    'detail.copy': '\u590d\u5236',
    'detail.copied': '\u5df2\u590d\u5236',
    'detail.signals': '\u4fe1\u53f7',
    'detail.risks': '\u98ce\u9669',
    'detail.copyOk': '\u539f\u59cb artifact \u5df2\u590d\u5236\u3002',
    'detail.copyBlocked': '\u5f53\u524d\u6d4f\u89c8\u5668\u4f1a\u8bdd\u963b\u6b62\u4e86\u526a\u8d34\u677f\u3002',
    'detail.shareOk': '\u5361\u7247\u94fe\u63a5\u5df2\u590d\u5236\u3002',
    'detail.shareFallback': '\u5206\u4eab\u94fe\u63a5\u5728\u5730\u5740\u680f\u91cc\u3002',
    'detail.loadFailed': '\u8bfb\u53d6\u5361\u7247\u8be6\u60c5\u5931\u8d25',
    'theme.dark': '\u7384\u591c',
    'theme.light': '\u7d20\u5e1b',
    'intensity.High intensity': '\u9ad8\u5f3a\u5ea6',
    'intensity.Neutral field': '\u4e2d\u6027\u573a\u57df',
    'intensity.Volatile field': '\u9707\u8361\u573a\u57df',
  },
  en: {
    'nav.ask': 'Ask',
    'nav.readings': 'Readings',
    'nav.almanac': 'Almanac',
    'nav.methodology': 'Methodology',
    'ask.headline': 'Ask Universe, Get A Reading.',
    'ask.subline': 'When the charts offer no answers, perhaps the stars do.',
    'ask.placeholder': 'Ask about SPX, HSI, NDX, VIX...',
    'ask.suggested': 'Suggested',
    'ask.button': '',
    'ask.empty': 'No reading exists for this symbol yet.',
    'ask.loading': 'Oracle core is aligning',
    'idx.kicker': 'READING LIBRARY',
    'idx.headline': 'Choose the asset. Then inspect the omen.',
    'idx.headline.first': 'Choose the asset.',
    'idx.headline.second': 'Then inspect the omen.',
    'idx.subline': 'No default ticker. No user portal. This screen is the asset entry layer for existing public readings.',
    'idx.period': 'PERIOD',
    'idx.loading': 'Aligning star charts...',
    'alm.title': 'Period Almanac',
    'alm.subtext': 'Full asset rankings and oracle guidance for the period',
    'alm.rank': 'RANK',
    'alm.asset': 'ASSET',
    'alm.score': 'SCORE',
    'alm.change': '24H CHANGE',
    'reading.back': 'Back to Ask',
    'reading.composite': 'Composite Reading',
    'reading.engines': 'Oracle Engines',
    'reading.pulse': 'Market Pulse Context',
    'reading.polarity': 'Polarity',
    'reading.intensity': 'Intensity',
    'reading.period': 'Period',
    'reading.openPulse': 'Open Pulse',
    'reading.reconciled': 'engines reconciled',
    'reading.compositeLead': 'The engines lean ',
    'reading.compositeMiddle': ' with intensity ',
    'reading.synthesis': 'This is a synthesis layer, not a prediction label.',
    'reading.modelConfig': 'Model Config',
    'reading.askAgain': 'Ask Again',
    'reading.share': 'Share',
    'reading.provider': 'Provider',
    'reading.model': 'Model',
    'reading.reasoning': 'Reasoning effort',
    'reading.apiKey': 'API key env',
    'reading.baseUrl': 'Base URL',
    'reading.run': 'Run configured reading',
    'reading.providerPlaceholder': 'Select provider...',
    'reading.reasoningPlaceholder': 'Select effort...',
    'reading.customReasoning': 'Custom reasoning effort',
    'reading.codexMissing': 'ChatGPT OAuth requires Codex CLI. Run `codex login` in terminal.',
    'reading.genTimeout': 'Generation timed out. Check provider config and retry.',
    'reading.genComplete': 'Regeneration complete',
    'reading.genFailed': 'Generation failed',
    'reading.generating': 'Generating...',
    'reading.genCodex': 'Codex CLI calling',
    'reading.genAPI': 'API calling',
    'reading.notFound': 'Reading not found.',
    'reading.shareCopied': 'Reading link copied.',
    'reading.shareReady': 'Share link is ready in the address bar.',
    'detail.loading': 'Decoding oracle signal...',
    'detail.overview': 'Overview',
    'detail.raw': 'Raw',
    'detail.visual': 'Visual',
    'detail.copy': 'COPY',
    'detail.copied': 'COPIED',
    'detail.signals': 'Signals',
    'detail.risks': 'Risk Tags',
    'detail.copyOk': 'Raw artifact copied.',
    'detail.copyBlocked': 'Clipboard is blocked in this browser session.',
    'detail.shareOk': 'Card link copied.',
    'detail.shareFallback': 'Share link is ready in the address bar.',
    'detail.loadFailed': 'Failed to load card details',
    'theme.dark': 'Dark',
    'theme.light': 'Light',
    'intensity.High intensity': 'High intensity',
    'intensity.Neutral field': 'Neutral field',
    'intensity.Volatile field': 'Volatile field',
  },
}

const LABEL_MAP: Record<string, Record<Language, string>> = {
  favorable: { zh: '\u6b63\u5411', en: 'favorable' },
  unfavorable: { zh: '\u8d1f\u5411', en: 'unfavorable' },
  positive: { zh: '\u6b63\u5411', en: 'positive' },
  negative: { zh: '\u8d1f\u5411', en: 'negative' },
  neutral: { zh: '\u4e2d\u6027', en: 'neutral' },
  bullish: { zh: '\u504f\u591a', en: 'bullish' },
  bearish: { zh: '\u504f\u7a7a', en: 'bearish' },
  bearish_neutral: { zh: '\u504f\u7a7a', en: 'bearish-neutral' },
  neutral_bullish: { zh: '\u504f\u591a', en: 'neutral bullish' },
  neutral_positive: { zh: '\u6b63\u5411', en: 'neutral positive' },
  mixed: { zh: '\u6df7\u5408', en: 'mixed' },
  high: { zh: '\u9ad8', en: 'high' },
  moderate: { zh: '\u4e2d', en: 'moderate' },
  medium: { zh: '\u4e2d', en: 'medium' },
  low: { zh: '\u4f4e', en: 'low' },
  volatile: { zh: '\u9707\u8361', en: 'volatile' },
  strong_downtrend: { zh: '\u5f3a\u4e0b\u884c', en: 'strong downtrend' },
  strong_uptrend: { zh: '\u5f3a\u4e0a\u884c', en: 'strong uptrend' },
  rising: { zh: '\u4e0a\u884c', en: 'rising' },
  falling: { zh: '\u4e0b\u884c', en: 'falling' },
  normal: { zh: '\u6b63\u5e38', en: 'normal' },
  shallow: { zh: '\u6d45\u56de\u64a4', en: 'shallow' },
  shallow_drawdown: { zh: '\u6d45\u56de\u64a4', en: 'shallow drawdown' },
  normal_volatility: { zh: '\u6b63\u5e38', en: 'normal volatility' },
  timing_risk: { zh: '\u65f6\u5e8f\u98ce\u9669', en: 'timing risk' },
  volatility: { zh: '\u6ce2\u52a8', en: 'volatility' },
  drawdown: { zh: '\u56de\u64a4', en: 'drawdown' },
  mixed_momentum: { zh: '\u52a8\u91cf\u6df7\u6742', en: 'mixed momentum' },
  headline_volatility: { zh: '\u6d88\u606f\u6ce2\u52a8', en: 'headline volatility' },
  policy_headline_sensitivity: { zh: '\u653f\u7b56\u6d88\u606f\u654f\u611f', en: 'policy headline sensitivity' },
}

const cleanLabel = (key: string): string => {
  return String(key).split(':')[0].trim().replaceAll('_', ' ')
}

const translateLabel = (lang: Language, key: string): string => {
  const clean = cleanLabel(key)
  const lowered = clean.toLowerCase().replace(/[ -]+/g, '_')
  return LABEL_MAP[lowered]?.[lang] || clean
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
    label: (key: string) => translateLabel(lang, key),
  }), [lang, theme])

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>
}

export const useConfig = () => {
  const context = useContext(ConfigContext)
  if (!context) throw new Error('useConfig must be used within ConfigProvider')
  return context
}
