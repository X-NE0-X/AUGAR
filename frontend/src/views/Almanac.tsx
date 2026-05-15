import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useToast } from '../components/Toast'
import { Trophy, TrendingUp, TrendingDown } from 'lucide-react'

const Almanac = () => {
  const [rankings, setRankings] = useState<any[]>([])
  const { showToast } = useToast()

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        // Mocking some scores for the Almanac
        const mockRankings = data.symbols.map((s: string) => ({
          symbol: s,
          score: Math.floor(Math.random() * 60) + 30,
          change: (Math.random() * 4 - 2).toFixed(2)
        })).sort((a: any, b: any) => b.score - a.score)
        setRankings(mockRankings)
      })
      .catch(() => showToast('Failed to load almanac', 'error'))
  }, [showToast])

  return (
    <div style={{ flex: 1, padding: '126px 40px 40px', overflowY: 'auto' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <header style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '12px' }}>Period Almanac</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Universe rankings and omens for 2026-04-M</p>
        </header>

        <section className="glass" style={{ borderRadius: '24px', padding: '0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.02)' }}>
                <th style={{ padding: '20px 24px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--text-muted)' }}>RANK</th>
                <th style={{ padding: '20px 24px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--text-muted)' }}>ASSET</th>
                <th style={{ padding: '20px 24px', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>SCORE</th>
                <th style={{ padding: '20px 24px', textAlign: 'right', fontSize: '0.8rem', color: 'var(--text-muted)' }}>24H CHANGE</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((item, i) => (
                <motion.tr
                  key={item.symbol}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  style={{ borderBottom: '1px solid var(--glass-border)', cursor: 'pointer' }}
                  onClick={() => { window.location.href = `/readings/2026-04-M/${item.symbol}` }}
                >
                  <td style={{ padding: '20px 24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      {i < 3 ? <Trophy size={16} color={i === 0 ? '#ffd700' : i === 1 ? '#c0c0c0' : '#cd7f32'} /> : <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{i + 1}</span>}
                    </div>
                  </td>
                  <td style={{ padding: '20px 24px' }}>
                    <Link to={`/readings/2026-04-M/${item.symbol}`} style={{ fontWeight: 600, textDecoration: 'none' }}>{item.symbol}</Link>
                  </td>
                  <td style={{ padding: '20px 24px', textAlign: 'center' }}>
                    <div style={{ 
                      display: 'inline-block',
                      padding: '4px 12px',
                      borderRadius: '8px',
                      background: item.score > 60 ? 'rgba(139, 227, 125, 0.1)' : item.score < 45 ? 'rgba(255, 107, 95, 0.1)' : 'rgba(255,255,255,0.05)',
                      color: item.score > 60 ? 'var(--favorable)' : item.score < 45 ? 'var(--unfavorable)' : 'var(--text-primary)',
                      fontWeight: 600
                    }}>
                      {item.score}
                    </div>
                  </td>
                  <td style={{ padding: '20px 24px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px', color: item.change > 0 ? 'var(--favorable)' : 'var(--unfavorable)' }}>
                      {item.change > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                      <span className="mono">{item.change}%</span>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  )
}

export default Almanac
