import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Orbit, Search } from 'lucide-react'
import { CommandBar } from '../components/CommandBar'
import { useConfig } from '../context/ConfigContext'

const fallbackSymbols = ['SPX', 'HSI', 'NDX', 'VIX', 'DJI', 'FTSE', '000300.SS', '000001.SS']
const period = '2026-04-M'

const MONTH_NAMES = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const formatPeriod = (raw: string): string => {
  const m = raw.match(/^(\d{4})-(\d{2})-([WMQY])$/)
  if (!m) return raw
  const [, year, unit, freq] = m
  const u = parseInt(unit, 10)
  if (freq === 'M') return `${MONTH_NAMES[u] || unit} ${year}`
  if (freq === 'Q') return `Q${u} ${year}`
  if (freq === 'W') return `W${u} ${year}`
  return raw
}

const intensityLabels = ['intensity.High intensity', 'intensity.Neutral field', 'intensity.Volatile field'] as const

const ReadingsIndex = () => {
  const [symbols, setSymbols] = useState<string[]>(fallbackSymbols)
  const { t, lang } = useConfig()

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.ok ? res.json() : Promise.reject())
      .then((data) => setSymbols(data.symbols?.length ? data.symbols : fallbackSymbols))
      .catch(() => setSymbols(fallbackSymbols))
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
          <div>
            <p className="mono">{t('idx.period')}</p>
            <h2>{formatPeriod(period)}</h2>
          </div>
          <Search size={20} />
        </div>
        <div className="reading-grid">
          {symbols.map((symbol, index) => (
            <Link to={`/readings/${period}/${symbol}`} className="reading-row" key={symbol}>
              <span className="reading-symbol">{symbol}</span>
              <span className="reading-meta">
                <Orbit size={15} />
                {t(intensityLabels[index % 3])}
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
