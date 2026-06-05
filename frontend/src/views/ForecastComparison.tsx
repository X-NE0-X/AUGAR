import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { ExternalLink, LineChart, RefreshCw } from 'lucide-react'
import { useConfig } from '../context/ConfigContext'
import { readComparison } from '../lib/artifacts'

type Point = {
  ordinal: number
  label: string
  zodiac: string
  start: string
  end: string
  clsa_index: number
  augar_score: number | null
  augar_index: number | null
  price_close: number | null
  price_index: number | null
  actual_return: number | null
  augar_rationale: string
  augar_rationale_zh?: string
  augar_rationale_en?: string
}

type YearPayload = {
  year: number
  source_url: string
  chart_js_url: string
  price_as_of: Record<string, number | string>
  augar: {
    model: string
    headline: string
    summary: string
    summary_zh?: string
    summary_en?: string
    annual_bias: string
    confidence: string
  }
  monthly: Point[]
}

const WIDTH = 1160
const HEIGHT = 430
const PAD = { left: 66, right: 34, top: 34, bottom: 58 }

const pathFor = (values: Array<number | null>) => {
  const points = values
    .map((value, index) => ({ value, index }))
    .filter((item): item is { value: number; index: number } => item.value !== null)
  if (!points.length) return ''
  const xSpan = WIDTH - PAD.left - PAD.right
  const ySpan = HEIGHT - PAD.top - PAD.bottom
  return points.map((point, i) => {
    const x = PAD.left + (point.index / Math.max(values.length - 1, 1)) * xSpan
    const y = PAD.top + ((100 - point.value) / 100) * ySpan
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`
  }).join(' ')
}

const pointPosition = (value: number | null, index: number, count: number) => {
  if (value === null) return null
  const x = PAD.left + (index / Math.max(count - 1, 1)) * (WIDTH - PAD.left - PAD.right)
  const y = PAD.top + ((100 - value) / 100) * (HEIGHT - PAD.top - PAD.bottom)
  return { x, y }
}

const pct = (value: number | null | undefined) => {
  if (!Number.isFinite(value)) return 'n/a'
  return `${(Number(value) * 100).toFixed(1)}%`
}

const num = (value: number | null | undefined, digits = 1) => {
  if (!Number.isFinite(value)) return 'n/a'
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits })
}

const ForecastComparison = () => {
  const [data, setData] = useState<any>(null)
  const [year, setYear] = useState<number | null>(null)
  const [activeOrdinal, setActiveOrdinal] = useState<number | null>(null)
  const { t, label, lang } = useConfig()

  useEffect(() => {
    readComparison().then((payload) => {
      setData(payload)
      const years = payload?.years?.map((item: YearPayload) => item.year) || []
      setYear(years.includes(2026) ? 2026 : years[years.length - 1] || null)
    }).catch(() => setData(null))
  }, [])

  const selected: YearPayload | null = useMemo(() => {
    return data?.years?.find((item: YearPayload) => item.year === year) || null
  }, [data, year])

  const chart = useMemo(() => {
    const rows = selected?.monthly || []
    const clsa = rows.map((row) => Number.isFinite((row as any).clsa_percent) ? Number((row as any).clsa_percent) : null)
    const augar = rows.map((row) => Number.isFinite((row as any).augar_percent) ? Number((row as any).augar_percent) : null)
    const price = rows.map((row) => Number.isFinite((row as any).price_percent) ? Number((row as any).price_percent) : null)
    return { rows, clsa, augar, price }
  }, [selected])

  if (!data || !selected) {
    return (
      <section className="comparison-page page">
        <div className="reading-loading">
          <RefreshCw className="animate-spin" size={36} color="var(--amber)" />
          <p className="mono">{t('cmp.loading')}</p>
        </div>
      </section>
    )
  }

  const latestActual = [...selected.monthly].reverse().find((row) => row.price_close)
  const activeIndex = activeOrdinal ?? Math.min(1, chart.rows.length - 1)
  const activeRow = chart.rows[activeIndex]
  const summaryCopy = lang === 'zh'
    ? selected.augar.summary_zh || selected.augar.summary
    : selected.augar.summary_en || selected.augar.summary
  const rationaleFor = (row: Point) => lang === 'zh'
    ? row.augar_rationale_zh || row.augar_rationale
    : row.augar_rationale_en || row.augar_rationale

  return (
    <section className="comparison-page page">
      <div className="comparison-shell">
        <header className="comparison-header">
          <div>
            <h1 className="display gold-title">{t('cmp.title')}</h1>
            <p>{t('cmp.subline')}</p>
          </div>
          <div className="comparison-year-strip glass">
            {data.years.map((item: YearPayload) => (
              <button key={item.year} className={item.year === year ? 'active' : ''} onClick={() => setYear(item.year)}>
                {item.year}
              </button>
            ))}
          </div>
        </header>

        <section className="comparison-grid">
          <div className="comparison-chart-panel glass">
            <div className="comparison-panel-head">
              <div>
                <p className="mono panel-kicker">{selected.year} / HSI</p>
                <h2>{selected.augar.headline}</h2>
              </div>
              <LineChart size={22} />
            </div>
            <div className="comparison-chart-wrap comparison-floating-chart">
              <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="HSI normalized price chart">
                <line x1={PAD.left} y1={PAD.top + (HEIGHT - PAD.top - PAD.bottom) / 2} x2={WIDTH - PAD.right} y2={PAD.top + (HEIGHT - PAD.top - PAD.bottom) / 2} className="chart-zero" />
                {[0, 50, 100].map((tick) => {
                  const y = PAD.top + ((100 - tick) / 100) * (HEIGHT - PAD.top - PAD.bottom)
                  return <text key={tick} x={16} y={y + 4} className="chart-axis">{tick}%</text>
                })}
                {chart.rows.map((row, index) => {
                  const x = PAD.left + (index / Math.max(chart.rows.length - 1, 1)) * (WIDTH - PAD.left - PAD.right)
                  return (
                    <g key={row.ordinal}>
                      <line x1={x} y1={PAD.top} x2={x} y2={HEIGHT - PAD.bottom} className="chart-gridline" />
                      <text x={x} y={HEIGHT - 16} className="chart-month">{row.end.slice(5)}</text>
                    </g>
                  )
                })}
                <path d={pathFor(chart.price)} className="chart-line price" />
                {chart.rows.map((row, index) => {
                  const pos = pointPosition(chart.price[index], index, chart.rows.length)
                  return (
                    <g key={`points-${row.ordinal}`}>
                      {pos && (
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r={activeIndex === index ? 7 : 4.5}
                          className={`chart-point price ${activeIndex === index ? 'active' : ''}`}
                        />
                      )}
                      <rect
                        x={PAD.left + (index / Math.max(chart.rows.length - 1, 1)) * (WIDTH - PAD.left - PAD.right) - 28}
                        y={PAD.top}
                        width={56}
                        height={HEIGHT - PAD.top - PAD.bottom}
                        className="chart-hitbox"
                        onMouseEnter={() => setActiveOrdinal(index)}
                        onFocus={() => setActiveOrdinal(index)}
                      />
                    </g>
                  )
                })}
              </svg>
              {activeRow && (
                <div className="comparison-tooltip">
                  <b>{activeRow.start} / {activeRow.end}</b>
                  <span>CLSA {num((activeRow as any).clsa_percent, 1)}% / {num(activeRow.clsa_index, 0)} ({activeRow.zodiac})</span>
                  <span>AUGAR {num((activeRow as any).augar_percent, 1)}% / {num(activeRow.augar_index, 1)}</span>
                  <span>{t('cmp.price')} {num((activeRow as any).price_percent, 1)}% / {pct(activeRow.actual_return)}</span>
                </div>
              )}
            </div>
            <div className="score-strip-shell">
              <ScoreStrip
                label="AUGAR"
                rows={chart.rows}
                values={chart.augar}
                raw={(row) => num(row.augar_index, 1)}
                activeIndex={activeIndex}
                setActiveOrdinal={setActiveOrdinal}
                tone="augar"
              />
              <ScoreStrip
                label="CLSA FSI"
                rows={chart.rows}
                values={chart.clsa}
                raw={(row) => `${num(row.clsa_index, 0)} (${row.zodiac})`}
                activeIndex={activeIndex}
                setActiveOrdinal={setActiveOrdinal}
                tone="clsa"
              />
            </div>
            <div className="comparison-legend">
              <span><i className="price" />{t('cmp.price')}</span>
              <span><i className="augar" />AUGAR score strip</span>
              <span><i className="clsa" />CLSA score strip</span>
              <a href={selected.source_url} target="_blank" rel="noreferrer">
                CLSA source <ExternalLink size={13} />
              </a>
            </div>
          </div>

          <aside className="comparison-summary glass">
            <p className="mono panel-kicker">{t('cmp.snapshot')}</p>
            <div className="metric-row"><span>{t('cmp.bias')}</span><b>{label(selected.augar.annual_bias || 'neutral')}</b></div>
            <div className="metric-row"><span>{t('cmp.confidence')}</span><b>{label(selected.augar.confidence || 'low')}</b></div>
            <div className="metric-row"><span>{t('cmp.asOf')}</span><b>{String(selected.price_as_of.as_of)}</b></div>
            <div className="metric-row"><span>{t('cmp.latest')}</span><b>{latestActual ? num(latestActual.price_close) : 'n/a'}</b></div>
            <p className="comparison-summary-copy">{summaryCopy}</p>
          </aside>
        </section>

        <section className="comparison-table glass">
          <div className="comparison-table-head">
            <span>{t('cmp.period')}</span>
            <span>CLSA</span>
            <span>AUGAR</span>
            <span>{t('cmp.price')}</span>
            <span>{t('cmp.actual')}</span>
          </div>
          {selected.monthly.map((row) => (
            <div className="comparison-row" key={row.ordinal}>
              <span>
                <b>{row.end}</b>
                <small>{row.start} / {row.end}</small>
              </span>
              <strong>{num(row.clsa_index, 0)} ({row.zodiac})</strong>
              <span>
                <strong>{num(row.augar_index, 1)}</strong>
                <small>{rationaleFor(row)}</small>
              </span>
              <strong>{num(row.price_close, 0)}</strong>
              <strong>{pct(row.actual_return)}</strong>
            </div>
          ))}
        </section>
      </div>
    </section>
  )
}

const ScoreStrip = ({
  label,
  rows,
  values,
  raw,
  activeIndex,
  setActiveOrdinal,
  tone,
}: {
  label: string
  rows: Point[]
  values: Array<number | null>
  raw: (row: Point) => string
  activeIndex: number
  setActiveOrdinal: (value: number) => void
  tone: 'augar' | 'clsa'
}) => (
  <div className={`score-strip ${tone}`}>
    <div className="score-strip-label mono">{label}</div>
    <div className="score-strip-track">
      {rows.map((row, index) => {
        const value = values[index]
        const height = value === null ? 0 : Math.max(8, Math.min(100, value))
        return (
          <button
            key={row.ordinal}
            className={activeIndex === index ? 'active' : ''}
            style={{ '--score': `${height}%` } as CSSProperties}
            onMouseEnter={() => setActiveOrdinal(index)}
            onFocus={() => setActiveOrdinal(index)}
            title={`${row.start} / ${row.end}: ${raw(row)}`}
          >
            <i />
            <span>{row.end.slice(5)}</span>
            <b>{raw(row)}</b>
          </button>
        )
      })}
    </div>
  </div>
)

export default ForecastComparison
