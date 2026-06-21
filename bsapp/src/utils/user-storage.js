export const USER_SCOPED_STORAGE_KEYS = [
  'last_ingredients',
  'agent_conversation_id',
  'inventory_items',
  'recognition_result',
  'app_history_records',
  'plan_meal_slot'
]

export function clearUserScopedStorage() {
  USER_SCOPED_STORAGE_KEYS.forEach(key => uni.removeStorageSync(key))
}
