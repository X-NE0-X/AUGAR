import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Check, ChevronLeft, Copy, Share2, Terminal } from 'lucide-react'
import { useToast } from '../components/Toast'
import { useConfig } from '../context/ConfigContext'
import { readCard } from '../lib/artifacts'
import { getTarotImage } from '../lib/tarotAssets'

const engineLabels: Record<string, string> = {
  tarot: 'Tarot',
  wenwang: 'Wenwang',
  bazi: 'BaZi',
  ziwei: 'Ziwei',
  astrology: 'Astrology',
  market_pulse: 'Market Pulse',
}

const cleanTag = (value: string): string => String(value).split(':')[0].trim()

const EngineDetail = () => {
  const { period, ticker, engine } = useParams()
  const { showToast } = useToast()
  const { t, label: trLabel, lang } = useConfig()
  const [card, setCard] = useState<any>(null)
  const [terminalMode, setTerminalMode] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let cancelled = false
    readCard(period, ticker, engine)
      .then((json) => {
        if (!cancelled) setCard(json)
      })
      .catch(() => {
        if (!cancelled) showToast(t('detail.loadFailed'), 'error')
      })
    return () => { cancelled = true }
  }, [period, ticker, engine, showToast, t])

  const rawPayload = useMemo(() => {
    return JSON.stringify(card?.raw_artifact || card?.raw_ref || card || {}, null, 2)
  }, [card])

  const handleCopyRaw = async () => {
    try {
      await navigator.clipboard.writeText(rawPayload)
      setCopied(true)
      showToast(t('detail.copyOk'), 'success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast(t('detail.copyBlocked'), 'info')
    }
  }

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      showToast(t('detail.shareOk'), 'success')
    } catch {
      showToast(t('detail.shareFallback'), 'info')
    }
  }

  if (!card) {
    return (
      <div className="engine-detail-loading page">
        <p className="mono">{t('detail.loading')}</p>
      </div>
    )
  }

  const id = card.engine?.id || engine || 'tarot'
  const label = engineLabels[id] || card.engine?.display_name || id
  const r = lang === 'en' && card?.result_en?.headline ? card.result_en : card.result || {}

  return (
    <motion.section className={`engine-detail-page page engine-${id}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <header className="engine-detail-bar glass">
        <div className="engine-detail-identity">
          <Link to={`/readings/${period}/${ticker}`} className="back-link">
            <ChevronLeft size={18} />
            <span className="mono">{t('detail.overview')}</span>
          </Link>
          <div className="identity-rule" />
          <div>
            <h2>{label}</h2>
            <p className="mono">{ticker} / {period}</p>
          </div>
        </div>

        <div className="reading-actions">
          <button className="glass-button" onClick={() => setTerminalMode((value) => !value)}>
            <Terminal size={16} />
            <span>{terminalMode ? t('detail.visual') : t('detail.raw')}</span>
          </button>
          <button className="glass-button" onClick={handleShare}>
            <Share2 size={16} />
            <span>{t('reading.share')}</span>
          </button>
        </div>
      </header>

      <main className="engine-detail-shell">
        <AnimatePresence mode="wait">
          {terminalMode ? (
            <motion.section
              key="terminal"
              className="engine-terminal glass"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
            >
              <div className="terminal-head">
                <span className="mono">RAW_ARTIFACT.JSON</span>
                <button onClick={handleCopyRaw}>
                  {copied ? <Check size={15} /> : <Copy size={15} />}
                  <span>{copied ? t('detail.copied') : t('detail.copy')}</span>
                </button>
              </div>
              <pre className="mono">{rawPayload}</pre>
            </motion.section>
          ) : (
            <motion.section
              key="visual"
              className="engine-canvas glass"
              initial={{ opacity: 0, y: 18, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12, scale: 0.98 }}
            >
              <div className="engine-canvas-copy">
                <p className="mono panel-kicker">{label.toUpperCase()}</p>
                <h1 className="display gold-title">{r.headline}</h1>
                <p className="engine-subline">{r.subline}</p>
                <p className="engine-reading">{r.long_reading}</p>

                <div className="engine-meta-grid">
                  <MetaBlock title={t('detail.signals')} items={card.symbols || []} translate={trLabel} />
                  <MetaBlock title={t('detail.risks')} items={card.risk_tags || []} translate={trLabel} danger />
                </div>
              </div>

              <div className="engine-art-board">
                <EngineHeroVisual card={card} />
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </main>
    </motion.section>
  )
}

const MetaBlock = ({ title, items, translate, danger = false }: { title: string; items: string[]; translate: (value: string) => string; danger?: boolean }) => (
  <div className="engine-meta-block">
    <h4 className="mono">{title}</h4>
    <div>
      {items.slice(0, 8).map((item) => (
        <span className={danger ? 'danger' : ''} key={item}>{translate(cleanTag(item))}</span>
      ))}
    </div>
  </div>
)

const EngineHeroVisual = ({ card }: { card: any }) => {
  const id = card.engine?.id
  const symbols = card.symbols?.length ? card.symbols : ['Signal', 'Cycle', 'Risk']

  if (id === 'tarot') {
    const labels = symbols.slice(0, 10)
    return (
      <div className="hero-tarot">
        {labels.map((label: string, index: number) => {
          const image = getTarotImage(label)
          const isReversed = label.toLowerCase().includes('reversed')
          return (
            <div className="hero-tarot-card" key={label}>
              {image && <img src={image} alt={cleanTag(label)} />}
              <small>{String(index + 1).padStart(2, '0')} · {isReversed ? '逆' : '正'}</small>
              <b>{cleanTag(label)}</b>
            </div>
          )
        })}
      </div>
    )
  }

  if (id === 'wenwang') {
    return (
      <div className="hero-hexagram">
        {[1, 2, 3, 4, 5, 6].map((line) => <i key={line} className={line % 2 ? 'solid' : 'broken'} />)}
        <b>{cleanTag(symbols[0])}</b>
      </div>
    )
  }

  if (id === 'bazi') {
    return (
      <div className="hero-bazi">
        {['Wood', 'Fire', 'Earth', 'Metal', 'Water'].map((item, index) => (
          <span key={item} style={{ '--i': index } as CSSProperties}>{item}</span>
        ))}
        <b>{cleanTag(symbols[0])}</b>
      </div>
    )
  }

  if (id === 'ziwei') {
    return (
      <div className="hero-ziwei">
        {Array.from({ length: 12 }).map((_, index) => (
          <i key={index} style={{ '--i': index } as CSSProperties}>{index + 1}</i>
        ))}
        <b>{cleanTag(symbols[0])}</b>
      </div>
    )
  }

  if (id === 'astrology') {
    return (
      <div className="hero-astrology">
        {['Moon', 'Sun', 'Mars', 'Jupiter', 'Saturn'].map((planet, index) => (
          <span key={planet} style={{ '--i': index } as CSSProperties}>{planet}</span>
        ))}
        <b>{cleanTag(symbols[0])}</b>
      </div>
    )
  }

  return (
    <div className="hero-pulse">
      {Array.from({ length: 34 }).map((_, index) => (
        <i key={index} style={{ height: `${24 + ((index * 23) % 70)}%` }} />
      ))}
      <b>{cleanTag(symbols[0])}</b>
    </div>
  )
}

export default EngineDetail
