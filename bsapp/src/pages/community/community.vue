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
      <view
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: category === tab.key }"
        @tap="setCategory(tab.key)"
      >
        {{ tab.label }}
      </view>
    </scroll-view>

    <view class="sort-row">
      <view
        v-for="item in sortOptions"
        :key="item.key"
        class="sort-pill"
        :class="{ active: sortMode === item.key }"
        @tap="sortMode = item.key"
      >
        {{ item.label }}
      </view>
    </view>

    <view v-if="loading && !posts.length" class="empty">正在加载社区内容...</view>
    <view v-else-if="error" class="empty">
      <text>{{ error }}</text>
      <button class="retry" @tap="reload">重试</button>
    </view>
    <view v-else-if="!posts.length" class="empty">还没有内容，发布第一条菜谱或饮食记录。</view>

    <view v-else class="feed">
      <view class="column">
        <view v-for="post in leftPosts" :key="post.id" class="note-card" @tap="detail(post)">
          <community-card
            :post="post"
            :category-label="categoryLabel(post.category)"
            :summary="recipeSummary(post)"
            :text-mode="settingsStore.communityTextMode"
            @preview="previewImages(post, $event)"
            @like="toggleLike(post)"
            @favorite="toggleFavorite(post)"
            @check="check(post)"
          />
        </view>
      </view>
      <view class="column">
        <view v-for="post in rightPosts" :key="post.id" class="note-card" @tap="detail(post)">
          <community-card
            :post="post"
            :category-label="categoryLabel(post.category)"
            :summary="recipeSummary(post)"
            :text-mode="settingsStore.communityTextMode"
            @preview="previewImages(post, $event)"
            @like="toggleLike(post)"
            @favorite="toggleFavorite(post)"
            @check="check(post)"
          />
        </view>
      </view>
    </view>

    <button v-if="posts.length && hasMore" class="load-more" :disabled="loading" @tap="loadMore">
      {{ loading ? '加载中...' : '加载更多' }}
    </button>

    <button class="float-compose" @tap="publish">+</button>
  </view>
</template>

<script setup>
import { computed, defineComponent, h, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'
import { useSettingsStore } from '@/store/settings'

const CommunityCard = defineComponent({
  props: {
    post: { type: Object, required: true },
    categoryLabel: { type: String, default: '' },
    summary: { type: String, default: '' },
    textMode: { type: String, default: 'summary' },
  },
  emits: ['preview', 'like', 'favorite', 'check'],
  setup(props, { emit }) {
    const cover = computed(() => (props.post.images || [])[0] || '')
    const compactContent = computed(() => summarizeContent(props.post.content, props.textMode))
    const author = computed(() => authorInfo(props.post))
    return () => h('view', { class: 'card-inner' }, [
      cover.value
        ? h('image', {
            class: 'cover',
            src: cover.value,
            mode: 'aspectFill',
            onTap: (event) => {
              event.stopPropagation()
              emit('preview', 0)
            },
          })
        : h('view', { class: ['cover', 'cover-placeholder', `tone-${props.post.category || 'recipe'}`] }, [
            h('text', { class: 'placeholder-mark' }, props.post.category === 'health' ? '问' : props.post.category === 'checkin' ? '记' : '食'),
          ]),
      props.post.images?.length > 1
        ? h('view', { class: 'image-count' }, `1/${props.post.images.length}`)
        : null,
      h('view', { class: 'card-body' }, [
        h('view', { class: 'meta-row' }, [
          h('text', { class: 'badge' }, props.categoryLabel),
          h('text', { class: 'time' }, formatTime(props.post.created_at)),
        ]),
        h('text', { class: 'post-title' }, props.post.title),
        compactContent.value ? h('text', { class: 'post-copy' }, compactContent.value) : null,
        props.summary ? h('text', { class: 'recipe-summary' }, props.summary) : null,
        h('view', { class: 'author-row' }, [
          author.value.avatar_url
            ? h('image', { class: 'avatar-img', src: author.value.avatar_url, mode: 'aspectFill' })
            : h('view', { class: 'avatar' }, shortName(author.value.name)),
          h('text', { class: 'author' }, userLabel(author.value.name)),
        ]),
        h('view', { class: 'actions' }, [
          h('view', {
            class: ['action', props.post.liked_by_me ? 'active' : ''],
            onTap: (event) => {
              event.stopPropagation()
              emit('like')
            },
          }, [
            h('text', { class: 'action-icon' }, props.post.liked_by_me ? '♥' : '♡'),
            h('text', {}, String(props.post.like_count || 0)),
          ]),
          h('view', {
            class: ['action', props.post.favorited_by_me ? 'active favorite-active' : ''],
            onTap: (event) => {
              event.stopPropagation()
              emit('favorite')
            },
          }, [
            h('text', { class: 'action-icon' }, props.post.favorited_by_me ? '★' : '☆'),
            h('text', {}, props.post.favorited_by_me ? '已收' : '收藏'),
          ]),
          h('view', { class: 'action muted' }, [
            h('text', { class: 'action-icon' }, '💬'),
            h('text', {}, String(props.post.comment_count || 0)),
          ]),
          props.post.category === 'recipe'
            ? h('view', {
                class: 'action check',
                onTap: (event) => {
                  event.stopPropagation()
                  emit('check')
                },
              }, '清点')
            : null,
        ]),
      ]),
    ])
  },
})

const tabs = [
  { key: 'all', label: '推荐' },
  { key: 'recipe', label: '菜谱' },
  { key: 'health', label: '健康' },
  { key: 'checkin', label: '打卡' },
]
const sortOptions = [
  { key: 'hot', label: '热门' },
  { key: 'new', label: '最新' },
  { key: 'image', label: '有图' },
]
const category = ref('all')
const sortMode = ref('hot')
const posts = ref([])
const loading = ref(false)
const error = ref('')
const limit = 20
const offset = ref(0)
const hasMore = ref(false)
const settingsStore = useSettingsStore()

const sortedPosts = computed(() => {
  const list = [...posts.value]
  if (sortMode.value === 'new') {
    return list.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
  }
  if (sortMode.value === 'image') {
    return list.sort((a, b) => Number((b.images || []).length > 0) - Number((a.images || []).length > 0))
  }
  return list.sort((a, b) => hotScore(b) - hotScore(a))
})
const leftPosts = computed(() => sortedPosts.value.filter((_, idx) => idx % 2 === 0))
const rightPosts = computed(() => sortedPosts.value.filter((_, idx) => idx % 2 === 1))

onShow(reload)

async function load(reset = false) {
  loading.value = true
  error.value = ''
  try {
    const nextOffset = reset ? 0 : offset.value
    const data = await ApiService.getCommunityPosts(category.value, { limit, offset: nextOffset })
    const nextPosts = (data.posts || []).map(normalizePost)
    posts.value = reset ? nextPosts : posts.value.concat(nextPosts)
    offset.value = nextOffset + nextPosts.length
    hasMore.value = !!data.has_more
  } catch (e) {
    error.value = e.message || '社区加载失败'
  } finally {
    loading.value = false
  }
}
function reload() { offset.value = 0; hasMore.value = false; load(true) }
function loadMore() { if (!loading.value && hasMore.value) load(false) }
function setCategory(key) { category.value = key; reload() }
function publish() {
  if (!uni.getStorageSync('auth_token')) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 400)
    return
  }
  uni.navigateTo({ url: '/pages/community-publish/community-publish' })
}
function detail(post) { uni.navigateTo({ url: `/pages/community-detail/community-detail?postId=${post.id}` }) }
function check(post) { uni.navigateTo({ url: `/pages/recipe-checker/recipe-checker?targetType=community_post&targetId=${post.id}` }) }
function previewImages(post, idx) { uni.previewImage({ current: idx, urls: post.images || [] }) }

async function toggleLike(post) {
  try {
    if (post.liked_by_me) {
      await ApiService.unlikeCommunityPost(post.id)
      post.liked_by_me = false
      post.like_count = Math.max(0, (post.like_count || 1) - 1)
    } else {
      await ApiService.likeCommunityPost(post.id)
      post.liked_by_me = true
      post.like_count = (post.like_count || 0) + 1
    }
  } catch (e) {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}
async function toggleFavorite(post) {
  try {
    if (post.favorited_by_me) {
      await ApiService.removeFavorite('community_post', post.id)
      post.favorited_by_me = false
      uni.showToast({ title: '已取消收藏', icon: 'none' })
    } else {
      await ApiService.addFavorite('community_post', post.id, post)
      post.favorited_by_me = true
      uni.showToast({ title: '已收藏', icon: 'success' })
    }
  } catch (e) {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function normalizePost(post) {
  return {
    ...post,
    images: Array.isArray(post.images) ? post.images : [],
    like_count: Number(post.like_count || 0),
    comment_count: Number(post.comment_count || 0),
  }
}
function authorInfo(post) {
  const author = post?.author || {}
  const rawName = String(author.name || '').trim()
  return {
    name: rawName && !/^u_[a-f0-9]{4,}/i.test(rawName) ? rawName : '社区用户',
    avatar_url: String(author.avatar_url || '').trim(),
  }
}
function categoryLabel(c) { return ({ recipe: '菜谱', health: '健康', checkin: '打卡' })[c] || '社区' }
function recipeSummary(post) {
  if (post.category !== 'recipe') return ''
  const payload = post.recipe_payload || {}
  const ingredients = (payload.ingredients || []).slice(0, 2).map(i => i.name || '').filter(Boolean)
  const parts = []
  if (ingredients.length) parts.push(ingredients.join(' / '))
  if (payload.calories) parts.push(`${payload.calories} kcal`)
  if ((payload.steps || []).length) parts.push(`${payload.steps.length} 步`)
  return parts.join(' · ')
}
function hotScore(post) {
  return (post.like_count || 0) * 3 + (post.comment_count || 0) * 2 + ((post.images || []).length ? 1 : 0)
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
function summarizeContent(value, mode = 'summary') {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (!text) return ''
  if (/^(t|x|test|测试|1|11|111)$/i.test(text)) return ''
  const limit = mode === 'full' ? 92 : 42
  if (mode === 'summary' && text.length <= 2) return ''
  return text.length > limit ? `${text.slice(0, limit)}...` : text
}
function shortName(name) {
  const text = String(name || 'U').trim()
  return (text[0] || 'U').toUpperCase()
}
function userLabel(value) {
  const text = String(value || '社区用户').trim()
  if (!text) return '社区用户'
  if (text.length <= 8) return text
  return `${text.slice(0, 8)}...`
}
</script>

<style>
.page {
  min-height: 100vh;
  padding: calc(28rpx + var(--status-bar-height, 0px)) 24rpx 150rpx;
  background: #f7f7f8;
}
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 6rpx 2rpx 18rpx;
}
.eyebrow {
  display: block;
  color: #7a828e;
  font-size: 21rpx;
  font-weight: 700;
}
.title {
  display: block;
  margin-top: 6rpx;
  color: #15171a;
  font-size: 36rpx;
  font-weight: 800;
  letter-spacing: 0;
}
.publish-btn {
  width: 112rpx;
  height: 60rpx;
  border: none;
  border-radius: 999rpx;
  background: #15171a;
  color: #fff;
  font-size: 24rpx;
  font-weight: 800;
}
button::after { border: none; }
.tabs {
  white-space: nowrap;
  margin: 4rpx 0 16rpx;
}
.tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 92rpx;
  height: 58rpx;
  margin-right: 12rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: #fff;
  color: #6b7280;
  font-size: 25rpx;
  font-weight: 700;
}
.tab.active {
  background: #15171a;
  color: #fff;
}
.sort-row {
  display: flex;
  gap: 12rpx;
  margin-bottom: 18rpx;
}
.sort-pill {
  height: 48rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  background: transparent;
  color: #7b8491;
  font-size: 23rpx;
  font-weight: 700;
}
.sort-pill.active {
  background: #e8f7ef;
  color: #16865d;
}
.feed {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}
.column {
  flex: 1;
  min-width: 0;
}
.note-card {
  position: relative;
  margin-bottom: 18rpx;
  overflow: hidden;
  border-radius: 18rpx;
  background: #fff;
  box-shadow: 0 8rpx 22rpx rgba(17, 24, 39, 0.055);
}
.cover {
  width: 100%;
  height: 214rpx;
  display: block;
  background: #eef2f7;
}
.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}
.tone-recipe { background: linear-gradient(135deg, #fff1e8, #e8f7ef); }
.tone-health { background: linear-gradient(135deg, #e9f2ff, #f4ecff); }
.tone-checkin { background: linear-gradient(135deg, #fff7d6, #ecfdf5); }
.placeholder-mark {
  width: 76rpx;
  height: 76rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,.82);
  color: #15171a;
  font-size: 34rpx;
  font-weight: 800;
}
.image-count {
  position: absolute;
  top: 12rpx;
  right: 12rpx;
  height: 36rpx;
  padding: 0 12rpx;
  border-radius: 999rpx;
  background: rgba(17,24,39,.72);
  color: #fff;
  font-size: 20rpx;
  display: flex;
  align-items: center;
}
.card-body {
  padding: 18rpx 18rpx 16rpx;
}
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 10rpx;
}
.badge {
  flex-shrink: 0;
  height: 34rpx;
  padding: 0 12rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  background: #f0fdf4;
  color: #16865d;
  font-size: 19rpx;
  font-weight: 750;
}
.time {
  min-width: 0;
  color: #9ca3af;
  font-size: 19rpx;
  white-space: nowrap;
}
.post-title {
  display: block;
  color: #17191d;
  font-size: 24rpx;
  line-height: 1.34;
  font-weight: 750;
}
.post-copy {
  display: block;
  margin-top: 9rpx;
  color: #5d6673;
  font-size: 21rpx;
  line-height: 1.5;
}
.recipe-summary {
  display: block;
  margin-top: 10rpx;
  color: #16865d;
  font-size: 20rpx;
  font-weight: 750;
  line-height: 1.35;
}
.author-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 16rpx;
  min-width: 0;
}
.avatar,
.avatar-img {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  flex-shrink: 0;
}
.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #22252b, #555d6b);
  color: #fff;
  font-size: 18rpx;
  font-weight: 800;
}
.avatar-img { display: block; background: #eef2f7; }
.author {
  min-width: 0;
  max-width: 150rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: #6b7280;
  font-size: 20rpx;
  font-weight: 650;
}
.actions {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8rpx;
  margin-top: 14rpx;
  overflow: hidden;
}
.action {
  min-width: 0;
  height: 38rpx;
  padding: 0 9rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  color: #6b7280;
  background: #f7f8fa;
  font-size: 19rpx;
  font-weight: 750;
  transition: transform .16s ease, background-color .16s ease, color .16s ease;
}
.action.active {
  color: #e5484d;
  background: #fff1f2;
  transform: scale(1.04);
}
.action.favorite-active {
  color: #b7791f;
  background: #fff7e6;
}
.action.muted {
  color: #8a94a3;
}
.action.check {
  color: #fff;
  background: #15171a;
  flex-shrink: 0;
  min-width: 54rpx;
}
.action-icon {
  font-size: 21rpx;
  line-height: 1;
}
.empty {
  margin-top: 24rpx;
  padding: 42rpx 24rpx;
  border-radius: 20rpx;
  background: #fff;
  color: #6b7280;
  text-align: center;
  font-size: 24rpx;
  box-shadow: 0 10rpx 28rpx rgba(17, 24, 39, 0.06);
}
.retry,
.load-more {
  width: 100%;
  height: 64rpx;
  margin-top: 16rpx;
  border: none;
  border-radius: 999rpx;
  background: #15171a;
  color: #fff;
  font-size: 24rpx;
  font-weight: 800;
}
.load-more[disabled] {
  opacity: .65;
}
.float-compose {
  position: fixed;
  right: 34rpx;
  bottom: 124rpx;
  width: 92rpx;
  height: 92rpx;
  border: none;
  border-radius: 50%;
  background: #23a978;
  color: #fff;
  font-size: 44rpx;
  font-weight: 800;
  line-height: 92rpx;
  box-shadow: 0 18rpx 42rpx rgba(35, 169, 120, .28);
}

@media screen and (min-width: 720px) {
  .page {
    max-width: 430px;
    margin: 0 auto;
  }
  .cover {
    height: 236rpx;
  }
}
</style>
