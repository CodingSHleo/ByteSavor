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

export function buildNutritionOverview(recipes = []) {
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

  const targets = { calories: 1800, protein: 70, carbs: 220, fat: 60, fiber: 30, vitamin_c: 90, iron: 18 }
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
