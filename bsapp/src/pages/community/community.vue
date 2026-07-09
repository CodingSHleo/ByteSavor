<template>
  <view class="page">
    <view class="hero">
      <view>
        <text class="eyebrow">ByteSavor 社区</text>
        <text class="title">发现真实餐桌灵感</text>
      </view>
      <button class="publish-btn" @tap="publish">发布</button>
    </view>

    <scroll-view scroll-x class="tabs" :show-scrollbar="false">
      <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: category === tab.key }" @tap="setCategory(tab.key)">{{ tab.label }}</view>
    </scroll-view>

    <view class="sort-row">
      <view v-for="item in sortOptions" :key="item.key" class="sort-pill" :class="{ active: sortMode === item.key }" @tap="sortMode = item.key">{{ item.label }}</view>
    </view>

    <view v-if="loading && !posts.length" class="empty">正在加载社区内容...</view>
    <view v-else-if="error" class="empty"><text>{{ error }}</text><button class="retry" @tap="reload">重试</button></view>
    <view v-else-if="!posts.length" class="empty">还没有内容，发布第一条菜谱或饮食记录。</view>

    <view v-else class="feed">
      <view class="column">
        <view v-for="post in leftPosts" :key="post.id" class="card" @tap="detail(post)">
          <image v-if="(post.images||[])[0]" :src="(post.images||[])[0]" class="card-img" mode="aspectFill" />
          <view v-else class="card-img card-img-place" :class="'tone-'+post.category">
            <text>{{ post.category==='health'?'问':post.category==='checkin'?'记':'食' }}</text>
          </view>
          <view class="card-badge">{{ catLabel(post.category) }}</view>
          <view v-if="isAdmin" class="admin-del" @tap.stop="adminDelete(post)">✕</view>
          <view class="card-body">
            <text class="card-title">{{ post.title }}</text>
            <text v-if="post.content" class="card-desc">{{ cropText(post.content, 40) }}</text>
            <text v-if="recipeSummary(post)" class="card-recipe">{{ recipeSummary(post) }}</text>
            <view class="card-foot">
              <view class="card-author">
                <image v-if="(post.author||{}).avatar_url" :src="post.author.avatar_url" class="avatar-img" mode="aspectFill" />
                <view v-else class="avatar">{{ ((post.author||{}).name||'U')[0].toUpperCase() }}</view>
                <text class="author-name">{{ (post.author||{}).name||'社区用户' }}</text>
              </view>
              <view class="card-stats">
                <text class="stat" :class="{ active: post.liked_by_me }" @tap.stop="toggleLike(post)">{{ post.liked_by_me ? '♥' : '♡' }} {{ post.like_count||0 }}</text>
                <text>{{ commentIcon }} {{ post.comment_count||0 }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
      <view class="column">
        <view v-for="post in rightPosts" :key="post.id" class="card" @tap="detail(post)">
          <image v-if="(post.images||[])[0]" :src="(post.images||[])[0]" class="card-img" mode="aspectFill" />
          <view v-else class="card-img card-img-place" :class="'tone-'+post.category">
            <text>{{ post.category==='health'?'问':post.category==='checkin'?'记':'食' }}</text>
          </view>
          <view class="card-badge">{{ catLabel(post.category) }}</view>
          <view v-if="isAdmin" class="admin-del" @tap.stop="adminDelete(post)">✕</view>
          <view class="card-body">
            <text class="card-title">{{ post.title }}</text>
            <text v-if="post.content" class="card-desc">{{ cropText(post.content, 40) }}</text>
            <text v-if="recipeSummary(post)" class="card-recipe">{{ recipeSummary(post) }}</text>
            <view class="card-foot">
              <view class="card-author">
                <image v-if="(post.author||{}).avatar_url" :src="post.author.avatar_url" class="avatar-img" mode="aspectFill" />
                <view v-else class="avatar">{{ ((post.author||{}).name||'U')[0].toUpperCase() }}</view>
                <text class="author-name">{{ (post.author||{}).name||'社区用户' }}</text>
              </view>
              <view class="card-stats">
                <text class="stat" :class="{ active: post.liked_by_me }" @tap.stop="toggleLike(post)">{{ post.liked_by_me ? '♥' : '♡' }} {{ post.like_count||0 }}</text>
                <text>💬 {{ post.comment_count||0 }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <button v-if="posts.length && hasMore" class="load-more" :disabled="loading" @tap="loadMore">{{ loading ? '加载中...' : '加载更多' }}</button>
    <button class="float-compose" @tap="publish">+</button>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'

const tabs = [{ key: 'all', label: '推荐' }, { key: 'recipe', label: '菜谱' }, { key: 'health', label: '健康' }, { key: 'checkin', label: '打卡' }]
const sortOptions = [{ key: 'hot', label: '热门' }, { key: 'new', label: '最新' }, { key: 'image', label: '有图' }]
const category = ref('all')
const sortMode = ref('hot')
const posts = ref([])
const loading = ref(false)
const isAdmin = ref(false)
const error = ref('')
const limit = 20
const offset = ref(0)
const hasMore = ref(false)

const sortedPosts = computed(() => {
  const list = [...posts.value]
  if (sortMode.value === 'new') return list.sort((a, b) => new Date(b.created_at||0) - new Date(a.created_at||0))
  if (sortMode.value === 'image') return list.sort((a, b) => ((b.images||[]).length>0) - ((a.images||[]).length>0))
  return list.sort((a, b) => ((b.like_count||0)*3+(b.comment_count||0)*2+((b.images||[]).length?1:0)) - ((a.like_count||0)*3+(a.comment_count||0)*2+((a.images||[]).length?1:0)))
})
const leftPosts = computed(() => sortedPosts.value.filter((_, i) => i % 2 === 0))
const rightPosts = computed(() => sortedPosts.value.filter((_, i) => i % 2 === 1))

onShow(() => {
  // 检查管理员角色
  try {
    const token = uni.getStorageSync('auth_token') || ''
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]))
      isAdmin.value = payload.role === 'admin'
    }
  } catch(e) { isAdmin.value = false }
  reload()
})

async function reload() { offset.value = 0; posts.value = []; await load(true) }
function setCategory(k) { category.value = k; reload() }
async function load(reset) {
  loading.value = true; error.value = ''
  try {
    const o = reset ? 0 : offset.value
    const data = await ApiService.getCommunityPosts(category.value, { limit, offset: o })
    const list = (data.posts||[]).map(p => ({ ...p, images: Array.isArray(p.images)?p.images:[], like_count: Number(p.like_count||0), comment_count: Number(p.comment_count||0) }))
    posts.value = reset ? list : [...posts.value, ...list]
    offset.value = o + limit
    hasMore.value = data.has_more || false
  } catch(e) { error.value = e.message || '加载失败' }
  loading.value = false
}
async function loadMore() { if (!loading.value && hasMore.value) await load(false) }
function detail(post) { uni.navigateTo({ url: `/pages/community-detail/community-detail?postId=${post.id}` }) }
function publish() {
  const token = uni.getStorageSync('auth_token')
  if (!token) { uni.showToast({ title: '请先登录', icon: 'none' }); return }
  uni.navigateTo({ url: '/pages/community-publish/community-publish' })
}
function check(post) { uni.navigateTo({ url: `/pages/recipe-checker/recipe-checker?targetType=community_post&targetId=${post.id}` }) }
async function toggleLike(post) {
  try {
    if (post.liked_by_me) {
      await ApiService.unlikeCommunityPost(post.id)
      post.liked_by_me = false; post.like_count = Math.max(0, (post.like_count||1)-1)
    } else {
      await ApiService.likeCommunityPost(post.id)
      post.liked_by_me = true; post.like_count = (post.like_count||0)+1
    }
  } catch(e) { uni.showToast({ title: '操作失败', icon: 'none' }) }
}
async function adminDelete(post) {
  uni.showModal({
    title: '管理员删除',
    content: `确定删除「${post.title}」？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await ApiService.deleteCommunityPost(post.id)
        posts.value = posts.value.filter(p => p.id !== post.id)
        uni.showToast({ title: '已删除', icon: 'success' })
      } catch(e) { uni.showToast({ title: '删除失败', icon: 'none' }) }
    }
  })
}
function catLabel(c) { return ({ recipe: '菜谱', health: '健康', checkin: '打卡' })[c] || '社区' }
function recipeSummary(post) {
  if (post.category !== 'recipe') return ''
  const p = post.recipe_payload || {}
  const ings = (p.ingredients||[]).slice(0,2).map(i=>i.name||'').filter(Boolean)
  const parts = []
  if (ings.length) parts.push(ings.join(' / '))
  if (p.calories) parts.push(`${p.calories}kcal`)
  if ((p.steps||[]).length) parts.push(`${p.steps.length}步`)
  return parts.join(' · ')
}
function cropText(v, max) { const t = String(v||'').replace(/\s+/g,' ').trim(); return t.length > max ? t.slice(0,max)+'...' : t }
</script>

<style scoped>
.page { min-height: 100vh; padding: calc(28rpx + var(--status-bar-height,0px)) 24rpx 150rpx; background: #f5f5f7; }
.hero { display: flex; align-items: center; justify-content: space-between; gap: 18rpx; padding: 6rpx 2rpx 18rpx; }
.eyebrow { display: block; color: #9098a3; font-size: 21rpx; font-weight: 700; }
.title { display: block; margin-top: 6rpx; color: #1a1c1e; font-size: 36rpx; font-weight: 800; }
.publish-btn { width: 112rpx; height: 60rpx; border: none; border-radius: 999rpx; background: #1a1c1e; color: #fff; font-size: 24rpx; font-weight: 800; }
.publish-btn::after { border: none; }
.tabs { white-space: nowrap; margin: 8rpx 0 16rpx; }
.tab { display: inline-flex; align-items: center; justify-content: center; min-width: 92rpx; height: 58rpx; margin-right: 12rpx; padding: 0 24rpx; border-radius: 999rpx; background: #fff; color: #6b7280; font-size: 25rpx; font-weight: 700; }
.tab.active { background: #1a1c1e; color: #fff; }
.sort-row { display: flex; gap: 12rpx; margin-bottom: 20rpx; }
.sort-pill { height: 48rpx; padding: 0 18rpx; border-radius: 999rpx; display: flex; align-items: center; color: #8b95a5; font-size: 23rpx; font-weight: 700; }
.sort-pill.active { background: #e8f7ef; color: #16865d; }
.feed { display: flex; align-items: flex-start; gap: 16rpx; }
.column { flex: 1; min-width: 0; }
.card { position: relative; margin-bottom: 16rpx; border-radius: 16rpx; background: #fff; overflow: hidden; box-shadow: 0 2rpx 12rpx rgba(0,0,0,.06); }
.card-img { width: 100%; height: 220rpx; display: block; }
.card-img-place { height: 160rpx; display: flex; align-items: center; justify-content: center; }
.card-img-place text { width: 72rpx; height: 72rpx; border-radius: 50%; background: rgba(255,255,255,.8); display: flex; align-items: center; justify-content: center; font-size: 30rpx; font-weight: 800; color: #333; }
.tone-recipe { background: linear-gradient(135deg, #fff1e8, #e8f7ef); }
.tone-health { background: linear-gradient(135deg, #e9f2ff, #f4ecff); }
.tone-checkin { background: linear-gradient(135deg, #fff7d6, #ecfdf5); }
.card-badge { position: absolute; top: 12rpx; left: 12rpx; height: 34rpx; padding: 0 12rpx; border-radius: 999rpx; background: rgba(0,0,0,.55); color: #fff; font-size: 19rpx; font-weight: 700; display: flex; align-items: center; }
.admin-del { position: absolute; top: 10rpx; right: 10rpx; width: 40rpx; height: 40rpx; border-radius: 50%; background: rgba(220,38,38,.85); color: #fff; font-size: 24rpx; display: flex; align-items: center; justify-content: center; z-index: 5; }
.card-body { padding: 18rpx 18rpx 14rpx; }
.card-title { display: block; font-size: 26rpx; font-weight: 750; color: #1a1c1e; line-height: 1.35; margin-bottom: 6rpx; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.card-desc { display: block; font-size: 22rpx; color: #8b95a5; line-height: 1.5; margin-bottom: 8rpx; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.card-recipe { display: block; font-size: 20rpx; color: #16865d; margin-bottom: 10rpx; font-weight: 600; }
.card-foot { display: flex; justify-content: space-between; align-items: center; gap: 12rpx; }
.card-author { display: flex; align-items: center; gap: 8rpx; min-width: 0; }
.avatar { width: 36rpx; height: 36rpx; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-size: 20rpx; font-weight: 800; color: #666; flex-shrink: 0; }
.avatar-img { width: 36rpx; height: 36rpx; border-radius: 50%; flex-shrink: 0; }
.author-name { font-size: 20rpx; color: #8b95a5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-stats { display: flex; gap: 16rpx; font-size: 22rpx; color: #8b95a5; }
.card-stats .active { color: #e74c3c; }
.empty { text-align: center; padding: 80rpx 0; color: #8b95a5; font-size: 26rpx; }
.retry { margin-top: 20rpx; padding: 12rpx 32rpx; border-radius: 999rpx; background: #1a1c1e; color: #fff; border: none; font-size: 24rpx; }
.retry::after { border: none; }
.load-more { width: 100%; height: 72rpx; margin-top: 20rpx; border-radius: 999rpx; background: #fff; color: #666; border: none; font-size: 25rpx; }
.load-more::after { border: none; }
.float-compose { position: fixed; right: 28rpx; bottom: 160rpx; width: 88rpx; height: 88rpx; border-radius: 50%; background: #1a1c1e; color: #fff; font-size: 40rpx; border: none; display: flex; align-items: center; justify-content: center; box-shadow: 0 8rpx 24rpx rgba(0,0,0,.15); z-index: 100; }
.float-compose::after { border: none; }
</style>
