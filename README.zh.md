# A.U.G.A.R.
**Ask Universe, Get A Reading.**


## 五维玄学市场预测框架 | The 5-Dimension Divination Market Forecasting Framework

***“当你在K线里找不到答案，也许答案写在星星里。”***

[![License: WTFPL](https://img.shields.io/badge/License-WTFPL-brightgreen.svg)](http://www.wtfpl.net/about/)
[![Build Status](https://img.shields.io/badge/准确率-看缘分-brightgreen)]()
[![Coverage](https://img.shields.io/badge/玄学覆盖率-500%25-purple)]()


## 🤔 这是什么

**AUGAR** 是一个基于五行八字、六爻八卦、紫微斗数、古典占星、塔罗牌，加上量化市场脉冲的市场周期解读系统。

它 **不保证** 帮你赚钱。它也不保证比猩猩掷飞镖更准。

本项目的核心哲学是：**如果市场是不可预测的，那么用5个不可预测的系统同时预测，是不是就负负得正了？**

*（答：不是。）*


## 🧠 六维引擎架构

| 维度 | 玄学体系 | 市场职责 | 核心逻辑 |
|------|----------|----------|----------|
| **🔴 八字** | 四柱命理 | 宏观大势基调 | `日主` × `十神` × `五行行业映射` |
| **🟣 紫微** | 斗数飞星 | 月度情绪与资金流向 | `流月四化` × `12宫位资金池` |
| **🟢 八卦** | 六爻纳甲 | 短线拐点与日内波动 | `价格`/`时间起卦` → `六亲持世` → `涨跌爻辞` |
| **🔵 占星** | 古典占星 | 全球性风险事件 | `外行星相位` → `入庙擢升/落陷受克` |
| **🟡 塔罗** | 伟特体系 | 周期叙事与情绪 | `Celtic Cross 十张牌` → `正逆位解读` |
| **⚪ 市场脉冲** | 量化指标 | 现实派校验 | `动量`·`波动`·`回撤` → `三脉合参` |

**融合策略**：Display Orchestrator 不做 LLM 统一裁判——六张卡片并列展示，用户自行判断。Composite score 由算术平均 + 众数极性计算，纯程序化，不接 LLM。


## 🎲 实际功能
### 1. 纯代码抽牌/起卦/排盘
每个引擎的 Program Generator（`generators/`）是纯 Python 代码，不接 LLM。塔罗用 RNG 洗牌抽 Celtic Cross 十张牌，六爻用三枚铜钱六次抛掷，八字用资产上市日推四柱，紫微用命宫起十二宫——LLM 只负责最后一步解读。

### 2. 中英双语输出
LLM 以中文 prompt 生成中文解读，后端通过 `translators` 库（Google 优先，Bing fallback）自动英译。每张卡片同时存储 `result`（中文）+ `result_en`（英文），前端按语言切换。

### 3. 多 Provider 支持
同一套生成流水线支持 DeepSeek、OpenAI、ChatGPT OAuth（本地 Codex CLI）、以及任意 OpenAI-compatible 端点。CLI `--api-key` 参数或 `.env` 环境变量传入 Key。

### 4. 静态 JSON 部署
所有生成结果落盘为 JSON（`public/data/`），前端纯静态读取。可以部署到 Vercel/Cloudflare Pages，不需要运行时数据库或 LLM 调用。


## 🚀 快速开始

```bash
git clone https://github.com/X-NE0-X/AUGAR.git
cd AUGAR
pip install -e .

# 启动完整应用（前端 + 后端）
augar serve
# 打开 http://127.0.0.1:8765

# 生成全量月度卡片（需要 LLM API Key）
$env:DEEPSEEK_API_KEY = "sk-xxx"
augar generate --all-indexes --provider deepseek --model deepseek-v4-flash

# 生成单个资产的所有引擎卡片
augar generate --symbols SPX --provider openai --model gpt-5.5

# 查看所有命令
augar --help
```

**环境变量**：复制 `.env.example` → `.env`，填入 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY`。`augar` 命令启动时自动加载。


## 🏗 实际架构

```
CLI (augar generate / serve)         Web Frontend (React + Vite)
            │                                    │
            └────────── FastAPI (:8765) ─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   Market Loader       6× Generators        LLM Interpreter
   (4× Parquet)        (pure Python)        (OpenAI / DeepSeek
   CN/HK/UK/US         tarot, wenwang        / ChatGPT OAuth)
                        bazi, ziwei               │
                        astrology,          CN prompt → CN
                        market_pulse        → translators → EN
        │                    │                    │
        └──────────────── JSON Export ───────────┘
                public/data/cards/{period}/{ticker}/{engine}.json
                public/data/readings/{period}/{ticker}.json
```

每个引擎的 **抽牌/起卦/排盘** 是纯代码（`generators/`），不接 LLM。
LLM 只负责 **解读**（`interpreter.py`），输出标准化 OracleCard JSON。


## 📦 项目结构

```
AUGAR/
  augar_engine/           ← Python 包
    api/app.py            ← FastAPI 后端
    cli.py                ← generate 命令
    entry.py              ← augar 入口（serve/build/check/generate）
    pipeline.py           ← 生成流水线
    interpreter.py        ← LLM 解读 + 中英翻译
    llm.py                ← LLM 客户端 (OpenAI/DeepSeek/ChatGPT OAuth)
    generators/           ← 纯代码引擎生成器
    exports.py            ← JSON 导出
    schemas.py            ← OracleCard / ReadingBundle 数据结构
    constants.py          ← 配置加载器 (configs/defaults.json)
  configs/
    defaults.json         ← LLM 默认参数、引擎列表、评分阈值
    llm.json              ← 各 Provider 推荐模型与参数
    market_thresholds.json ← 动量/波动/回撤分类阈值
  public/data/            ← 生成的卡片与读数（JSON）
  frontend/               ← React + TypeScript + Vite
    src/views/            ← Ask / Readings / Almanac / Methodology
  data/                   ← Parquet 市场数据 (CN/HK/UK/US)
```


## 📄 标准输出格式

每个引擎输出同一 JSON 结构，前端不做模型分歧处理：

```json
{
  "schema_version": "0.1",
  "asset": { "ticker": "SPX", "name": "SPX", "region": "US" },
  "engine": { "id": "tarot", "name": "Tarot Celtic Cross", "display_name": "塔罗" },
  "result": {
    "score": 72, "polarity": "positive", "intensity": "moderate",
    "headline": "Turning of the Wheel: From Conflict to Stability",
    "subline": "...", "short_reading": "...", "long_reading": "..."
  },
  "result_en": { "headline": "...", "subline": "...", "..." : "..." },
  "symbols": ["Nine of Swords reversed", "Seven of Cups", ...],
  "risk_tags": ["volatility", "mixed_momentum"]
}
```

卡片同时存储中英双语（`result` + `result_en`），前端按语言切换。


## 🔌 支持的 LLM Provider

| Provider | 认证 | 备注 |
|----------|------|------|
| `deepseek` | `DEEPSEEK_API_KEY` 环境变量 | deepseek-v4-flash / deepseek-v4-pro |
| `openai` | `OPENAI_API_KEY` 环境变量 | gpt-5.5 等 |
| `chatgpt_oauth` | 本地 Codex CLI OAuth | 无需 Key，需要安装 Codex |
| `openai_compatible` | `OPENAI_API_KEY` | 任意兼容端点 |
| `local` | 无需 | 本地 LLM (vllm/ollama) |


## 📄 开源协议
**[WTFPL](http://www.wtfpl.net/about/) —— Do What The Fuck You Want To Public License**


## ⚠️ 免责声明
本项目为 **娱乐目的** 创建。**不构成任何投资建议。**
- 如果按预测操作后赚钱了，那是你命中带财，不用打赏。
- 如果亏钱了，建议检查本地 git 记录，也许是你 clone 的姿势不对。
- 作者不对任何因本项目引发的财务亏损、家庭矛盾、或对玄学世界观产生动摇等后果负责。


## 🙏 鸣谢
本项目深受 **中信里昂证券风水指数** 启发。多年来，CSLA 以券商研报的严谨格式书写玄学，证明了金融圈不只有冰冷的数字，还有炽热的五行。AUGAR 试图将这份精神开源化、多维度化，让每个人都拥有自己的风水。

向 CSLA 致敬。