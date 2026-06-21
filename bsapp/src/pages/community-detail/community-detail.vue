<template>
  <view class="page">
    <view v-if="loading" class="card muted">正在加载帖子...</view>
    <view v-else-if="error" class="card muted">
      <text>{{ error }}</text>
      <button class="full" @tap="load">重试</button>
    </view>

    <view v-if="post" class="post-card">
      <view class="author-row">
        <image v-if="author.avatar_url" class="avatar-img" :src="author.avatar_url" mode="aspectFill" />
        <view v-else class="avatar">{{ shortName(author.name) }}</view>
        <view class="author-main">
          <text class="author-name">{{ author.name }}</text>
          <text class="author-meta">{{ categoryLabel(post.category) }} · {{ formatTime(post.created_at) }}</text>
        </view>
        <text class="badge">{{ shortCategory(post.category) }}</text>
      </view>

      <text class="title">{{ post.title }}</text>
      <text v-if="post.content" class="content">{{ post.content }}</text>
      <view v-if="post.images && post.images.length" class="image-grid">
        <image
          v-for="(img, idx) in post.images"
          :key="idx"
          :src="img"
          mode="aspectFill"
          class="post-image"
          @tap="previewImages(idx)"
        />
      </view>
      <view v-if="post.category === 'recipe'" class="recipe-box">
        <text class="section small">食材</text>
        <text v-for="(ing, idx) in recipeIngredients" :key="idx" class="recipe-line">{{ ing.name }} {{ ing.amount || '' }}</text>
        <text v-if="recipeCalories" class="recipe-line">{{ recipeCalories }} kcal</text>
        <text v-if="recipeSteps.length" class="section small">步骤</text>
        <text v-for="(step, idx) in recipeSteps" :key="`step-${idx}`" class="recipe-line">{{ idx + 1 }}. {{ step }}</text>
      </view>
      <view v-if="post.category === 'health'" class="notice">饮食建议仅供健康管理参考，不能替代医生诊断。</view>
      <view class="actions">
        <button class="like" :class="{active: post.liked_by_me}" @tap="toggleLike">
          <text>{{ post.liked_by_me ? '♥' : '♡' }}</text>
          <text>{{ post.liked_by_me ? '已赞' : '点赞' }} {{ post.like_count || 0 }}</text>
        </button>
        <button class="like favorite" :class="{active: post.favorited_by_me}" @tap="toggleFavorite">
          <text>{{ post.favorited_by_me ? '★' : '☆' }}</text>
          <text>{{ post.favorited_by_me ? '已收藏' : '收藏' }}</text>
        </button>
        <button v-if="post.category === 'recipe'" class="dark" @tap="check">清点食材</button>
      </view>
      <button v-if="canDelete" class="danger" @tap="deletePost">删除帖子</button>
    </view>

    <view class="card">
      <text class="section">评论</text>
      <view v-if="!comments.length" class="comment empty-comment">暂无评论</view>
      <view v-for="c in comments" :key="c.id" class="comment">{{ c.content }}</view>
      <view class="comment-box">
        <input v-model="comment" placeholder="写下你的想法" placeholder-class="ph" />
        <button :disabled="commenting" @tap="sendComment">{{ commenting ? '...' : '发送' }}</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { useAuthStore } from '@/store/auth'

const postId = ref('')
const post = ref(null)
const comments = ref([])
const comment = ref('')
const loading = ref(false)
const error = ref('')
const commenting = ref(false)
const authStore = useAuthStore()

const currentUserId = computed(() => authStore.currentUser?.userId || uni.getStorageSync('user_id') || '')
const canDelete = computed(() => post.value && currentUserId.value && post.value.user_id === currentUserId.value)
const recipeIngredients = computed(() => (post.value?.recipe_payload?.ingredients || []).filter(i => i.name))
const recipeSteps = computed(() => post.value?.recipe_payload?.steps || [])
const recipeCalories = computed(() => post.value?.recipe_payload?.calories || 0)
const author = computed(() => {
  const a = post.value?.author || {}
  const rawName = String(a.name || '').trim()
  return {
    name: rawName && !/^u_[a-f0-9]{4,}/i.test(rawName) ? rawName : '社区用户',
    avatar_url: String(a.avatar_url || '').trim(),
  }
})

onLoad(async (options) => {
  postId.value = options.postId || ''
  await load()
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await ApiService.getCommunityPost(postId.value)
    post.value = data.post
    comments.value = data.comments || []
  } catch (e) {
    error.value = e.message || '获取帖子失败'
  } finally {
    loading.value = false
  }
}
async function toggleLike() {
  if (!post.value) return
  try {
    if (post.value.liked_by_me) await ApiService.unlikeCommunityPost(postId.value)
    else await ApiService.likeCommunityPost(postId.value)
    await load()
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  }
}
async function toggleFavorite() {
  if (!post.value) return
  try {
    if (post.value.favorited_by_me) {
      await ApiService.removeFavorite('community_post', post.value.id)
      post.value.favorited_by_me = false
      uni.showToast({ title: '已取消收藏', icon: 'none' })
    } else {
      await ApiService.addFavorite('community_post', post.value.id, post.value)
      post.value.favorited_by_me = true
      uni.showToast({ title: '已收藏', icon: 'success' })
    }
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  }
}
function check() { uni.navigateTo({ url: `/pages/recipe-checker/recipe-checker?targetType=community_post&targetId=${post.value.id}` }) }
function previewImages(idx) { uni.previewImage({ current: idx, urls: post.value?.images || [] }) }
async function sendComment() {
  if (!comment.value.trim()) return
  commenting.value = true
  try {
    await ApiService.addCommunityComment(postId.value, comment.value)
    comment.value = ''
    await load()
  } catch (e) {
    uni.showToast({ title: e.message || '评论失败', icon: 'none' })
  } finally {
    commenting.value = false
  }
}
async function deletePost() {
  uni.showModal({
    title: '删除帖子',
    content: '确定删除这条社区内容吗？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await ApiService.deleteCommunityPost(postId.value)
        uni.showToast({ title: '已删除', icon: 'success' })
        setTimeout(() => uni.navigateBack(), 500)
      } catch (e) {
        uni.showToast({ title: e.message || '删除失败', icon: 'none' })
      }
    }
  })
}
function categoryLabel(c) { return ({ recipe: '菜谱分享', health: '健康咨询', checkin: '饮食打卡' })[c] || c }
function shortCategory(c) { return ({ recipe: '菜谱', health: '健康', checkin: '打卡' })[c] || '社区' }
function shortName(name) {
  const text = String(name || '社').trim()
  return (text[0] || '社').toUpperCase()
}
function formatTime(value) {
  if (!value) return '刚刚'
  const diff = Date.now() - new Date(value).getTime()
  if (!Number.isFinite(diff) || diff < 0) return '刚刚'
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  return `${Math.floor(hours / 24)}天前`
}
</script>

<style scoped>
.page { min-height:100vh; padding:28rpx 24rpx 130rpx; background:#F7F7F8; }
.card,
.post-card { background:#fff; border-radius:22rpx; padding:22rpx; margin-bottom:18rpx; box-shadow:0 8rpx 24rpx rgba(17,24,39,.06); }
.author-row { display:flex; align-items:center; gap:12rpx; min-width:0; margin-bottom:18rpx; }
.avatar,
.avatar-img { width:56rpx; height:56rpx; border-radius:50%; flex-shrink:0; }
.avatar { display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#22252b,#555d6b); color:#fff; font-size:24rpx; font-weight:800; }
.avatar-img { display:block; background:#eef2f7; }
.author-main { flex:1; min-width:0; }
.author-name { display:block; color:#17191d; font-size:25rpx; font-weight:750; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
.author-meta { display:block; margin-top:4rpx; color:#8a94a3; font-size:20rpx; }
.badge { flex-shrink:0; display:inline-flex; background:#E8F7EF; color:#16865d; border-radius:999rpx; padding:6rpx 14rpx; font-size:20rpx; font-weight:750; }
.title { display:block; margin-top:4rpx; font-size:36rpx; line-height:1.25; font-weight:850; color:#15171a; letter-spacing:0; }
.content { display:block; margin-top:16rpx; color:#4b5563; font-size:26rpx; line-height:1.65; }
.image-grid { display:flex; flex-wrap:wrap; gap:12rpx; margin-top:18rpx; }
.post-image { width:calc((100% - 24rpx) / 3); height:198rpx; border-radius:16rpx; background:#EEF4F0; }
.notice { margin-top:16rpx; padding:16rpx; border-radius:18rpx; background:#FFF6E8; color:#9A651B; font-size:23rpx; }
.recipe-box { margin-top:18rpx; padding:18rpx; border-radius:18rpx; background:#F3F8F5; }
.small { margin:8rpx 0; font-size:24rpx; }
.recipe-line { display:block; margin-top:8rpx; color:#4B5A52; font-size:23rpx; line-height:1.45; }
.actions { display:flex; flex-wrap:wrap; gap:12rpx; margin-top:18rpx; }
button { height:62rpx; border-radius:999rpx; background:#23A978; color:#fff; border:none; font-size:24rpx; font-weight:800; display:flex; align-items:center; justify-content:center; gap:8rpx; }
button::after { border:none; }
.dark { background:#15171a; flex:1; min-width:180rpx; }
.like { flex:1; min-width:180rpx; background:#F3F5F7; color:#69717D; }
.like.active { background:#FFF1F2; color:#E5484D; }
.like.favorite.active { background:#FFF7E6; color:#B7791F; }
.danger,.full { width:100%; margin-top:14rpx; }
.danger { background:#D94F4F; }
.muted { color:#7A8982; font-size:24rpx; }
.section { display:block; font-size:28rpx; font-weight:800; color:#15171a; margin-bottom:14rpx; }
.comment { padding:14rpx 0; border-bottom:1rpx solid #EDF2EF; color:#4B5A52; font-size:24rpx; }
.empty-comment { color:#8A9690; }
.comment-box { display:flex; gap:10rpx; margin-top:16rpx; }
input { flex:1; height:62rpx; background:#F3F5F7; border-radius:999rpx; padding:0 18rpx; font-size:24rpx; }
.comment-box button { width:94rpx; }
.comment-box button[disabled] { opacity:.65; }
.ph { color:#A5B0AA; }
</style>
