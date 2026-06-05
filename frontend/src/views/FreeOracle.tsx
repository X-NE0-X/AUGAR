import { useEffect, useState } from 'react'
import { ArrowUpRight, RefreshCw, Sparkles } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useToast } from '../components/Toast'
import { useConfig } from '../context/ConfigContext'
import { readQuestionHistory } from '../lib/artifacts'

type QuestionRecord = {
  title: string
  ticker: string
  period: string
  question: string
  score: number
  polarity: string
  href: string
}

const FreeOracle = () => {
  const [title, setTitle] = useState('')
  const [question, setQuestion] = useState('')
  const [records, setRecords] = useState<QuestionRecord[]>([])
  const [loading, setLoading] = useState(false)
  const { t, label } = useConfig()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const loadHistory = () => {
    readQuestionHistory()
      .then((payload) => setRecords(payload.records || []))
      .catch(() => setRecords([]))
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const submit = async () => {
    if (!title.trim() || !question.trim() || loading) return
    setLoading(true)
    try {
      const response = await fetch('/api/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title.trim(), question: question.trim() }),
      })
      if (!response.ok) throw new Error(await response.text())
      const payload = await response.json()
      const href = payload?.record?.href
      loadHistory()
      if (href) navigate(href)
    } catch (error: any) {
      showToast(error?.message || t('oracle.failed'), 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="free-oracle-page page">
      <div className="free-oracle-shell">
        <header className="free-oracle-header">
          <h1 className="display gold-title">{t('oracle.title')}</h1>
          <p>{t('oracle.subline')}</p>
        </header>

        <section className="free-oracle-box glass">
          <label>
            <span className="mono">{t('oracle.titleLabel')}</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={t('oracle.titlePlaceholder')} />
          </label>
          <label>
            <span className="mono">{t('oracle.questionLabel')}</span>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={t('oracle.questionPlaceholder')} />
          </label>
          <button className="glass-button primary-button oracle-submit" disabled={loading || !title.trim() || !question.trim()} onClick={submit}>
            {loading ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
            <span>{loading ? t('oracle.asking') : t('oracle.submit')}</span>
          </button>
        </section>

        <div className="oracle-divider" />

        <section className="oracle-history">
          {!records.length && (
            <div className="oracle-history-empty glass">
              <Sparkles size={18} />
              <span>{t('oracle.historyEmpty')}</span>
            </div>
          )}
          {records.map((record) => (
            <Link className="oracle-history-card glass" to={`/questions/${record.period}/${record.ticker}`} key={`${record.period}-${record.ticker}`}>
              <div>
                <span className="mono">{record.period}</span>
                <ArrowUpRight size={15} />
              </div>
              <h3>{record.title}</h3>
              <p>{record.question}</p>
              <footer>
                <b>{record.score}</b>
                <small>{label(record.polarity)}</small>
              </footer>
            </Link>
          ))}
        </section>
      </div>
    </section>
  )
}

export default FreeOracle
