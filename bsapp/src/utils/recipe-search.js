const SYNONYM_GROUPS = [
  ['炒蛋', '炒鸡蛋', '鸡蛋', '蛋'],
  ['番茄', '西红柿'],
]

const STOP_WORDS = ['的', '和', '与', '加', '配', '做', '菜', '餐']
const PREFERENCE_ALIASES = {
  '清淡': 'light',
  '少油': 'light',
  '低油': 'light',
  '不油': 'light',
  '香辣': 'spicy',
  '麻辣': 'spicy',
  '辣': 'spicy',
  '高蛋白': 'high_protein',
  '蛋白': 'high_protein',
  '低碳': 'low_carb',
  '低碳水': 'low_carb',
  '素食': 'vegetarian',
  '蔬菜': 'vegetarian',
  '海鲜': 'seafood',
  '快炒': 'stir_fry',
  '小炒': 'stir_fry',
  '炒': 'stir_fry',
  '10分钟': 'quick_meal',
  '15分钟': 'quick_meal',
  '快手': 'quick_meal',
  'quick': 'quick_meal',
  'low_oil': 'low_oil',
  'stir_fry': 'stir_fry',
  'quick_meal': 'quick_meal'
}

function normalizeText(value) {
  return String(value || '').toLowerCase().trim()
}

function compactQuery(query) {
  let text = normalizeText(query)
  for (const word of STOP_WORDS) text = text.replaceAll(word, '')
  return text
}

export function tokenizeRecipeQuery(query) {
  let rest = compactQuery(query)
  const groups = []
  for (const group of SYNONYM_GROUPS) {
    if (group.some(term => rest.includes(term))) {
      groups.push(group)
      for (const term of group.sort((a, b) => b.length - a.length)) {
        rest = rest.replaceAll(term, '')
      }
    }
  }

  const knownIngredients = ['韭黄', '牛肉', '鸡肉', '猪肉', '南瓜', '番茄', '西红柿', '西兰花', '芹菜', '豆腐', '黄瓜', '生菜', '虾', '鱼']
  for (const ing of knownIngredients) {
    if (rest.includes(ing)) {
      groups.push([ing])
      rest = rest.replaceAll(ing, '')
    }
  }

  const leftovers = rest.split(/\s+/).map(s => s.trim()).filter(Boolean)
  for (const token of leftovers) groups.push([token])
  return groups
}

function recipeSearchText(recipe) {
  const title = normalizeText(recipe.title)
  const ingNames = ((recipe.ingredients || []).map(i => normalizeText(i.name))).join(' ')
  const tags = ((recipe.tags || []).map(normalizeText)).join(' ')
  return `${title} ${ingNames} ${tags}`
}

export function normalizePreferences(preferences = []) {
  const out = []
  for (const pref of preferences || []) {
    const raw = String(pref || '').trim()
    if (!raw) continue
    const lower = raw.toLowerCase()
    let matched = false
    for (const [key, value] of Object.entries(PREFERENCE_ALIASES)) {
      if (raw.includes(key) || lower.includes(value)) {
        out.push(value)
        matched = true
      }
    }
    if (!matched) out.push(lower)
  }
  return [...new Set(out)]
}

function preferenceScore(recipe, preferences = []) {
  const prefs = normalizePreferences(preferences)
  if (!prefs.length) return 0
  const text = recipeSearchText(recipe)
  return prefs.filter(pref => {
    if (text.includes(pref)) return true
    if (pref === 'quick_meal') return text.includes('quick') || Number(recipe.cookTime || recipe.cook_time || 999) <= 15
    if (pref === 'low_oil') return text.includes('light') || text.includes('low_fat') || text.includes('少油') || text.includes('低油')
    return false
  }).length
}

export function searchRecipes(recipes, query, options = {}) {
  const groups = tokenizeRecipeQuery(query)
  const preferences = options.preferences || []
  if (!groups.length) return recipes
  return recipes
    .map((recipe, index) => {
      const text = recipeSearchText(recipe)
      const hits = groups.map(group => group.some(term => text.includes(normalizeText(term))))
      const hitCount = hits.filter(Boolean).length
      return { recipe, index, hitCount, prefScore: preferenceScore(recipe, preferences), pass: hitCount > 0 }
    })
    .filter(item => item.pass)
    .sort((a, b) => {
      if (b.hitCount !== a.hitCount) return b.hitCount - a.hitCount
      if (b.prefScore !== a.prefScore) return b.prefScore - a.prefScore
      return a.index - b.index
    })
    .map(item => item.recipe)
}
