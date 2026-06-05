export const FALLBACK_SYMBOLS = ['SPX', 'HSI', 'NDX', 'VIX', 'DJI', 'FTSE', '000300.SS', '000001.SS']

const uniq = (values: string[]) => Array.from(new Set(values.filter(Boolean)))

const basePath = (path: string) => {
  const base = import.meta.env.BASE_URL || '/'
  return `${base}${path.replace(/^\/+/, '')}`
}

export const readJson = async <T,>(paths: string[]): Promise<T> => {
  let lastError: unknown = null
  for (const path of paths) {
    try {
      const response = await fetch(path)
      if (!response.ok) throw new Error(`${response.status} ${path}`)
      return await response.json() as T
    } catch (error) {
      lastError = error
    }
  }
  throw lastError || new Error('Artifact not found')
}

export const readAvailableSymbols = async (): Promise<string[]> => {
  try {
    const health = await readJson<{ symbols?: string[] }>(['/api/health'])
    if (health.symbols?.length) return uniq([...health.symbols, ...FALLBACK_SYMBOLS])
  } catch {
    // Static artifacts remain the local source of truth when the API is not running.
  }

  try {
    const index = await readJson<{ symbols?: string[] }>([basePath('data/index.json')])
    if (index.symbols?.length) return uniq([...index.symbols, ...FALLBACK_SYMBOLS])
  } catch {
    // Keep the UI usable even when only known local artifacts exist.
  }

  return FALLBACK_SYMBOLS
}

export const readReading = async (period: string | undefined, ticker: string | undefined): Promise<any> => {
  if (!period || !ticker) throw new Error('Missing period or ticker')
  return readJson<any>([
    `/api/readings/${period}/${ticker}`,
    basePath(`data/readings/${period}/${ticker}.json`),
    basePath(`data/readings/${period}/${ticker}/index.json`),
  ])
}

export const readQuestionReading = async (period: string | undefined, ticker: string | undefined): Promise<any> => {
  if (!period || !ticker) throw new Error('Missing period or ticker')
  return readJson<any>([
    `/api/questions/readings/${period}/${ticker}`,
    basePath(`data/questions/readings/${period}/${ticker}.json`),
    basePath(`data/questions/readings/${period}/${ticker}/index.json`),
  ])
}

export const readCard = async (
  period: string | undefined,
  ticker: string | undefined,
  engine: string | undefined,
): Promise<any> => {
  if (!period || !ticker || !engine) throw new Error('Missing period, ticker, or engine')
  return readJson<any>([
    `/api/cards/${period}/${ticker}/${engine}`,
    basePath(`data/cards/${period}/${ticker}/${engine}.json`),
  ])
}

export const readQuestionCard = async (
  period: string | undefined,
  ticker: string | undefined,
  engine: string | undefined,
): Promise<any> => {
  if (!period || !ticker || !engine) throw new Error('Missing period, ticker, or engine')
  return readJson<any>([
    `/api/questions/cards/${period}/${ticker}/${engine}`,
    basePath(`data/questions/cards/${period}/${ticker}/${engine}.json`),
  ])
}

export const readComparison = async (): Promise<any> => {
  return readJson<any>([
    basePath('data/comparison/hsi_fsi_2020_2026.json'),
  ])
}

export const readQuestionHistory = async (): Promise<any> => {
  return readJson<any>([
    '/api/questions',
    basePath('data/questions/index.json'),
  ])
}
