import { motion } from 'framer-motion'
import { useConfig } from '../context/ConfigContext'

const ENGINES: { id: string; zh: { name: string; short: string; long: string }; en: { name: string; short: string; long: string } }[] = [
  {
    id: 'tarot',
    zh: {
      name: '塔罗 · Celtic Cross',
      short: '十张牌，一次完整的周期叙事。',
      long: '塔罗是西方神秘学传统中最具叙事密度的占卜体系。AUGAR 使用 Celtic Cross 牌阵——从当下、挑战、根基、过往、目标、近未来、自我、环境、希望与恐惧、直到最终结局——十张牌构成一条完整的因果弧线。它不是回答"涨还是跌"，而是摊开一张市场在这一周期中走过的心理地图。',
    },
    en: {
      name: 'Tarot · Celtic Cross',
      short: 'Ten cards. One complete cycle narrative.',
      long: "Tarot is the most narratively dense divination system in Western esoteric tradition. AUGAR employs the Celtic Cross spread — from Present, Crossing, Root, Past, Goal, Near Future, Self, Environment, Hopes & Fears, to Outcome — ten cards forming a complete causal arc. It does not answer \"up or down\". It lays out the psychological map the market traverses during this cycle.",
    },
  },
  {
    id: 'wenwang',
    zh: {
      name: '文王卦 · 六爻',
      short: '六次铜钱，一卦之象。',
      long: '文王六爻卦源自《周易》，以三枚铜钱六次抛掷生成六爻，组成本卦与变卦。AUGAR 将市场视为问卦者，资产为所问之事。妻财为收益、官鬼为风险、子孙为流动性、父母为消息、兄弟为竞争分流。卦象不给出确切价格，但给出市场中力量对抗的拓扑结构。',
    },
    en: {
      name: 'Wenwang Liuyao · Six Lines',
      short: 'Six coin tosses. One hexagram.',
      long: "Wenwang Liuyao originates from the I Ching, generating six lines through three-coin tosses to form a primary hexagram and its transformation. AUGAR treats the market as the querent, the asset as the subject. Wealth line governs returns; Officer line governs risk; Children line governs liquidity; Parent line governs information; Brother line governs competitive diversion. The hexagram does not predict a price — it reveals the topology of forces contending within the market.",
    },
  },
  {
    id: 'bazi',
    zh: {
      name: '子平八字 · 四柱',
      short: '年、月、日、时，四柱推命。',
      long: '八字命理学以出生时刻的年月日时四柱天干地支为底，分析五行生克制化。在 AUGAR 中，资产被赋予一个"出生代用时刻"——以其上市日或指数基日为基准——生成八字盘面。配合当前周期的流年流月，判断该资产在此时段是"得时得地"还是"受压受克"。这不是迷信，而是将资产的周期性格编码为一套近乎生物节律的符号系统。',
    },
    en: {
      name: 'Zi Ping BaZi · Four Pillars',
      short: 'Year, month, day, hour — destiny in four pillars.',
      long: "BaZi destiny analysis uses the Four Pillars — year, month, day, hour — expressed in Heavenly Stems and Earthly Branches, to analyze the five-element dynamics of creation and control. In AUGAR, each asset is assigned a birth proxy — based on its listing date or index base date — to generate a BaZi chart. Combined with the current period's annual and monthly cycles, the engine assesses whether the asset is \"in season and in place\" or \"under pressure and restraint\". This is not superstition — it encodes the asset's cyclical temperament into a symbolic system resembling biological rhythm.",
    },
  },
  {
    id: 'ziwei',
    zh: {
      name: '紫微斗数 · 星盘',
      short: '十二宫，百星拱照。',
      long: '紫微斗数是中国古代最精细的星命体系，以出生时刻定命宫，在十二宫中排布紫微、天府、七杀、破军等百余星曜。AUGAR 将其用于资产周期解读：命宫为资产本质，兄弟宫为同类竞争，财帛宫为收益能力，迁移宫为外部资金流动。星曜在十二宫中的聚散辉映，揭示了资产在周期内的根基、机遇与暗礁。',
    },
    en: {
      name: 'Ziwei Doushu · Purple Star',
      short: 'Twelve palaces. A hundred stars.',
      long: "Ziwei Doushu is the most refined stellar destiny system in ancient China, determining the Life Palace from birth time and arranging over a hundred stars — Ziwei, Tianfu, Qisha, Pojun — across twelve palaces. AUGAR applies it to asset cycle interpretation: Life Palace governs the asset's nature; Siblings Palace governs competitive peers; Wealth Palace governs earning capacity; Migration Palace governs external capital flows. The gathering and dispersal of stars across the twelve palaces reveals the asset's foundation, opportunities, and hidden perils within the cycle.",
    },
  },
  {
    id: 'astrology',
    zh: {
      name: '西洋占星 · 星座周期',
      short: '市场亦有星座与月相。',
      long: '占星学将黄道十二宫与行星运动作为解读人间事务的框架。AUGAR 为每个资产分配一个星座代用符——基于其行业、波动特性和历史行为——并追踪当前太阳星座、月相和主要行星相位。这不是在预言天体影响市场，而是在问：如果市场也有出生星盘，它现在正走在哪一段黄道叙事里？',
    },
    en: {
      name: 'Western Astrology · Zodiac Cycle',
      short: 'Markets have signs and moon phases too.',
      long: "Astrology uses the twelve zodiac signs and planetary movements as a framework for interpreting human affairs. AUGAR assigns each asset a zodiac proxy — based on its sector, volatility profile, and historical behavior — and tracks the current solar sign, moon phase, and major planetary aspects. This is not about claiming celestial bodies influence markets. It is asking: if the market had a birth chart, which zodiacal narrative is it walking through right now?",
    },
  },
  {
    id: 'market_pulse',
    zh: {
      name: '市场脉冲 · 量化脉诊',
      short: '动量、波动、回撤，三脉合参。',
      long: '市场脉冲是 AUGAR 的"现实主义占卜"引擎。它不依赖任何神秘学传统，而是将21日/63日动量、年化波动率和最大回撤三类市场指标编码为叙事。这不是技术分析——它不做交易信号，不画支撑阻力线。它只是把冷冰冰的数字，用一种可以和其他神谕并列的语言，陈述当前市场的脉象。',
    },
    en: {
      name: 'Market Pulse · Quantitative Reading',
      short: 'Momentum, volatility, drawdown — three pulses.',
      long: "Market Pulse is AUGAR's \"realist oracle\" engine. It draws on no esoteric tradition — instead, it encodes three categories of market indicators — 21-day and 63-day momentum, annualized volatility, and maximum drawdown — into narrative form. This is not technical analysis. It does not produce trading signals or draw support and resistance lines. It simply restates the cold numbers in a language that can stand alongside the other oracles, describing the market's current pulse.",
    },
  },
]

const Methodology = () => {
  const { lang } = useConfig()
  const isZh = lang === 'zh'

  return (
    <motion.div className="methodology-page page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="methodology-wrap">
        <header className="methodology-header">
          <h1 className="display gold-title">{isZh ? '神谕源流' : 'The Oracles'}</h1>
          <p>
            {isZh
              ? '六种认知框架，六种解读世界的方式。它们并非彼此竞争，而是从不同维度照亮同一片市场。选择你最不信的那个——那往往是最值得听的声音。'
              : 'Six cognitive frameworks. Six ways of reading the world. They do not compete — they illuminate the same market from different dimensions. Choose the one you trust least — that is often the voice most worth hearing.'}
          </p>
        </header>

        <div className="methodology-grid">
          {ENGINES.map((engine, i) => (
            <motion.article
              className="methodology-card glass"
              key={engine.id}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <div className="methodology-index mono">{String(i + 1).padStart(2, '0')}</div>
              <h2 className="display">{isZh ? engine.zh.name : engine.en.name}</h2>
              <p className="methodology-short">{isZh ? engine.zh.short : engine.en.short}</p>
              <p className="methodology-long">{isZh ? engine.zh.long : engine.en.long}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default Methodology
