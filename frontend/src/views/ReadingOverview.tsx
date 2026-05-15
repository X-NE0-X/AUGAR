import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronLeft, RefreshCw, Share2, SlidersHorizontal, Sparkles, X } from 'lucide-react'
import { useToast } from '../components/Toast'
import { useConfig } from '../context/ConfigContext'

const engineLabels: Record<string, string> = {
  tarot: 'Tarot',
  wenwang: 'Wenwang',
  bazi: 'BaZi',
  ziwei: 'Ziwei',
  astrology: 'Astrology',
  market_pulse: 'Market Pulse',
}

const engineOrder = ['tarot', 'wenwang', 'bazi', 'ziwei', 'astrology', 'market_pulse']

const ReadingOverview = () => {
  const { period, ticker } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const { lang } = useConfig()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [configOpen, setConfigOpen] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetch(`/api/readings/${period}/${ticker}`)
      .then((res) => res.ok ? res.json() : Promise.reject())
      .then((json) => {
        setData(json)
        setLoading(false)
      })
      .catch(() => {
        showToast('Reading not found', 'error')
        setLoading(false)
      })
  }, [period, ticker, showToast])

  const composite = data?.composite || {}
  const ui = lang === 'zh'
    ? {
        ask: '提问',
        askAgain: '再次提问',
        share: '分享',
        composite: '综合读数',
        pulse: '市场脉冲上下文',
        polarity: '倾向',
        intensity: '强度',
        period: '周期',
        openPulse: '打开脉冲',
        reconciled: '个引擎已合成',
        modelConfig: '模型配置',
        provider: '调用渠道',
        model: '模型',
        reasoning: '推理强度',
        apiKey: 'API Key 环境变量',
        baseUrl: 'Base URL',
        temperature: 'Temperature',
        run: '按此配置重新生成',
        synthesis: '这是综合层，不是预测标签。',
        configToast: '模型配置入口已就绪，等待后端生成接口接线。',
      }
    : {
        ask: 'ASK',
        askAgain: 'Ask Again',
        share: 'Share',
        composite: 'Composite Reading',
        pulse: 'Market Pulse Context',
        polarity: 'Polarity',
        intensity: 'Intensity',
        period: 'Period',
        openPulse: 'Open Pulse',
        reconciled: 'engines reconciled',
        modelConfig: 'Model Config',
        provider: 'Provider',
        model: 'Model',
        reasoning: 'Reasoning effort',
        apiKey: 'API key env',
        baseUrl: 'Base URL',
        temperature: 'Temperature',
        run: 'Run configured reading',
        synthesis: 'This is a synthesis layer, not a prediction label.',
        configToast: 'Model config UI is ready for backend wiring.',
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
    const url = window.location.href
    try {
      await navigator.clipboard.writeText(url)
      showToast('Reading link copied.', 'success')
    } catch {
      showToast('Share link is ready in the address bar.', 'info')
    }
  }

  if (loading) return (
    <div className="reading-loading page">
        <RefreshCw className="animate-spin" size={40} color="var(--amber)" />
      <p className="mono">{lang === 'zh' ? '正在校准星图...' : 'Aligning star charts...'}</p>
    </div>
  )

  if (!data) return (
    <div className="reading-loading page">
      <p>{lang === 'zh' ? '没有找到读数。' : 'Reading not found.'}</p>
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
            <p className="mono">{period}</p>
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
                  ? <>六个引擎综合倾向为 <b>{composite.polarity}</b>，强度为 <b>{composite.intensity}</b>。{ui.synthesis}</>
                  : <>The engines lean <b>{composite.polarity}</b> with <b>{composite.intensity}</b> intensity. {ui.synthesis}</>}
              </p>
              <div className="dominant-row">
                {(composite.dominant_symbols || dominant).slice(0, 5).map((symbol: string) => (
                  <span key={symbol}>{symbol}</span>
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
              [ui.polarity, composite.polarity || 'neutral'],
              [ui.intensity, composite.intensity || 'medium'],
              [ui.period, period || '2026-04-M'],
            ].map(([label, value]) => (
              <div className="metric-row" key={label}>
                <span>{label}</span>
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
              <small>{card.result.polarity}</small>
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
                  {card.symbols?.slice(0, 4).map((symbol: string) => <span key={symbol}>{symbol}</span>)}
                </div>
              </div>
            </motion.article>
          ))}
        </section>
      </div>

      <AnimatePresence>
        {configOpen && (
          <motion.div className="config-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="config-panel glass" initial={{ y: 28, scale: 0.97 }} animate={{ y: 0, scale: 1 }} exit={{ y: 18, scale: 0.98 }}>
              <div className="config-head">
                <div>
                  <p className="mono panel-kicker">{ui.modelConfig.toUpperCase()}</p>
                  <h2>{ui.askAgain}</h2>
                </div>
                <button className="glass-button" onClick={() => setConfigOpen(false)}><X size={16} /></button>
              </div>
              <div className="config-grid">
                <label>{ui.provider}<select defaultValue="chatgpt_oauth"><option value="chatgpt_oauth">ChatGPT OAuth</option><option value="openai">OpenAI API</option><option value="openai_compatible">OpenAI-compatible</option><option value="local">Local LLM</option></select></label>
                <label>{ui.model}<input defaultValue="gpt-5.5" /></label>
                <label>{ui.reasoning}<select defaultValue="low"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
                <label>{ui.apiKey}<input defaultValue="OPENAI_API_KEY / AUGAR_LLM_API_KEY" /></label>
                <label>{ui.baseUrl}<input placeholder="http://localhost:8000/v1" /></label>
                <label>{ui.temperature}<input defaultValue="0.4" /></label>
              </div>
              <button className="glass-button primary-button config-submit" onClick={() => showToast(ui.configToast, 'info')}>
                <Sparkles size={16} />
                {ui.run}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  )
}

const EngineVisual = ({ card }: { card: any }) => {
  const id = card.engine?.id
  const symbols = card.symbols?.length ? card.symbols : card.result?.symbols || []
  if (id === 'tarot') {
    const labels = card.symbols?.slice(0, 3) || ['Past', 'Present', 'Future']
    return <div className="tarot-spread">{labels.map((label: string, index: number) => <div className="tarot-card" key={label}><span>{index + 1}</span><b>{label}</b></div>)}</div>
  }
  if (id === 'wenwang') return <div className="hexagram-visual">{[1, 2, 3, 4, 5, 6].map((line) => <i key={line} className={line % 2 ? 'solid' : 'broken'} />)}</div>
  if (id === 'bazi') return <div className="bazi-wheel">{['Wood', 'Fire', 'Earth', 'Metal', 'Water'].map((x, i) => <span key={x} style={{ '--i': i } as CSSProperties}>{x}</span>)}</div>
  if (id === 'ziwei') return <div className="ziwei-palace">{Array.from({ length: 12 }).map((_, i) => <i key={i} style={{ '--i': i } as CSSProperties} />)}<b>{symbols[0] || 'Ming'}</b></div>
  if (id === 'astrology') return <div className="astro-arc">{['Moon', 'Sun', 'Mars', 'Jupiter'].map((x) => <span key={x}>{x}</span>)}</div>
  return <div className="pulse-wave">{Array.from({ length: 18 }).map((_, i) => <i key={i} style={{ height: `${28 + ((i * 17) % 56)}%` }} />)}</div>
}

export default ReadingOverview
