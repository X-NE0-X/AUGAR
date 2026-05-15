import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CommandBar } from '../components/CommandBar'
import { OracleCore } from '../components/OracleCore'
import { useToast } from '../components/Toast'
import { useConfig } from '../context/ConfigContext'

const suggested = ['SPX', 'HSI', 'NDX', 'VIX', 'DJI', 'FTSE']

const Ask = () => {
  const [status, setStatus] = useState<'idle' | 'generating' | 'success'>('idle')
  const navigate = useNavigate()
  const { showToast } = useToast()
  const { t } = useConfig()

  const handleAsk = async (ticker: string) => {
    const normalized = ticker.toUpperCase()
    const period = '2026-04-M'
    setStatus('generating')

    try {
      const reading = await fetch(`/api/readings/${period}/${normalized}`)
      if (reading.ok) {
        setStatus('success')
        setTimeout(() => navigate(`/readings/${period}/${normalized}`), 420)
        return
      }

      const generate = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ period, symbols: [normalized], provider: 'history', force: false }),
      })

      if (generate.ok) {
        setStatus('success')
        setTimeout(() => navigate(`/readings/${period}/${normalized}`), 420)
        return
      }

      showToast(t('ask.empty'), 'error')
      setStatus('idle')
    } catch {
      showToast(t('ask.empty'), 'error')
      setStatus('idle')
    }
  }

  return (
    <section className="ask-screen page">
      <motion.div
        className="arrival-orbit"
        initial={{ opacity: 0, scale: 0.62, rotate: -28 }}
        animate={{ opacity: [0, 1, 0.72], scale: [0.62, 1.18, 1], rotate: 0 }}
        transition={{ duration: 1.75, ease: [0.16, 1, 0.3, 1] }}
      />
      <div className="ask-copy">
        <motion.h1
          className="display gold-title"
          initial={{ opacity: 0, y: 18, filter: 'blur(12px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ delay: 1.0, duration: 0.82, ease: 'easeOut' }}
        >
          {t('ask.headline')}
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 12, filter: 'blur(8px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ delay: 1.18, duration: 0.7, ease: 'easeOut' }}
        >
          {t('ask.subline')}
        </motion.p>
      </div>

      <motion.div
        className="core-field"
        initial={{ opacity: 0, scale: 0.44, filter: 'blur(18px)' }}
        animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
        transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }}
      >
        <OracleCore status={status} />
      </motion.div>

      <motion.div
        className="ask-command"
        initial={{ opacity: 0, y: 22, filter: 'blur(10px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        transition={{ delay: 1.34, duration: 0.75, ease: 'easeOut' }}
      >
        <CommandBar onAsk={handleAsk} loading={status === 'generating'} />
        <div className="suggested-assets">
          <span className="mono">{t('ask.suggested')}</span>
          {suggested.map((symbol) => (
            <button key={symbol} onClick={() => handleAsk(symbol)}>
              {symbol}
            </button>
          ))}
        </div>
      </motion.div>
      {status === 'generating' && <div className="ask-status mono">{t('ask.loading')}</div>}
    </section>
  )
}

export default Ask
