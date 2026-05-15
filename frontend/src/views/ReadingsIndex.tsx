import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Orbit, Search } from 'lucide-react'
import { CommandBar } from '../components/CommandBar'

const fallbackSymbols = ['SPX', 'HSI', 'NDX', 'VIX', 'DJI', 'FTSE', '000300.SS', '000001.SS']
const period = '2026-04-M'

const ReadingsIndex = () => {
  const [symbols, setSymbols] = useState<string[]>(fallbackSymbols)

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
          <p className="mono readings-kicker">READING LIBRARY</p>
          <h1 className="display">Choose the asset. Then inspect the omen.</h1>
          <p>No default ticker. No user portal. This screen is the asset entry layer for existing public readings.</p>
        </div>
        <CommandBar compact onAsk={(ticker) => { window.location.href = `/readings/${period}/${ticker.toUpperCase()}` }} />
      </div>

      <div className="reading-list glass">
        <div className="reading-list-head">
          <div>
            <p className="mono">PERIOD</p>
            <h2>{period}</h2>
          </div>
          <Search size={20} />
        </div>
        <div className="reading-grid">
          {symbols.map((symbol, index) => (
            <Link to={`/readings/${period}/${symbol}`} className="reading-row" key={symbol}>
              <span className="reading-symbol">{symbol}</span>
              <span className="reading-meta">
                <Orbit size={15} />
                {index % 3 === 0 ? 'High intensity' : index % 3 === 1 ? 'Neutral field' : 'Volatile field'}
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
