import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useToast } from '../components/Toast'
import { useConfig } from '../context/ConfigContext'
import { Trophy } from 'lucide-react'

const PERIOD = '2026-05-17-1942'

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

const Almanac = () => {
  const [rankings, setRankings] = useState<any[]>([])
  const { showToast } = useToast()
  const { t, label: trLabel } = useConfig()
  const navigate = useNavigate()

  useEffect(() => {
    (async () => {
      try {
        const healthResp = await fetch('/api/health')
        const health = await healthResp.json()
        const symbols: string[] = health.symbols?.length ? health.symbols : []
        const results: any[] = []
        for (const symbol of symbols) {
          try {
            const r = await fetch(`/api/readings/${PERIOD}/${symbol}`)
            if (!r.ok) continue
            const reading = await r.json()
            results.push({
              symbol,
              score: reading.composite?.score ?? 50,
              polarity: reading.composite?.polarity ?? 'neutral',
            })
          } catch { /* skip missing readings */ }
        }
        if (results.length) setRankings(results.sort((a, b) => b.score - a.score))
        else showToast('No reading data for this period.', 'info')
      } catch {
        showToast('Failed to load almanac', 'error')
      }
    })()
  }, [showToast])

  const medalColor = (i: number) => i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : i === 2 ? '#cd7f32' : undefined

  return (
    <div className="almanac-page page">
      <div className="almanac-wrap">
        <header className="almanac-header">
          <h1 className="display gold-title">{t('alm.title')}</h1>
          <p>
            {t('alm.subtext')}{' '}
            <span className="period-label-tooltip" title={`Format: YYYY-MM-FREQ (${PERIOD})`}>{formatPeriod(PERIOD)}</span>
          </p>
        </header>

        <section className="almanac-table glass">
          <div className="almanac-thead">
            <span>{t('alm.rank')}</span>
            <span>{t('alm.asset')}</span>
            <span>{t('alm.score')}</span>
            <span>{t('reading.polarity')}</span>
          </div>
          <div className="almanac-tbody">
            {rankings.map((item, i) => (
              <motion.div
                key={item.symbol}
                className="almanac-row"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                onClick={() => navigate(`/readings/${PERIOD}/${item.symbol}`)}
              >
                <span>
                  {i < 3 ? <Trophy size={16} color={medalColor(i)} /> : <span className="mono rank-num">{i + 1}</span>}
                </span>
                <span>
                  <Link to={`/readings/${PERIOD}/${item.symbol}`} onClick={(e) => e.stopPropagation()} className="almanac-symbol">
                    {item.symbol}
                  </Link>
                </span>
                <span>
                  <span className={`almanac-score ${item.score > 60 ? 'high' : item.score < 45 ? 'low' : ''}`}>
                    {item.score}
                  </span>
                </span>
                <span className="mono almanac-polarity">{trLabel(item.polarity || 'neutral')}</span>
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default Almanac



