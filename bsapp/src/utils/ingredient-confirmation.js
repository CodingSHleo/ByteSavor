import { ingredientName, normalizeIngredientItem } from './food-analysis'

function cleanName(name) {
  return String(name || '').trim()
}

function keyOf(item) {
  return ingredientName(item).toLowerCase()
}

function toIngredient(item) {
  if (typeof item === 'string') return { name: cleanName(item), confidence: 0, amount: '' }
  const normalized = normalizeIngredientItem(item)
  return {
    ...normalized,
    name: cleanName(normalized.name),
    confidence: Number(normalized.confidence || 0)
  }
}

export function mergeRecognizedIngredients(items = []) {
  const map = new Map()
  items.map(toIngredient).filter(item => item.name).forEach(item => {
    const key = keyOf(item)
    const current = map.get(key)
    if (!current) {
      map.set(key, { ...item, source_count: 1 })
      return
    }

    const confidence = Math.max(Number(current.confidence || 0), Number(item.confidence || 0))
    const weight = Number(current.weight_estimate || 0) || Number(item.weight_estimate || 0) || undefined
    const features = current.features || item.features || current.state || item.state || ''
    map.set(key, {
      ...current,
      ...item,
      name: current.name,
      confidence,
      weight_estimate: weight,
      source_count: Number(current.source_count || 1) + 1,
      features: features ? `已合并${Number(current.source_count || 1) + 1}个候选：${features}` : `已合并${Number(current.source_count || 1) + 1}个候选`
    })
  })
  return Array.from(map.values())
}

export function updateIngredientAt(items = [], index, patch = {}) {
  return items.map((item, idx) => idx === index ? normalizeIngredientItem({ ...item, ...patch, name: cleanName(patch.name ?? item.name) }) : item)
}

export function removeIngredientAt(items = [], index) {
  return items.filter((_, idx) => idx !== index)
}
