const KNOWN_TAROT_SLUGS = new Set([
  'the-fool',
  'the-magician',
  'the-high-priestess',
  'the-empress',
  'the-emperor',
  'the-hierophant',
  'the-lovers',
  'the-chariot',
  'strength',
  'the-hermit',
  'wheel-of-fortune',
  'justice',
  'the-hanged-man',
  'death',
  'temperance',
  'the-devil',
  'the-tower',
  'the-star',
  'the-moon',
  'the-sun',
  'judgement',
  'the-world',
  'ace-of-wands',
  'two-of-wands',
  'three-of-wands',
  'four-of-wands',
  'five-of-wands',
  'six-of-wands',
  'seven-of-wands',
  'eight-of-wands',
  'nine-of-wands',
  'ten-of-wands',
  'page-of-wands',
  'knight-of-wands',
  'queen-of-wands',
  'king-of-wands',
  'ace-of-cups',
  'two-of-cups',
  'three-of-cups',
  'four-of-cups',
  'five-of-cups',
  'six-of-cups',
  'seven-of-cups',
  'eight-of-cups',
  'nine-of-cups',
  'ten-of-cups',
  'page-of-cups',
  'knight-of-cups',
  'queen-of-cups',
  'king-of-cups',
  'ace-of-swords',
  'two-of-swords',
  'three-of-swords',
  'four-of-swords',
  'five-of-swords',
  'six-of-swords',
  'seven-of-swords',
  'eight-of-swords',
  'nine-of-swords',
  'ten-of-swords',
  'page-of-swords',
  'knight-of-swords',
  'queen-of-swords',
  'king-of-swords',
  'ace-of-pentacles',
  'two-of-pentacles',
  'three-of-pentacles',
  'four-of-pentacles',
  'five-of-pentacles',
  'six-of-pentacles',
  'seven-of-pentacles',
  'eight-of-pentacles',
  'nine-of-pentacles',
  'ten-of-pentacles',
  'page-of-pentacles',
  'knight-of-pentacles',
  'queen-of-pentacles',
  'king-of-pentacles',
])


export const normalizeTarotName = (value: string): string => {
  return String(value)
    .split(':')[0]
    .replace(/\b(upright|reversed)\b/gi, '')
    .trim()
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export const getTarotImage = (value: string): string | null => {
  const slug = normalizeTarotName(value)
  return KNOWN_TAROT_SLUGS.has(slug)
    ? `${import.meta.env.BASE_URL}tarots/${slug}.png`
    : null
}
