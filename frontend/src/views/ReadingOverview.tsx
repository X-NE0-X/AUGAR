import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronDown, ChevronLeft, RefreshCw, Share2, SlidersHorizontal, Sparkles, X } from 'lucide-react'
import { useToast } from '../components/Toast'
import { useConfig } from '../context/ConfigContext'
import { readReading } from '../lib/artifacts'
import { getTarotImage } from '../lib/tarotAssets'

const MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const formatPeriod = (raw: string | undefined): string => {
  if (!raw) return ''
  const m = raw.match(/^(\d{4})-(\d{2})-([WMQY])$/)
  if (!m) return raw
  const [, year, unit, freq] = m
  const u = parseInt(unit, 10)
  if (freq === 'M') return `${MONTHS[u] || unit} ${year}`
  if (freq === 'Q') return `Q${u} ${year}`
  if (freq === 'W') return `W${u} ${year}`
  return raw
}

const engineLabels: Record<string, string> = {
  tarot: 'Tarot',
  wenwang: 'Wenwang',
  bazi: 'BaZi',
  ziwei: 'Ziwei',
  astrology: 'Astrology',
  market_pulse: 'Market Pulse',
}

const engineOrder = ['tarot', 'wenwang', 'bazi', 'ziwei', 'astrology', 'market_pulse']
const cleanTag = (value: string): string => String(value).split(':')[0].trim()

const ReadingOverview = () => {
  const { period, ticker } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const { lang, label: trLabel, t } = useConfig()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [configOpen, setConfigOpen] = useState(false)
  const [providerOpen, setProviderOpen] = useState(false)
  const [reasoningOpen, setReasoningOpen] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState('chatgpt_oauth')
  const [selectedReasoning, setSelectedReasoning] = useState('low')
  const [customReasoning, setCustomReasoning] = useState('')
  const [configModel, setConfigModel] = useState('gpt-5.5')
  const [configBaseUrl, setConfigBaseUrl] = useState('')
  const [configApiKey, setConfigApiKey] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generatingElapsed, setGeneratingElapsed] = useState(0)
  const [providerConnected, setProviderConnected] = useState<boolean | null>(null)
  const [providerChecking, setProviderChecking] = useState(false)

  useEffect(() => {
    let cancelled = false
    if (selectedProvider !== 'chatgpt_oauth') {
      setProviderConnected(null)
      return
    }
    setProviderChecking(true)
    setProviderConnected(null)
    ;(async () => {
      try {
        const r = await fetch('/api/health/codex', { signal: AbortSignal.timeout(10000) })
        const d = await r.json()
        if (!cancelled) setProviderConnected(!!(d.available && d.logged_in))
      } catch {
        if (!cancelled) setProviderConnected(false)
      } finally {
        if (!cancelled) setProviderChecking(false)
      }
    })()
    return () => { cancelled = true }
  }, [selectedProvider])

  useEffect(() => {
    if (!generating) {
      setGeneratingElapsed(0)
      return
    }
    setGeneratingElapsed(0)
    const interval = setInterval(() => setGeneratingElapsed((s) => s + 1), 1000)
    return () => clearInterval(interval)
  }, [generating])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    readReading(period, ticker)
      .then((json) => {
        if (cancelled) return
        setData(json)
        setLoading(false)
      })
      .catch(() => {
        if (cancelled) return
        showToast(t('reading.notFound'), 'error')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [period, ticker, showToast, t])

  const composite = data?.composite || {}
  const ui = {
    ask: t('reading.back'),
    askAgain: t('reading.askAgain'),
    share: t('reading.share'),
    composite: t('reading.composite'),
    pulse: t('reading.pulse'),
    polarity: t('reading.polarity'),
    intensity: t('reading.intensity'),
    period: t('reading.period'),
    openPulse: t('reading.openPulse'),
    reconciled: t('reading.reconciled'),
    modelConfig: t('reading.modelConfig'),
    provider: t('reading.provider'),
    model: t('reading.model'),
    reasoning: t('reading.reasoning'),
    apiKey: t('reading.apiKey'),
    baseUrl: t('reading.baseUrl'),
    run: t('reading.run'),
    synthesis: t('reading.synthesis'),
    providerPlaceholder: t('reading.providerPlaceholder'),
    reasoningPlaceholder: t('reading.reasoningPlaceholder'),
    codexMissing: t('reading.codexMissing'),
  }
  const cards = useMemo(() => {
    return [...(data?.cards || [])].sort((a: any, b: any) => {
      return engineOrder.indexOf(a.engine?.id) - engineOrder.indexOf(b.engine?.id)
    })
  }, [data])
  const dominant = useMemo(() => {
    const symbols = new Set<string>()
    ;(composite.dominant_symbols || composite.symbols || []).forEach((symbol: string) => symbols.add(symbol))
    cards.forEach((card: any) => card.symbols?.slice(0, 2).forEach((symbol: string) => symbols.add(symbol)))
    return Array.from(symbols).slice(0, 6)
  }, [cards, composite])

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      showToast(t('reading.shareCopied'), 'success')
    } catch {
      showToast(t('reading.shareReady'), 'info')
    }
  }

  const handleRun = async () => {
    if (!period || !ticker || generating) return
    setGenerating(true)
    const reasoning = selectedReasoning === 'custom' ? customReasoning : selectedReasoning
    try {
      if (selectedProvider === 'chatgpt_oauth') {
        try {
          const r = await fetch('/api/health/codex', { signal: AbortSignal.timeout(10000) })
          const d = await r.json()
          if (!d.available || !d.logged_in) {
            showToast(ui.codexMissing, 'error')
            setGenerating(false)
            return
          }
        } catch {
          showToast(ui.codexMissing, 'error')
          setGenerating(false)
          return
        }
      }
      const body: Record<string, unknown> = { period, symbols: [ticker], provider: selectedProvider, model: configModel, reasoning_effort: reasoning || undefined, force: true }
      if (selectedProvider !== 'chatgpt_oauth') {
        if (configBaseUrl) body.base_url = configBaseUrl
        if (configApiKey) body.api_key = configApiKey
      }
      const resp = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(selectedProvider === 'chatgpt_oauth' ? 180_000 : 90_000),
      })
      if (!resp.ok) {
        const err = await resp.text()
        throw new Error(err || `HTTP ${resp.status}`)
      }
      setConfigOpen(false)
      showToast(t('reading.genComplete'), 'success')
      setTimeout(() => navigate(0), 600)
    } catch (e: any) {
      if (e?.name === 'TimeoutError' || e?.name === 'AbortError') showToast(t('reading.genTimeout'), 'error')
      else showToast(e?.message || t('reading.genFailed'), 'error')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return (
    <div className="reading-loading page">
      <RefreshCw className="animate-spin" size={40} color="var(--amber)" />
      <p className="mono">{t('idx.loading')}</p>
    </div>
  )

  if (!data) return (
    <div className="reading-loading page">
      <p>{t('reading.notFound')}</p>
    </div>
  )

  return (
    <motion.section className="reading-page page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <header className="reading-actionbar glass">
        <div className="reading-identity">
          <Link to="/" className="back-link">
            <ChevronLeft size={18} />
            <span className="mono">{ui.ask}</span>
          </Link>
          <div className="identity-rule" />
          <div>
            <h2>{ticker}</h2>
            <p className="mono">{formatPeriod(period)}</p>
          </div>
        </div>

        <div className="reading-actions">
          <button className="glass-button" onClick={() => setConfigOpen(true)}>
            <SlidersHorizontal size={16} />
            <span>{ui.askAgain}</span>
          </button>
          <button className="glass-button" onClick={handleShare}>
            <Share2 size={16} />
            <span>{ui.share}</span>
          </button>
        </div>
      </header>

      <div className="reading-content">
        <section className="reading-hero-grid">
          <motion.div className="composite-panel glass" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
            <div className="composite-copy">
              <p className="mono panel-kicker">{ui.composite.toUpperCase()}</p>
              <h1 className="display gold-title">{composite.headline || composite.polarity || 'Composite Signal'}</h1>
              <p>
                {lang === 'zh'
                  ? <>{t('reading.compositeLead')}<b>{trLabel(composite.polarity || 'neutral')}</b>{t('reading.compositeMiddle')}<b>{trLabel(composite.intensity || 'medium')}</b></>
                  : <>The engines lean <b>{trLabel(composite.polarity || 'neutral')}</b> with <b>{trLabel(composite.intensity || 'medium')}</b> intensity. {ui.synthesis}</>}
              </p>
              <div className="dominant-row">
                {(composite.dominant_symbols || dominant).slice(0, 5).map((symbol: string) => (
                  <span key={symbol}>{trLabel(cleanTag(symbol))}</span>
                ))}
              </div>
            </div>
            <div className="score-oracle">
              <div className="score-ring" style={{ '--score': composite.score || 50 } as CSSProperties}>
                <strong>{composite.score || 50}</strong>
              </div>
              <div className="score-caption">
                <span>{cards.length}</span>
                <small>{ui.reconciled}</small>
              </div>
            </div>
          </motion.div>

          <aside className="market-panel glass">
            <p className="mono panel-kicker">{ui.pulse.toUpperCase()}</p>
            {[
              [ui.polarity, trLabel(composite.polarity || 'neutral')],
              [ui.intensity, trLabel(composite.intensity || 'medium')],
              [ui.period, formatPeriod(period) || '2026-04-M'],
            ].map(([lbl, value]) => (
              <div className="metric-row" key={String(lbl)}>
                <span>{lbl}</span>
                <b>{value}</b>
              </div>
            ))}
            <button className="glass-button primary-button" onClick={() => navigate(`/readings/${period}/${ticker}/market_pulse`)}>
              {ui.openPulse}
            </button>
          </aside>
        </section>

        <section className="engine-orbit-strip glass">
          {cards.map((card: any, index: number) => (
            <button key={card.engine?.id} onClick={() => navigate(`/readings/${period}/${ticker}/${card.engine?.id}`)}>
              <span>{engineLabels[card.engine?.id] || card.engine?.display_name}</span>
              <b>{card.result.score}</b>
              <small>{trLabel(card.result.polarity)}</small>
              <i style={{ animationDelay: `${index * 120}ms` }} />
            </button>
          ))}
        </section>

        <section className="engine-visual-grid">
          {cards.map((card: any, index: number) => (
            <motion.article
              className="engine-visual-card glass"
              key={card.engine.id}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => navigate(`/readings/${period}/${ticker}/${card.engine?.id}`)}
            >
              <EngineVisual card={card} />
              <div className="engine-card-copy">
                <div className="engine-card-head">
                  <p className="mono">{engineLabels[card.engine?.id] || card.engine?.display_name}</p>
                  <strong>{card.result.score}</strong>
                </div>
                <h3>{card.result.headline}</h3>
                <p>{card.result.subline}</p>
                <div className="symbol-row">
                  {card.symbols?.slice(0, 4).map((symbol: string) => <span key={symbol}>{trLabel(cleanTag(symbol))}</span>)}
                </div>
              </div>
            </motion.article>
          ))}
        </section>
      </div>

      <AnimatePresence>
        {configOpen && (
          <motion.div className="config-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setConfigOpen(false)}>
            <motion.div className="config-panel glass" initial={{ y: 28, scale: 0.97 }} animate={{ y: 0, scale: 1 }} exit={{ y: 18, scale: 0.98 }} onClick={(e) => e.stopPropagation()}>
              <div className="config-head">
                <div>
                  <p className="mono panel-kicker">{ui.modelConfig.toUpperCase()}</p>
                  <h2>{ui.askAgain}</h2>
                </div>
                <button className="glass-button" onClick={() => setConfigOpen(false)}><X size={16} /></button>
              </div>
              <div className="config-grid">
                <label>
                  <span className="provider-label-row">
                    {ui.provider}
                    {providerChecking ? <span className="provider-dot checking" title="Checking codex...">...</span>
                     : providerConnected === true ? <span className="provider-dot connected" title="Codex OAuth active">&#10003;</span>
                     : providerConnected === false ? <span className="provider-dot disconnected" title="Codex not logged in">&#10007;</span>
                     : null}
                  </span>
                  <CustomSelect open={providerOpen} setOpen={setProviderOpen} value={selectedProvider} setValue={setSelectedProvider}
                    options={[{value:'chatgpt_oauth',label:'ChatGPT OAuth'},{value:'openai',label:'OpenAI API'},{value:'deepseek',label:'DeepSeek API'},{value:'openai_compatible',label:'OpenAI-compatible'},{value:'local',label:'Local LLM'}]}
                    placeholder={ui.providerPlaceholder} />
                </label>
                <label>{ui.model}<input value={configModel} onChange={(e) => setConfigModel(e.target.value)} /></label>
                <label>{ui.reasoning}
                  <CustomSelect open={reasoningOpen} setOpen={setReasoningOpen} value={selectedReasoning} setValue={setSelectedReasoning}
                    options={[{value:'low',label:'Low'},{value:'medium',label:'Medium'},{value:'high',label:'High'},{value:'xhigh',label:'Extra High'},{value:'custom',label:'Custom'}]}
                    placeholder={ui.reasoningPlaceholder} />
                </label>
                {selectedProvider !== 'chatgpt_oauth' && (
                  <label>{ui.baseUrl}<input placeholder="http://localhost:8000/v1" value={configBaseUrl} onChange={(e) => setConfigBaseUrl(e.target.value)} /></label>
                )}
              </div>
              {selectedReasoning === 'custom' && (
                <div className="config-grid" style={{ marginTop: '0.8rem' }}>
                  <label style={{ gridColumn: '1 / -1' }}>{t('reading.customReasoning')}
                    <input value={customReasoning} onChange={(e) => setCustomReasoning(e.target.value)} placeholder="e.g. minimal" />
                  </label>
                </div>
              )}
              {selectedProvider !== 'chatgpt_oauth' && (
                <label className="config-api-key">{ui.apiKey}
                  <input placeholder="OPENAI_API_KEY / DEEPSEEK_API_KEY / AUGAR_LLM_API_KEY" value={configApiKey} onChange={(e) => setConfigApiKey(e.target.value)} />
                </label>
              )}
              <button className="glass-button primary-button config-submit" onClick={handleRun} disabled={generating}>
                {generating ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
                {generating ? t('reading.generating') : ui.run}
              </button>
              {generating && (
                <div className="config-progress mono">
                  {selectedProvider === 'chatgpt_oauth' ? `${t('reading.genCodex')} / ${generatingElapsed}s` : `${t('reading.genAPI')} / ${generatingElapsed}s`}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  )
}

const CustomSelect = ({ open, setOpen, value, setValue, options, placeholder }: {
  open: boolean; setOpen: (v: boolean) => void; value: string; setValue: (v: string) => void
  options: { value: string; label: string }[]; placeholder: string
}) => {
  const selected = options.find((o) => o.value === value)
  return (
    <div className="custom-select" tabIndex={0} onBlur={() => setTimeout(() => setOpen(false), 150)}>
      <button type="button" className="custom-select-trigger" onClick={() => setOpen(!open)}>
        <span className={selected ? '' : 'placeholder'}>{selected ? selected.label : placeholder}</span>
        <ChevronDown size={14} style={{ transform: open ? 'rotate(180deg)' : undefined, transition: 'transform 180ms ease' }} />
      </button>
      {open && (
        <div className="custom-select-dropdown">
          {options.map((opt) => (
            <button key={opt.value} type="button" className={opt.value === value ? 'active' : ''}
              onClick={() => { setValue(opt.value); setOpen(false) }}>{opt.label}</button>
          ))}
        </div>
      )}
    </div>
  )
}

const EngineVisual = ({ card }: { card: any }) => {
  const id = card.engine?.id
  const symbols = card.symbols?.length ? card.symbols : card.result?.symbols || []
  if (id === 'tarot') {
    const labels = card.symbols?.slice(0, 3) || ['Past', 'Present', 'Future']
    return (
      <div className="tarot-spread">
        {labels.map((label: string, index: number) => {
          const image = getTarotImage(label)
          return (
            <div className="tarot-card" key={label}>
              {image && <img src={image} alt={cleanTag(label)} />}
              <span>{index + 1}</span>
              <b>{cleanTag(label)}</b>
            </div>
          )
        })}
      </div>
    )
  }
  if (id === 'wenwang') return <div className="hexagram-visual">{[1, 2, 3, 4, 5, 6].map((line) => <i key={line} className={line % 2 ? 'solid' : 'broken'} />)}</div>
  if (id === 'bazi') return <div className="bazi-wheel">{['Wood', 'Fire', 'Earth', 'Metal', 'Water'].map((x, i) => <span key={x} style={{ '--i': i } as CSSProperties}>{x}</span>)}</div>
  if (id === 'ziwei') return <div className="ziwei-palace">{Array.from({ length: 12 }).map((_, i) => <i key={i} style={{ '--i': i } as CSSProperties} />)}<b>{cleanTag(symbols[0] || 'Ming')}</b></div>
  if (id === 'astrology') return <div className="astro-arc">{['Moon', 'Sun', 'Mars', 'Jupiter'].map((x) => <span key={x}>{x}</span>)}</div>
  return <div className="pulse-wave">{Array.from({ length: 18 }).map((_, i) => <i key={i} style={{ height: `${28 + ((i * 17) % 56)}%` }} />)}</div>
}

export default ReadingOverview
