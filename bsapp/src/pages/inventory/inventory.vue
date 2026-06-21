<template>
  <view class="page">
    <view class="head">
      <text class="title">库存管理</text>
      <text class="sub">手动补充买到的食材，完成一餐后自动扣减</text>
    </view>

    <view class="stats">
      <view><text>{{ stats.total_items || items.length }}</text><text>食材</text></view>
      <view><text>{{ stats.total_amount_known || 0 }}</text><text>有数量</text></view>
      <view><text>{{ Object.keys(stats.by_source || {}).length }}</text><text>来源</text></view>
    </view>

    <view class="add-card">
      <input v-model="form.name" placeholder="食材名，如 南瓜" placeholder-class="ph" />
      <view class="form-row">
        <input v-model="form.amount" type="number" placeholder="数量" placeholder-class="ph" />
        <input v-model="form.unit" placeholder="单位 g/个/ml" placeholder-class="ph" />
      </view>
      <button @tap="addItem">加入库存</button>
    </view>

    <view class="list">
      <view v-for="item in items" :key="item.id" class="row">
        <view class="glyph">{{ item.name.slice(0, 1) }}</view>
        <view class="body">
          <text class="name">{{ item.name }}</text>
          <text class="meta">{{ item.display || '数量待确认' }} · {{ freshnessLabel(item.freshness) }} · {{ item.source || 'manual' }}</text>
        </view>
        <button class="mini" @tap="editItem(item)">编辑</button>
        <button class="mini danger" @tap="deleteItem(item)">删除</button>
      </view>
    </view>

    <view v-if="!items.length && !loading" class="empty">暂无库存，拍照识别或手动添加食材后会显示在这里。</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ApiService } from '@/api/index'

const items = ref([])
const stats = ref({})
const loading = ref(false)
const form = ref({ name: '', amount: '', unit: 'g', freshness: 'normal', source: 'manual' })

onShow(load)

async function load() {
  loading.value = true
  try {
    items.value = await ApiService.getInventory()
    stats.value = await ApiService.getInventoryStats()
  } catch (e) {
    uni.showToast({ title: e.message || '库存加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function addItem() {
  if (!form.value.name.trim()) {
    uni.showToast({ title: '请输入食材名', icon: 'none' })
    return
  }
  try {
    await ApiService.addInventoryItem(form.value)
    form.value = { name: '', amount: '', unit: 'g', freshness: 'normal', source: 'manual' }
    await load()
    uni.showToast({ title: '已加入库存', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e.message || '添加失败', icon: 'none' })
  }
}

function editItem(item) {
  uni.showModal({
    title: `修改 ${item.name}`,
    editable: true,
    placeholderText: item.display || '例如 300g',
    success: async (res) => {
      if (!res.confirm) return
      const text = (res.content || '').trim()
      const m = text.match(/(\d+(?:\.\d+)?)\s*(.*)/)
      try {
        await ApiService.updateInventoryItem(item.id, {
          amount: m ? Number(m[1]) : item.amount,
          unit: m ? (m[2] || item.unit) : item.unit,
          freshness: item.freshness || 'normal'
        })
        await load()
      } catch (e) {
        uni.showToast({ title: e.message || '更新失败', icon: 'none' })
      }
    }
  })
}

async function deleteItem(item) {
  const res = await new Promise(resolve => uni.showModal({ title: '删除食材', content: `确认删除 ${item.name}？`, success: resolve }))
  if (!res.confirm) return
  await ApiService.deleteInventoryItem(item.id)
  await load()
}

function freshnessLabel(f) {
  return ({ high: '新鲜', normal: '正常', medium: '普通', low: '待确认' })[f] || '待确认'
}
</script>

<style scoped>
.page { min-height: 100vh; padding: 30rpx; background: linear-gradient(180deg,#F7FCFA,#EEF7F2); }
.head { margin-bottom: 22rpx; }
.title { display:block; font-size: 44rpx; font-weight: 950; color:#173B2E; }
.sub { display:block; margin-top:8rpx; color:#66756D; font-size:24rpx; }
.stats { display:grid; grid-template-columns: repeat(3,1fr); gap:12rpx; margin-bottom:18rpx; }
.stats view,.add-card,.row,.empty { background:#fff; border-radius:24rpx; box-shadow:0 10rpx 32rpx rgba(23,59,46,.08); }
.stats view { padding:18rpx; }
.stats text:first-child { display:block; font-size:34rpx; font-weight:950; color:#173B2E; }
.stats text:last-child { display:block; margin-top:6rpx; color:#7A8982; font-size:21rpx; }
.add-card { padding:20rpx; margin-bottom:20rpx; }
input { height:72rpx; padding:0 18rpx; border-radius:18rpx; background:#F3F8F5; font-size:26rpx; color:#173B2E; }
.form-row { display:grid; grid-template-columns: 1fr 1fr; gap:12rpx; margin:12rpx 0; }
button { height:72rpx; border-radius:999rpx; background:#23A978; color:#fff; font-size:26rpx; font-weight:900; border:none; }
button::after { border:none; }
.row { display:flex; align-items:center; gap:14rpx; padding:16rpx; margin-bottom:12rpx; }
.glyph { width:58rpx; height:58rpx; border-radius:18rpx; background:#E8F7EF; color:#23A978; display:flex; align-items:center; justify-content:center; font-weight:950; }
.body { flex:1; min-width:0; }
.name { display:block; font-size:28rpx; color:#173B2E; font-weight:900; }
.meta { display:block; margin-top:4rpx; color:#7A8982; font-size:21rpx; }
.mini { width:84rpx; height:50rpx; font-size:21rpx; background:#173B2E; }
.mini.danger { background:#E85D4F; }
.empty { padding:24rpx; color:#7A8982; font-size:24rpx; }
.ph { color:#A5B0AA; }
</style>

