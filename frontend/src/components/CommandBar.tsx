import { FormEvent, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, Loader2, Search, Sparkles } from 'lucide-react'
import { useConfig } from '../context/ConfigContext'

interface CommandBarProps {
  onAsk: (ticker: string) => void
  loading?: boolean
  compact?: boolean
}

const fallbackSymbols = ['SPX', 'HSI', 'NDX', 'VIX', 'DJI', 'FTSE', '000300.SS', '000001.SS']

export const CommandBar = ({ onAsk, loading = false, compact = false }: CommandBarProps) => {
  const [value, setValue] = useState('')
  const [symbols, setSymbols] = useState<string[]>(fallbackSymbols)
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const { t } = useConfig()

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.ok ? res.json() : Promise.reject())
      .then((data) => setSymbols(data.symbols?.length ? data.symbols : fallbackSymbols))
      .catch(() => setSymbols(fallbackSymbols))
  }, [])

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [])

  const filtered = value.trim()
    ? symbols.filter((symbol) => symbol.toLowerCase().includes(value.trim().toLowerCase())).slice(0, 6)
    : symbols.slice(0, compact ? 4 : 6)

  const submit = (event?: FormEvent) => {
    event?.preventDefault()
    const ticker = value.trim().toUpperCase()
    if (!ticker || loading) return
    setOpen(false)
    onAsk(ticker)
  }

  const choose = (symbol: string) => {
    setValue(symbol)
    setOpen(false)
    onAsk(symbol)
  }

  return (
    <div className={`command-wrap ${compact ? 'compact' : ''}`} ref={ref}>
      <form className="command-bar glass" onSubmit={submit}>
        <div className="command-leading">
          {loading ? <Loader2 className="animate-spin" size={19} /> : <Search size={19} />}
        </div>
        <input
          value={value}
          disabled={loading}
          onChange={(event) => {
            setValue(event.target.value)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          placeholder={t('ask.placeholder')}
          aria-label="Ask AUGAR about an asset"
        />
        <button className="glass-button primary-button command-submit" disabled={!value.trim() || loading} type="submit">
          <ArrowRight size={18} />
        </button>
      </form>

      <AnimatePresence>
        {open && filtered.length > 0 && (
          <motion.div
            className="command-suggestions glass"
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
          >
            <div className="suggestion-label mono">{t('ask.suggested')}</div>
            {filtered.map((symbol) => (
              <button key={symbol} onClick={() => choose(symbol)} className="suggestion-row">
                <Sparkles size={15} />
                <span>{symbol}</span>
                <small className="mono">ENTER</small>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
