import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'
import { ArrowUpRight, ChevronDown, Orbit, Search } from 'lucide-react'
import { CommandBar } from '../components/CommandBar'
import { useConfig } from '../context/ConfigContext'
import { FALLBACK_SYMBOLS, readAvailableSymbols } from '../lib/artifacts'

const DEFAULT_PERIOD = '2026-05-17-1942'

const formatPeriod = (raw: string): string => {
  // timestamp: YYYY-MM-DD-HHMM
  const tm = raw.match(/^(\d{4})-(\d{2})-(\d{2})-(\d{2})(\d{2})$/)
  if (tm) return `${tm[1]}-${tm[2]}-${tm[3]} ${tm[4]}:${tm[5]} UTC`
  return raw
}

const ReadingsIndex = () => {
  const [symbols, setSymbols] = useState<string[]>(FALLBACK_SYMBOLS)
  const [period, setPeriod] = useState(DEFAULT_PERIOD)
  const [periods, setPeriods] = useState<string[]>([])
  const headingRef = useRef<HTMLHeadingElement>(null)
  const [periodOpen, setPeriodOpen] = useState(false)
  const { t, lang } = useConfig()

  useEffect(() => {
    readAvailableSymbols().then(setSymbols).catch(() => setSymbols(FALLBACK_SYMBOLS))
    fetch('/api/periods')
      .then(r => r.json())
      .then(d => {
        const p = d.periods || []
        setPeriods(p)
        if (p.length) setPeriod(p[0])
      })
      .catch(() => {})
  }, [])

  return (
    <section className="readings-index page">
      <div className="readings-hero">
        <div>
          <p className="mono readings-kicker">{t('idx.kicker')}</p>
          {lang === 'zh'
            ? <h1 className="display">{t('idx.headline')}</h1>
            : (
              <h1 className="display two-line-title">
                <span>{t('idx.headline.first')}</span>
                <span>{t('idx.headline.second')}</span>
              </h1>
            )}
          <p>{t('idx.subline')}</p>
        </div>
        <CommandBar compact onAsk={(ticker) => { window.location.href = `/readings/${period}/${ticker.toUpperCase()}` }} />
      </div>

      <div className="reading-list glass">
        <div className="reading-list-head">
          <div style={{ position: 'relative' }}>
            <p className="mono">{t('idx.period')}</p>
            <h2 ref={headingRef} className="period-heading" onClick={() => setPeriodOpen(!periodOpen)}>
              {formatPeriod(period)}
              <ChevronDown size={15} style={{ marginLeft: '0.4rem', transform: periodOpen ? 'rotate(180deg)' : undefined, transition: 'transform 180ms ease' }} />
            </h2>
            {periodOpen && periods.length > 0 && createPortal(
              <div className="period-dropdown glass" style={{
                position: 'fixed',
                top: headingRef.current ? headingRef.current.getBoundingClientRect().bottom + 8 : 0,
                left: headingRef.current ? headingRef.current.getBoundingClientRect().left : 0,
              }} onClick={e => e.stopPropagation()}>
                {periods.map((p: string) => (
                  <button key={p} className={p === period ? 'active' : ''}
                    onClick={() => { setPeriod(p); setPeriodOpen(false) }}>
                    {formatPeriod(p)}
                  </button>
                ))}
              </div>,
              document.body
            )}
          </div>
          <Search size={20} />
        </div>
        <div className="reading-grid">
          {symbols.map((symbol, index) => (
            <Link to={`/readings/${period}/${symbol}`} className="reading-row" key={symbol}>
              <span className="reading-symbol">{symbol}</span>
              <span className="reading-meta">
                <Orbit size={15} />
                {t(['intensity.High intensity', 'intensity.Neutral field', 'intensity.Volatile field'][index % 3])}
              </span>
              <ArrowUpRight size={18} />
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}

export default ReadingsIndex




