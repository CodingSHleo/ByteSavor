const INGREDIENT_WORDS = [
  '牛肉', '鸡肉', '猪肉', '鸡蛋', '番茄', '西红柿', '西兰花',
  '南瓜', '豆腐', '鱼', '虾', '土豆', '牛奶', '酸奶', '生菜',
  '黄瓜', '胡萝卜', '洋葱', '排骨', '鸡翅', '辣椒', '青椒',
  '米饭', '面条', '面包', '苹果', '香蕉', '西瓜', '榴莲',
  '橙子', '芝士', '奶酪', '面粉', '糖', '植物油', '油'
]

export function parsePreferenceText(text = '') {
  const input = String(text)
  const preferences = new Set()
  let goal = ''

  if (/减脂|减肥|瘦身|低脂/.test(input)) goal = 'fat_loss'
  if (/增肌|健身|蛋白/.test(input)) goal = 'muscle_gain'
  if (/均衡|健康|营养/.test(input) && !goal) goal = 'balanced'

  if (/辣|川菜|湘菜|麻辣|香辣/.test(input)) preferences.add('spicy')
  if (/清淡|少油|少盐|不油腻|不喜欢油腻|不要油|别太油|太油腻/.test(input)) preferences.add('light')
  if (/高蛋白|蛋白|牛肉|鸡胸|鸡肉|虾|鱼/.test(input)) preferences.add('high_protein')
  if (/低碳|低碳水|少主食|少米饭/.test(input)) preferences.add('low_carb')
  if (/素食|蔬菜|不吃肉/.test(input)) preferences.add('vegetarian')
  if (/粤菜|家常|暖胃|下饭/.test(input)) preferences.add('comfort_food')
  if (/海鲜|鱼|虾|贝/.test(input)) preferences.add('seafood')

  return {
    goal: goal || 'balanced',
    preferences: Array.from(preferences)
  }
}

export function extractIngredientNames(text = '') {
  const input = String(text)
  return INGREDIENT_WORDS.filter(name => input.includes(name))
}

export function normalizeRecipe(recipe = {}) {
  return {
    ...recipe,
    recipeId: recipe.recipeId || recipe.recipe_id,
    recipe_id: recipe.recipe_id || recipe.recipeId,
    cookTime: recipe.cookTime || recipe.cook_time,
    matchScore: recipe.matchScore ?? recipe.match_score
  }
}

export function recipeIngredientNames(recipe = {}) {
  return (recipe.ingredients || [])
    .map(item => typeof item === 'string' ? item : item?.name)
    .filter(Boolean)
}

export function missingIngredients(recipe = {}, owned = []) {
  const ownedSet = new Set(owned.map(item => String(typeof item === 'string' ? item : item?.name || '').toLowerCase()))
  return recipeIngredientNames(recipe).filter(name => !ownedSet.has(String(name).toLowerCase()))
}

export function buildNutritionOverview(recipes = [], customTargets = {}) {
  const selected = recipes.slice(0, 3)
  const totals = selected.reduce((acc, recipe) => {
    const macros = recipe.macros || {}
    acc.calories += Number(recipe.calories || macros.calories || 0)
    acc.protein += Number(macros.protein ?? recipe.protein ?? 0)
    acc.carbs += Number(macros.carbs ?? recipe.carbs ?? 0)
    acc.fat += Number(macros.fat ?? recipe.fat ?? 0)
    const micro = recipe.micronutrients || {}
    Object.keys(micro).forEach(key => {
      acc.micronutrients[key] = (acc.micronutrients[key] || 0) + Number(micro[key] || 0)
    })
    return acc
  }, { calories: 0, protein: 0, carbs: 0, fat: 0, micronutrients: {} })

  const targets = { ...NUTRITION_TARGETS, ...(customTargets || {}) }
  const pct = key => Math.min(100, Math.round((totals[key] / targets[key]) * 100))
  const score = Math.round((pct('calories') * 0.25) + (pct('protein') * 0.35) + (Math.min(100, Math.round((totals.carbs / targets.carbs) * 100)) * 0.2) + (Math.min(100, Math.round((totals.fat / targets.fat) * 100)) * 0.2))

  return {
    score: selected.length ? Math.min(100, score) : 0,
    caloriesPct: pct('calories'),
    proteinPct: pct('protein'),
    carbsPct: Math.min(100, Math.round((totals.carbs / targets.carbs) * 100)),
    fatPct: Math.min(100, Math.round((totals.fat / targets.fat) * 100)),
    fiberPct: Math.min(100, Math.round(((totals.micronutrients.fiber || 0) / targets.fiber) * 100)),
    vitaminPct: Math.min(100, Math.round(((totals.micronutrients.vitamin_c || 0) / targets.vitamin_c) * 100)),
    ironPct: Math.min(100, Math.round(((totals.micronutrients.iron || 0) / targets.iron) * 100)),
    totals,
    targets
  }
}

export function recipeIngredientsForUse(recipe = {}) {
  return (recipe.ingredients || []).map(item => {
    if (typeof item === 'string') return { name: item, amount: '' }
    return { name: item?.name || '', amount: item?.amount || item?.display || '', unit: item?.unit || '' }
  }).filter(item => item.name)
}

export function ingredientName(item = {}) {
  if (typeof item === 'string') return item.trim()
  const fields = [
    item.name,
    item.name_zh,
    item.display_name,
    item.food_name,
    item.dish_name,
    item.ingredient_name,
    item.label,
    item.title,
    item.category
  ]
  const picked = fields.find(v => String(v || '').trim())
  return String(picked || '').trim()
}

export function stringifyAmount(raw) {
  if (raw == null || raw === '') return ''
  if (typeof raw === 'string' || typeof raw === 'number') return String(raw).trim()
  if (typeof raw === 'object') {
    const display = raw.display || raw.text || raw.label || raw.amount
    if (display) return String(display).trim()
    const value = raw.value ?? raw.quantity ?? raw.count
    const unit = raw.unit || raw.unit_name || raw.measure || ''
    if (value != null && value !== '') return `${value}${unit}`.trim()
  }
  return ''
}

export function normalizeIngredientItem(item = {}) {
  if (typeof item === 'string') return { name: ingredientName(item), amount: '' }
  const name = ingredientName(item)
  const portion = item.portion_estimation || item.meta?.portion_estimation || {}
  const amount = stringifyAmount(
    item.display ||
    item.amount ||
    item.quantity ||
    item.serving_size ||
    item.weight_estimate ||
    portion.serving_size ||
    portion.total_weight ||
    portion.weight_g
  )
  return {
    ...item,
    name,
    display: item.display || amount,
    amount,
    confidence: Number(item.confidence || item.probability || item.score || 0)
  }
}

const INGREDIENT_NUTRITION_DB = [
  { keys: ['米饭', '白米饭'], calories: 116, protein: 2.6, carbs: 25.9, fat: 0.3, fiber: 0.3, vitamin_c: 0, iron: 0.2 },
  { keys: ['面条'], calories: 110, protein: 3.5, carbs: 22, fat: 0.4, fiber: 1, vitamin_c: 0, iron: 0.6 },
  { keys: ['牛肉'], calories: 125, protein: 20, carbs: 0, fat: 5, fiber: 0, vitamin_c: 0, iron: 2.8 },
  { keys: ['猪肉'], calories: 395, protein: 14, carbs: 0, fat: 37, fiber: 0, vitamin_c: 0, iron: 1.6 },
  { keys: ['鸡胸', '鸡肉'], calories: 133, protein: 24, carbs: 0, fat: 3, fiber: 0, vitamin_c: 0, iron: 0.7 },
  { keys: ['鸡蛋'], calories: 144, protein: 13.3, carbs: 2.8, fat: 8.8, fiber: 0, vitamin_c: 0, iron: 1.8 },
  { keys: ['鱼', '鲈鱼'], calories: 104, protein: 17.6, carbs: 0, fat: 3.4, fiber: 0, vitamin_c: 0, iron: 0.5 },
  { keys: ['虾'], calories: 93, protein: 18.6, carbs: 2.8, fat: 0.8, fiber: 0, vitamin_c: 0, iron: 1.5 },
  { keys: ['西兰花'], calories: 36, protein: 4.1, carbs: 4.0, fat: 0.6, fiber: 1.6, vitamin_c: 89, iron: 0.7 },
  { keys: ['番茄', '西红柿'], calories: 20, protein: 0.9, carbs: 4.0, fat: 0.2, fiber: 0.5, vitamin_c: 14, iron: 0.3 },
  { keys: ['黄瓜'], calories: 16, protein: 0.8, carbs: 2.9, fat: 0.2, fiber: 0.5, vitamin_c: 3, iron: 0.3 },
  { keys: ['青椒', '辣椒'], calories: 23, protein: 1.4, carbs: 3.7, fat: 0.3, fiber: 2.1, vitamin_c: 72, iron: 0.4 },
  { keys: ['南瓜'], calories: 22, protein: 0.7, carbs: 5.3, fat: 0.1, fiber: 0.8, vitamin_c: 9, iron: 0.8 },
  { keys: ['土豆'], calories: 81, protein: 2.0, carbs: 17.8, fat: 0.2, fiber: 0.7, vitamin_c: 27, iron: 0.8 },
  { keys: ['胡萝卜'], calories: 39, protein: 1.0, carbs: 8.8, fat: 0.2, fiber: 1.1, vitamin_c: 6, iron: 0.3 },
  { keys: ['生菜'], calories: 15, protein: 1.4, carbs: 2.0, fat: 0.2, fiber: 1.3, vitamin_c: 9, iron: 0.9 },
  { keys: ['豆腐'], calories: 82, protein: 8.1, carbs: 3.8, fat: 3.7, fiber: 0.1, vitamin_c: 0, iron: 1.6 },
  { keys: ['苹果'], calories: 53, protein: 0.2, carbs: 13.5, fat: 0.2, fiber: 1.2, vitamin_c: 5, iron: 0.1 },
  { keys: ['香蕉'], calories: 93, protein: 1.4, carbs: 22.8, fat: 0.2, fiber: 1.2, vitamin_c: 9, iron: 0.3 },
  { keys: ['西瓜'], calories: 32, protein: 0.6, carbs: 7.6, fat: 0.2, fiber: 0.3, vitamin_c: 8, iron: 0.2 },
  { keys: ['榴莲'], calories: 147, protein: 1.5, carbs: 27, fat: 5.3, fiber: 3.8, vitamin_c: 20, iron: 0.4 },
  { keys: ['橙子'], calories: 47, protein: 0.9, carbs: 11.8, fat: 0.1, fiber: 2.4, vitamin_c: 53, iron: 0.1 }
]

export const NUTRITION_TARGETS = { calories: 1800, protein: 70, carbs: 220, fat: 60, fiber: 30, vitamin_c: 90, iron: 18 }

function defaultUnitWeight(name = '', unit = '') {
  if (/碗/.test(unit)) {
    if (/饭|米饭|粥/.test(name)) return 200
    if (/面|粉/.test(name)) return 300
    return 250
  }
  if (/份|盘|全部/.test(unit)) {
    if (/饭|米饭/.test(name)) return 200
    if (/肉|牛|猪|鸡|鱼|虾/.test(name)) return 150
    if (/西瓜/.test(name)) return 500
    return 250
  }
  if (/个|颗|只|根|块|片/.test(unit)) {
    if (/西瓜/.test(name)) return 2500
    if (/榴莲/.test(name)) return 1200
    if (/苹果|橙子/.test(name)) return 180
    if (/香蕉/.test(name)) return 120
    if (/番茄|西红柿/.test(name)) return 160
    if (/鸡蛋/.test(name)) return 55
    if (/土豆/.test(name)) return 150
    if (/胡萝卜|黄瓜/.test(name)) return 120
    if (/玉米/.test(name)) return 200
    return 100
  }
  if (/斤/.test(unit)) return 500
  return 100
}

function firstNumericWeight(raw) {
  if (raw == null || raw === '') return null
  if (typeof raw === 'number') return raw
  if (typeof raw === 'object') raw = stringifyAmount(raw)
  const text = String(raw)
  const match = text.match(/(\d+(?:\.\d+)?)\s*(kg|千克|公斤|斤|g|克|毫克|个|颗|只|根|块|片|份|盘|碗)?/i)
  if (!match) return null
  return { value: Number(match[1]), unit: match[2] || 'g' }
}

export function parseIngredientWeight(item = {}) {
  const normalized = normalizeIngredientItem(item)
  const name = normalized.name
  const portion = item.portion_estimation || item.meta?.portion_estimation || {}
  const explicitWeight = [
    item.weight_g,
    item.weight_estimate_g,
    item.estimated_weight_g,
    item.estimated_weight,
    portion.weight_g,
    portion.total_weight
  ].map(firstNumericWeight).find(v => v)
  if (typeof explicitWeight === 'number' && explicitWeight > 0) return Math.round(explicitWeight)
  if (explicitWeight?.value > 0) {
    const unit = explicitWeight.unit
    if (/kg|千克|公斤/i.test(unit)) return Math.round(explicitWeight.value * 1000)
    if (/斤/.test(unit)) return Math.round(explicitWeight.value * 500)
    if (/毫克/.test(unit)) return Math.round(explicitWeight.value / 1000)
    if (/g|克/i.test(unit)) return Math.round(explicitWeight.value)
    return Math.round(explicitWeight.value * defaultUnitWeight(name, unit))
  }

  const candidates = [
    normalized.display,
    normalized.amount,
    item.weight_estimate,
    item.weight,
    item.display,
    item.amount,
    item.quantity,
    item.serving_size,
    portion.serving_size,
    portion.total_weight
  ]
  for (const raw of candidates) {
    const parsed = firstNumericWeight(raw)
    if (!parsed) continue
    const unit = parsed.unit
    if (/kg|千克|公斤/i.test(unit)) return Math.round(parsed.value * 1000)
    if (/斤/.test(unit)) return Math.round(parsed.value * 500)
    if (/毫克/.test(unit)) return Math.round(parsed.value / 1000)
    if (/g|克/i.test(unit)) return Math.round(parsed.value)
    return Math.round(parsed.value * defaultUnitWeight(name, unit))
  }

  const rawText = candidates.filter(Boolean).join(' ')
  if (/全部|整份|一份|1份/.test(rawText)) return defaultUnitWeight(name, '份')
  if (/半个|半颗|半只/.test(rawText)) return Math.round(defaultUnitWeight(name, '个') * 0.5)
  if (/一碗|1碗/.test(rawText)) return defaultUnitWeight(name, '碗')
  if (/一盘|1盘/.test(rawText)) return defaultUnitWeight(name, '盘')
  return defaultUnitWeight(name, '')
}

export function estimateIngredientNutrition(item = {}) {
  const normalized = normalizeIngredientItem(item)
  const name = normalized.name
  const weight = parseIngredientWeight(normalized)
  const base = INGREDIENT_NUTRITION_DB.find(row => row.keys.some(key => name.includes(key) || key.includes(name))) || {
    calories: 80, protein: 3, carbs: 10, fat: 2, fiber: 1, vitamin_c: 3, iron: 0.3
  }
  const ratio = weight / 100
  return {
    name,
    weight,
    calories: Math.round(base.calories * ratio),
    protein: Number((base.protein * ratio).toFixed(1)),
    carbs: Number((base.carbs * ratio).toFixed(1)),
    fat: Number((base.fat * ratio).toFixed(1)),
    fiber: Number((base.fiber * ratio).toFixed(1)),
    vitamin_c: Number((base.vitamin_c * ratio).toFixed(1)),
    iron: Number((base.iron * ratio).toFixed(1))
  }
}

export function summarizeIngredientNutrition(items = []) {
  const rows = items.map(estimateIngredientNutrition)
  const totals = rows.reduce((acc, row) => {
    ;['calories', 'protein', 'carbs', 'fat', 'fiber', 'vitamin_c', 'iron'].forEach(key => {
      acc[key] += Number(row[key] || 0)
    })
    return acc
  }, { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0, vitamin_c: 0, iron: 0 })
  totals.calories = Math.round(totals.calories)
  ;['protein', 'carbs', 'fat', 'fiber', 'vitamin_c', 'iron'].forEach(key => { totals[key] = Number(totals[key].toFixed(1)) })
  return { rows, totals, targets: NUTRITION_TARGETS }
}
