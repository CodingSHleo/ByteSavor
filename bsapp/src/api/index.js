import { currentLang } from '@/utils/i18n'

// API 基础配置 —— 可通过 storage 或编译时变量覆盖
function getBaseUrl() {
  try {
    const stored = uni.getStorageSync('api_base_url')
    if (stored) return stored
    if (typeof window !== 'undefined' && window.location?.hostname) {
      const host = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname
      return `http://${host}:8000`
    }
    return 'http://127.0.0.1:8000'
  } catch (e) { return 'http://127.0.0.1:8000' }
}

const HEADERS = {
  'Content-Type': 'application/json'
}

// trace_id 生成
function genTraceId() {
  return 'trace_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36)
}

// 智能本地化：根据当前语言返回对应字段
function L(item) {
  if (!item) return item
  if (Array.isArray(item)) return item.map(L)
  const lang = currentLang.value
  const localized = { ...item }
  // 优先使用当前语言版本，fallback 到中文
  if (lang === 'en') {
    if (item.nameEn !== undefined) localized.name = item.nameEn
    if (item.titleEn !== undefined) localized.title = item.titleEn
    if (item.stateEn !== undefined) localized.state = item.stateEn
    if (item.featuresEn !== undefined) localized.features = item.featuresEn
    if (item.difficultyEn !== undefined) localized.difficulty = item.difficultyEn
    if (item.tipsEn !== undefined) localized.tips = item.tipsEn
    if (item.serving_sizeEn !== undefined && item.portion_estimation) {
      localized.portion_estimation = { ...item.portion_estimation, serving_size: item.portion_estimation.serving_sizeEn || item.portion_estimation.serving_size }
    }
    // 翻译 steps
    if (item.stepsEn) localized.steps = item.stepsEn
    // 翻译 ingredients 里的 name
    if (item.ingredients) {
      localized.ingredients = item.ingredients.map(i => typeof i === 'string' ? i : ({ ...i, name: i.nameEn || i.name }))
    }
  }
  return localized
}

// ==================== Mock数据 (后端未启动时使用) ====================

export const MOCK_INGREDIENTS = [
  {
    name: '西兰花', nameEn: 'Broccoli',
    confidence: 0.98,
    freshness: 'high',
    state: '新鲜', stateEn: 'Fresh',
    features: '深绿色、花球紧实饱满、无黄斑、茎秆脆嫩、组织致密',
    featuresEn: 'Dark green, tight florets, no yellow spots, crisp stem, dense tissue',
    portion_estimation: { weight_g: 250, serving_size: '中等大小一棵', serving_sizeEn: '1 medium head' }
  },
  {
    name: '牛肉', nameEn: 'Beef',
    confidence: 0.95,
    freshness: 'normal',
    state: '冷藏', stateEn: 'Chilled',
    features: '纹理清晰均匀、呈樱桃红色、适度大理石花纹、肌组织弹性良好',
    featuresEn: 'Clear marbling, cherry-red color, moderate fat distribution, good elasticity',
    portion_estimation: { weight_g: 300, serving_size: '一块', serving_sizeEn: '1 piece' }
  },
  {
    name: '番茄', nameEn: 'Tomato',
    confidence: 0.92,
    freshness: 'high',
    state: '新鲜', stateEn: 'Fresh',
    features: '色泽鲜红均匀、果形圆润饱满、果蒂翠绿、触感微软有弹性',
    featuresEn: 'Bright red, round and plump, green stem, slightly soft to touch',
    portion_estimation: { weight_g: 180, serving_size: '两个中等番茄', serving_sizeEn: '2 medium tomatoes' }
  }
]

export const MOCK_RECIPES = [
  {
    recipeId: 'r_101',
    title: '香辣牛肉西兰花', titleEn: 'Spicy Beef & Broccoli',
    matchScore: 0.93,
    cookTime: 25,
    difficulty: '简单', difficultyEn: 'Easy',
    calories: 320,
    imageEmoji: '🥩'
  },
  {
    recipeId: 'r_102',
    title: '西兰花炒鸡胸', titleEn: 'Broccoli & Chicken Stir-Fry',
    matchScore: 0.88,
    cookTime: 20,
    difficulty: '简单', difficultyEn: 'Easy',
    calories: 280,
    imageEmoji: '🥦'
  },
  {
    recipeId: 'r_103',
    title: '番茄牛腩煲', titleEn: 'Tomato Beef Brisket Stew',
    matchScore: 0.85,
    cookTime: 60,
    difficulty: '中等', difficultyEn: 'Medium',
    calories: 420,
    imageEmoji: '🍅'
  },
  {
    recipeId: 'r_104',
    title: '低脂沙拉碗', titleEn: 'Low-Fat Salad Bowl',
    matchScore: 0.82,
    cookTime: 15,
    difficulty: '简单', difficultyEn: 'Easy',
    calories: 180,
    imageEmoji: '🥗'
  }
]

export const MOCK_NUTRITION_STATUS = {
  score: 65,
  deficits: ['vitamin_c', 'fiber', 'iron']
}

export const MOCK_NUTRITION_GAP = {
  protein: 'still_needed',
  fiber: 'critical',
  vitamin_c: 'critical',
  iron: 'moderate'
}

export const MOCK_USER_PROFILE = {
  userId: 'u_001',
  username: 'demo_user',
  name: 'demo_user',
  goal: 'fat_loss',
  preferences: ['spicy', 'high_protein'],
  healthData: {
    height: 175,
    weight: 78,
    targetWeight: 70,
    dailyCalorieTarget: 2200,
    dailyProteinTarget: 90,
    dailyFiberTarget: 30
  }
}

export const MOCK_RECIPE_DETAIL = {
  recipeId: 'r_101',
  title: '香辣牛肉西兰花', titleEn: 'Spicy Beef & Broccoli',
  cookTime: 25,
  difficulty: '简单', difficultyEn: 'Easy',
  calories: 320,
  imageEmoji: '🥩',
  servingSize: '2人份',
  ingredients: [
    { name: '牛肉', nameEn: 'Beef', amount: '300g' },
    { name: '西兰花', nameEn: 'Broccoli', amount: '200g' },
    { name: '蒜蓉', nameEn: 'Minced Garlic', amount: '10g' },
    { name: '干辣椒', nameEn: 'Dried Chili', amount: '适量' },
    { name: '生抽', nameEn: 'Soy Sauce', amount: '15ml' },
    { name: '料酒', nameEn: 'Cooking Wine', amount: '10ml' },
    { name: '淀粉', nameEn: 'Cornstarch', amount: '5g' }
  ],
  nutrition: { protein: 35, fat: 15, carbs: 12, fiber: 4, vitamin_c: 89, iron: 3.5, calcium: 45 },
  steps: [
    '牛肉切薄片，加入料酒、生抽、淀粉腌制10分钟',
    '西兰花掰成小朵，烧开水加盐焯烫1分钟捞出',
    '热锅冷油，放入蒜蓉和干辣椒炒香',
    '加入牛肉片快速翻炒至变色（约2分钟）',
    '加入焯好的西兰花，大火翻炒均匀',
    '调入生抽和少许盐，翻炒30秒即可出锅'
  ],
  stepsEn: [
    'Slice beef thinly, marinate with cooking wine, soy sauce & cornstarch for 10 min',
    'Break broccoli into florets, blanch in salted boiling water for 1 min',
    'Heat oil in a wok, sauté garlic and dried chili until fragrant',
    'Add beef slices, stir-fry quickly until color changes (~2 min)',
    'Add blanched broccoli, stir-fry over high heat',
    'Season with soy sauce and a pinch of salt, toss for 30s and serve'
  ],
  tips: '牛肉不要炒太久，变色即可保持嫩滑；西兰花焯水时加盐和几滴油能保持翠绿色泽。',
  tipsEn: 'Do not overcook the beef — remove as soon as it changes color. Add salt and a few drops of oil when blanching broccoli to keep it bright green.'
}

export const MOCK_RECIPE_DETAILS = {
  // 支持多菜谱详情查询
  'r_101': MOCK_RECIPE_DETAIL,
  'r_102': {
    recipeId: 'r_102',
    title: '西兰花炒鸡胸',
    cookTime: 20,
    difficulty: '简单',
    calories: 280,
    imageEmoji: '🥦',
    servingSize: '2人份',
    ingredients: [
      { name: '鸡胸肉', amount: '250g' },
      { name: '西兰花', amount: '200g' },
      { name: '蒜片', amount: '10g' },
      { name: '姜丝', amount: '5g' },
      { name: '盐', amount: '适量' },
      { name: '胡椒粉', amount: '少许' }
    ],
    nutrition: {
      protein: 42,
      fat: 8,
      carbs: 10,
      fiber: 3,
      vitamin_c: 82,
      iron: 2.1,
      calcium: 35
    },
    steps: [
      '鸡胸肉切丁，加盐和胡椒粉腌制5分钟',
      '西兰花掰小朵，开水焯烫1分钟捞出',
      '热锅少油，爆香姜丝蒜片',
      '加入鸡胸肉丁，中火翻炒至表面变白',
      '加入西兰花一起翻炒1分钟',
      '加少许盐调味，翻炒均匀出锅'
    ],
    tips: '鸡胸肉不要切太大块，小丁更容易熟透且口感更好。'
  },
  'r_103': {
    recipeId: 'r_103',
    title: '番茄牛腩煲',
    cookTime: 60,
    difficulty: '中等',
    calories: 420,
    imageEmoji: '🍅',
    servingSize: '3人份',
    ingredients: [
      { name: '牛腩', amount: '500g' },
      { name: '番茄', amount: '3个' },
      { name: '洋葱', amount: '半个' },
      { name: '姜片', amount: '5片' },
      { name: '八角', amount: '2个' },
      { name: '番茄酱', amount: '30g' },
      { name: '盐', amount: '适量' }
    ],
    nutrition: {
      protein: 38,
      fat: 22,
      carbs: 15,
      fiber: 5,
      vitamin_c: 35,
      iron: 4.8,
      calcium: 55
    },
    steps: [
      '牛腩切块，冷水下锅焯水去血沫，捞出洗净',
      '番茄切十字花刀，热水烫去皮后切块',
      '热锅加油，炒香洋葱和姜片',
      '加入牛腩翻炒至表面微黄',
      '加入番茄块和番茄酱，翻炒出汁',
      '加足量热水，放入八角，大火烧开转小火炖40分钟',
      '开盖收汁，加盐调味即可'
    ],
    tips: '番茄去皮后口感更好；炖的时间越长牛腩越软烂。'
  },
  'r_104': {
    recipeId: 'r_104',
    title: '低脂沙拉碗',
    cookTime: 15,
    difficulty: '简单',
    calories: 180,
    imageEmoji: '🥗',
    servingSize: '1人份',
    ingredients: [
      { name: '生菜', amount: '100g' },
      { name: '鸡胸肉(煮熟)', amount: '100g' },
      { name: '圣女果', amount: '8颗' },
      { name: '黄瓜', amount: '半根' },
      { name: '玉米粒', amount: '50g' },
      { name: '橄榄油', amount: '5ml' },
      { name: '柠檬汁', amount: '10ml' }
    ],
    nutrition: {
      protein: 28,
      fat: 6,
      carbs: 18,
      fiber: 8,
      vitamin_c: 45,
      iron: 2.5,
      calcium: 60
    },
    steps: [
      '生菜洗净撕成小片，铺碗底',
      '鸡胸肉煮熟后撕成丝',
      '黄瓜切片，圣女果对半切',
      '将所有食材放入碗中',
      '淋上橄榄油和柠檬汁',
      '撒少许黑胡椒和盐，拌匀即可'
    ],
    tips: '可以提前煮好鸡胸肉冷藏保存，吃的时候直接撕丝即可。柠檬汁能提鲜且减少油脂感。'
  }
}

// 响应式获取探索菜谱（根据当前语言自动切换）
export function getExploreRecipes() {
  return L(EXPLORE_RECIPES_RAW)
}
const EXPLORE_RECIPES_RAW = [
  { recipeId: 'r_101', title: '香辣牛肉西兰花', titleEn: 'Spicy Beef & Broccoli', cookTime: 25, difficulty: '简单', difficultyEn: 'Easy', calories: 320, imageEmoji: '🥩', category: 'high_protein' },
  { recipeId: 'r_102', title: '西兰花炒鸡胸', titleEn: 'Broccoli & Chicken Breast', cookTime: 20, difficulty: '简单', difficultyEn: 'Easy', calories: 280, imageEmoji: '🥦', category: 'high_protein' },
  { recipeId: 'r_103', title: '番茄牛腩煲', titleEn: 'Tomato Beef Brisket Stew', cookTime: 60, difficulty: '中等', difficultyEn: 'Medium', calories: 420, imageEmoji: '🍅', category: 'comfort' },
  { recipeId: 'r_104', title: '低脂沙拉碗', titleEn: 'Low-Fat Salad Bowl', cookTime: 15, difficulty: '简单', difficultyEn: 'Easy', calories: 180, imageEmoji: '🥗', category: 'low_fat' },
  { recipeId: 'r_201', title: '清蒸鲈鱼', titleEn: 'Steamed Sea Bass', cookTime: 25, difficulty: '简单', difficultyEn: 'Easy', calories: 200, imageEmoji: '🐟', category: 'seafood' },
  { recipeId: 'r_202', title: '南瓜炖牛肉', titleEn: 'Pumpkin Beef Stew', cookTime: 30, difficulty: '简单', difficultyEn: 'Easy', calories: 310, imageEmoji: '🎃', category: 'comfort' },
  { recipeId: 'r_203', title: '番茄炒蛋', titleEn: 'Tomato Scrambled Eggs', cookTime: 10, difficulty: '简单', difficultyEn: 'Easy', calories: 220, imageEmoji: '🍳', category: 'quick' },
  { recipeId: 'r_204', title: '蒜蓉空心菜', titleEn: 'Garlic Water Spinach', cookTime: 10, difficulty: '简单', difficultyEn: 'Easy', calories: 120, imageEmoji: '🥬', category: 'vegetarian' },
  { recipeId: 'r_301', title: '虾仁豆腐羹', titleEn: 'Shrimp Tofu Soup', cookTime: 20, difficulty: '中等', difficultyEn: 'Medium', calories: 250, imageEmoji: '🦐', category: 'seafood' },
  { recipeId: 'r_302', title: '白灼菜心', titleEn: 'Blanched Choy Sum', cookTime: 8, difficulty: '简单', difficultyEn: 'Easy', calories: 90, imageEmoji: '🥬', category: 'vegetarian' },
  { recipeId: 'r_303', title: '黑椒鸡胸肉', titleEn: 'Black Pepper Chicken Breast', cookTime: 15, difficulty: '简单', difficultyEn: 'Easy', calories: 260, imageEmoji: '🍗', category: 'high_protein' },
  { recipeId: 'r_304', title: '紫菜蛋花汤', titleEn: 'Seaweed Egg Drop Soup', cookTime: 10, difficulty: '简单', difficultyEn: 'Easy', calories: 80, imageEmoji: '🍲', category: 'quick' }
]

export const MOCK_SHOPPING_LIST = [
  { name: '牛肉', nameEn: 'Beef', amount: '300g' },
  { name: '蒜蓉', nameEn: 'Minced Garlic', amount: '10g' },
  { name: '西兰花', nameEn: 'Broccoli', amount: '200g' },
  { name: '干辣椒', nameEn: 'Dried Chili', amount: '适量' },
  { name: '生抽', nameEn: 'Soy Sauce', amount: '15ml' }
]

export const MOCK_VALID_USERNAME = 'demo'
export const MOCK_VALID_PASSWORD = '123456'

export const MOCK_LOGIN_RESPONSE = {
  token: 'mock_jwt_token_12345',
  user: {
    userId: 'u_001',
    username: 'demo_user',
    email: 'demo@example.com'
  }
}

// ==================== 请求封装 ====================

function request(options) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('auth_token') || ''
    uni.request({
      url: getBaseUrl() + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        ...HEADERS,
        'Authorization': token ? `Bearer ${token}` : ''
      },
      timeout: 60000,
      success: (res) => {
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve(res.data)
        } else {
          const message = res.data?.error?.message || res.data?.detail || `请求失败: ${res.statusCode}`
          reject(new Error(message))
        }
      },
      fail: (err) => {
        console.error('网络请求错误:', err)
        reject(err)
      }
    })
  })
}

// Mock 响应包装
function mockResponse(data) {
  return {
    status: 'success',
    data: data,
    trace_id: genTraceId()
  }
}

// ==================== API 方法 ====================

export const ApiService = {
  async getRecipes() {
    const res = await request({ url: '/v1/recipes' })
    if (res.status === 'success') return L(res.data.recipes || [])
    throw new Error(res.error?.message || '获取菜谱失败')
  },

  // 食材识别
  async analyzeIngredient(imageUrl) {
    const data = await this.analyzeIngredientDetail(imageUrl)
    return L(data.ingredients || [])
  },

  async analyzeIngredientDetail(imageUrl) {
    const res = await request({
      url: '/v1/sense/analyze',
      method: 'POST',
      data: {
        task_id: 'task_' + Date.now(),
        image_url: imageUrl,
        context: { scene: 'kitchen' }
      }
    })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '食材识别失败')
  },

  async assessQuality(imageUrl) {
    const res = await request({
      url: '/v1/quality/assess',
      method: 'POST',
      data: {
        task_id: 'quality_' + Date.now(),
        image_url: imageUrl,
        context: { scene: 'quality_assessment' }
      }
    })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '品质鉴定失败')
  },

  async analyzeMealNutrition(imageUrl, goal = 'balanced') {
    const res = await request({
      url: '/v1/nutrition/analyze-meal',
      method: 'POST',
      data: { image_url: imageUrl, goal }
    })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '营养分析失败')
  },

  async exploreFoodGuide(imageUrl) {
    const res = await request({
      url: '/v1/guide/explore',
      method: 'POST',
      data: {
        task_id: 'guide_' + Date.now(),
        image_url: imageUrl,
        context: { scene: 'restaurant' }
      }
    })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '探店向导失败')
  },

  // 获取用户画像
  async getUserProfile() {
    const res = await request({ url: '/v1/user/profile' })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '获取用户画像失败')
  },

  async updateProfile(goal, preferences, bodyMetrics = undefined, nutritionTargets = undefined, display = undefined) {
    const data = { goal, preferences }
    if (bodyMetrics !== undefined) data.body_metrics = bodyMetrics
    if (nutritionTargets !== undefined) data.nutrition_targets = nutritionTargets
    if (display?.name !== undefined) data.name = display.name
    if (display?.avatar_url !== undefined) data.avatar_url = display.avatar_url
    const res = await request({ url: '/v1/user/profile', method: 'PUT', data })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '更新用户画像失败')
  },

  // 获取营养状态
  async getNutritionStatus() {
    const res = await request({ url: '/v1/nutrition/status' })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '获取营养状态失败')
  },

  // 生成餐食方案
  async generateMealPlan(ingredients, options = {}) {
    const res = await request({
      url: '/v1/decision/meal-plan',
      method: 'POST',
      data: {
        ingredients: ingredients,
        constraints: { time_limit: 30, taste: '', goal: 'balanced' },
        refresh: !!options.refresh,
        exclude_recipe_ids: options.excludeRecipeIds || []
      }
    })
    if (res.status === 'success') return L(res.data.recipes || [])
    throw new Error(res.error?.message || '生成推荐失败')
  },

  // 获取菜谱详情
  async getRecipeDetail(recipeId) {
    const res = await request({ url: `/v1/recipes/${recipeId}` })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '获取菜谱详情失败')
  },

  // Agent对话（支持传入图片 URL）
  async agentExecute(input, imageUrl = null, conversationId = '') {
    const res = await request({
      url: '/v1/agent/execute',
      method: 'POST',
      data: {
        input,
        image_url: imageUrl || undefined,
        conversation_id: conversationId || undefined
      }
    })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || 'AI Agent 暂未连通')
  },

  async assistantChat(message, history = []) {
    const res = await request({
      url: '/v1/assistant/chat',
      method: 'POST',
      data: { message, history }
    })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || 'AI 助手暂未连通')
  },

  // 提交反馈
  async submitFeedback(recipeId, rating, comment = '') {
    const res = await request({
      url: '/v1/feedback/meal',
      method: 'POST',
      data: { recipe_id: recipeId, rating, comment }
    })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '提交反馈失败')
  },

  // 纠错日志
  async recordCorrection(payload) {
    const res = await request({
      url: '/v1/correction-logs',
      method: 'POST',
      data: payload
    })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '记录纠错失败')
  },

  // 合并购物清单
  async mergeShoppingList(recipeIds) {
    const res = await request({
      url: '/v1/task/merge-list',
      method: 'POST',
      data: { recipes: recipeIds }
    })
    if (res.status === 'success') return L(res.data.shopping_list || [])
    throw new Error(res.error?.message || '合并购物清单失败')
  },

  async importInventory(items, source = 'scan') {
    const res = await request({
      url: '/v1/inventory/import',
      method: 'POST',
      data: { items, source }
    })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '导入库存失败')
  },

  async getInventory() {
    const res = await request({ url: '/v1/inventory/current' })
    if (res.status === 'success') return L(res.data.items || [])
    throw new Error(res.error?.message || '获取库存失败')
  },

  async addInventoryItem(item) {
    const res = await request({ url: '/v1/inventory/items', method: 'POST', data: item })
    if (res.status === 'success') return L(res.data.item)
    throw new Error(res.error?.message || '新增食材失败')
  },

  async updateInventoryItem(itemId, item) {
    const res = await request({ url: `/v1/inventory/items/${itemId}`, method: 'PUT', data: item })
    if (res.status === 'success') return L(res.data.item)
    throw new Error(res.error?.message || '更新食材失败')
  },

  async deleteInventoryItem(itemId) {
    const res = await request({ url: `/v1/inventory/items/${itemId}`, method: 'DELETE' })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '删除食材失败')
  },

  async getInventoryStats() {
    const res = await request({ url: '/v1/inventory/stats' })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '获取库存统计失败')
  },

  async checkRecipe(targetType, targetId) {
    const res = await request({
      url: '/v1/recipes/check',
      method: 'POST',
      data: { target_type: targetType, target_id: String(targetId) }
    })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '菜谱清点失败')
  },

  async getFavorites() {
    const res = await request({ url: '/v1/favorites' })
    if (res.status === 'success') return L(res.data.favorites || [])
    throw new Error(res.error?.message || '获取收藏失败')
  },

  async addFavorite(targetType, targetId, snapshot = {}) {
    const res = await request({
      url: '/v1/favorites',
      method: 'POST',
      data: { target_type: targetType, target_id: String(targetId), snapshot }
    })
    if (res.status === 'success') return L(res.data.favorite)
    throw new Error(res.error?.message || '收藏失败')
  },

  async removeFavorite(targetType, targetId) {
    const res = await request({ url: `/v1/favorites?target_type=${encodeURIComponent(targetType)}&target_id=${encodeURIComponent(String(targetId))}`, method: 'DELETE' })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '取消收藏失败')
  },

  async getFavoriteStatus(targetType, targetId) {
    const res = await request({ url: `/v1/favorites/status?target_type=${encodeURIComponent(targetType)}&target_id=${encodeURIComponent(String(targetId))}` })
    if (res.status === 'success') return !!res.data.favorited
    throw new Error(res.error?.message || '获取收藏状态失败')
  },

  async getCommunityPosts(category = 'all', { limit = 20, offset = 0 } = {}) {
    const res = await request({ url: `/v1/community/posts?category=${encodeURIComponent(category)}&limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}` })
    if (res.status === 'success') return L(res.data || { posts: [], total: 0, limit, offset, has_more: false })
    throw new Error(res.error?.message || '获取社区内容失败')
  },

  async createCommunityPost(payload) {
    const res = await request({ url: '/v1/community/posts', method: 'POST', data: payload })
    if (res.status === 'success') return L(res.data.post)
    throw new Error(res.error?.message || '发布失败')
  },

  async getCommunityPost(postId) {
    const res = await request({ url: `/v1/community/posts/${postId}` })
    if (res.status === 'success') return L(res.data)
    throw new Error(res.error?.message || '获取帖子失败')
  },

  async likeCommunityPost(postId) {
    const res = await request({ url: `/v1/community/posts/${postId}/like`, method: 'POST' })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '点赞失败')
  },

  async unlikeCommunityPost(postId) {
    const res = await request({ url: `/v1/community/posts/${postId}/like`, method: 'DELETE' })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '取消点赞失败')
  },

  async deleteCommunityPost(postId) {
    const res = await request({ url: `/v1/community/posts/${postId}`, method: 'DELETE' })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '删除失败')
  },

  async addCommunityComment(postId, content) {
    const res = await request({ url: `/v1/community/posts/${postId}/comments`, method: 'POST', data: { content } })
    if (res.status === 'success') return L(res.data.comment)
    throw new Error(res.error?.message || '评论失败')
  },

  async planMeal(mealSlot, recipe, ingredientsUsed = [], shoppingList = []) {
    const res = await request({
      url: '/v1/meals/plan',
      method: 'POST',
      data: { meal_slot: mealSlot, recipe, ingredients_used: ingredientsUsed, shopping_list: shoppingList }
    })
    if (res.status === 'success') return L(res.data.meal)
    throw new Error(res.error?.message || '加入今日计划失败')
  },

  async getTodayMeals() {
    const res = await request({ url: '/v1/meals/today' })
    if (res.status === 'success') return L(res.data.meals || [])
    throw new Error(res.error?.message || '获取今日计划失败')
  },

  async completeMeal(mealId) {
    const res = await request({ url: `/v1/meals/${mealId}/complete`, method: 'POST' })
    if (res.status === 'success') return L(res.data.meal)
    throw new Error(res.error?.message || '完成这一餐失败')
  },

  async cancelMeal(mealId) {
    const res = await request({ url: `/v1/meals/${mealId}/cancel`, method: 'POST' })
    if (res.status === 'success') return L(res.data.meal)
    throw new Error(res.error?.message || '取消计划失败')
  },

  async changeMealSlot(mealId, newSlot) {
    const res = await request({ url: `/v1/meals/${mealId}/slot`, method: 'PUT', data: { meal_slot: newSlot } })
    if (res.status === 'success') return L(res.data.meal)
    throw new Error(res.error?.message || '切换餐次失败')
  },

  async getNutritionSummary(range = 'day') {
    const res = await request({ url: `/v1/nutrition/summary?range=${encodeURIComponent(range)}` })
    if (res.status === 'success') return res.data
    throw new Error(res.error?.message || '获取营养汇总失败')
  },

  // 登录（v5: 兼容 {username,password} 或 旧 openid 字符串）
  async login(payload) {
    const data = typeof payload === 'string' ? { openid: payload } : (payload || {})
    try {
      const res = await request({
        url: '/v1/auth/login',
        method: 'POST',
        data
      })
      if (res.status === 'success') return res.data
      throw new Error(res.error?.message || '登录失败')
    } catch (e) {
      console.error('API Error - login:', e)
      if (e?.message) throw e
    }
    throw new Error('登录失败，请检查网络或后端服务')
  },

  // 注册（v5: 兼容 {username,password,name} 或 旧 (openid, name)）
  async register(payload, name = '') {
    const data = typeof payload === 'string' ? { openid: payload, name } : (payload || {})
    try {
      const res = await request({
        url: '/v1/auth/register',
        method: 'POST',
        data
      })
      if (res.status === 'success') return res.data
      throw new Error(res.error?.message || '注册失败')
    } catch (e) {
      console.error('API Error - register:', e)
      if (e?.message) throw e
    }
    throw new Error('后端服务不可用，暂时无法注册')
  },

  // 登出
  async logout() {
    try {
    } catch (e) {
      console.error('API Error - logout:', e)
    }
    return true
  }
}
