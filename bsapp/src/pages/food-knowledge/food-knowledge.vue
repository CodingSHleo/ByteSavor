<template>
  <view class="fk-page">
    <!-- 标签切换 -->
    <view class="fk-tabs">
      <view
        v-for="(tab, idx) in tabs"
        :key="idx"
        class="fk-tab"
        :class="{ active: selectedTab === idx }"
        @tap="selectedTab = idx"
      >
        <image class="fk-tab-icon" :src="`/static/icons/${tab.icon}.svg`" />
        <text class="fk-tab-label">{{ tab.label }}</text>
      </view>
    </view>

    <!-- 食材营养 -->
    <view v-if="selectedTab === 0" class="fk-content">
      <view
        v-for="(item, idx) in ingredientData"
        :key="idx"
        class="fk-card"
        @tap="showDetail(item)"
      >
        <view class="fk-card-header">
          <image class="fk-card-emoji" src="/static/icons/icon_plate.svg" />
          <view class="fk-card-info">
            <text class="fk-card-name">{{ item.name }}</text>
            <text class="fk-card-brief">{{ item.benefits }}</text>
          </view>
          <text class="fk-arrow">›</text>
        </view>
        <view class="fk-card-tags">
          <text
            v-for="(n, nidx) in item.nutrients.slice(0, 2)"
            :key="nidx"
            class="fk-tag"
          >{{ n }}</text>
        </view>
      </view>
    </view>

    <!-- 烹饪技巧 -->
    <view v-if="selectedTab === 1" class="fk-content">
      <view
        v-for="(item, idx) in cookingTipData"
        :key="idx"
        class="fk-card"
      >
        <view class="fk-card-header">
          <image class="fk-card-icon" :src="`/static/icons/${item.icon}.svg`" />
          <text class="fk-card-name">{{ item.title }}</text>
        </view>
        <text class="fk-card-content">{{ item.content }}</text>
      </view>
    </view>

    <!-- 健康建议 -->
    <view v-if="selectedTab === 2" class="fk-content">
      <view
        v-for="(item, idx) in healthAdviceData"
        :key="idx"
        class="fk-card"
      >
        <view class="fk-tag-title">{{ item.title }}</view>
        <text class="fk-card-content">{{ item.content }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { t } from '@/utils/i18n'

const $t = key => t(key)
const selectedTab = ref(0)

const tabs = [
  { icon: 'icon_plate', label: $t('ingredientNutrition') },
  { icon: 'icon_fire', label: $t('cookingTips') },
  { icon: 'icon_leaf', label: $t('healthAdvice') }
]

const ingredientData = [
  { name: '鸡胸肉', nutrients: ['蛋白质 31g', '脂肪 3.6g', '热量 165 kcal'], benefits: '优质蛋白质来源，低脂肪，适合健身人群', tips: '白水煮或清蒸最健康，避免油炸' },
  { name: '西兰花', nutrients: ['纤维 2.4g', '维生素C 89mg', '热量 34 kcal'], benefits: '抗氧化，增强免疫力，促进消化', tips: '快速炒或水煮，避免过度烹饪破坏维生素' },
  { name: '鸡蛋', nutrients: ['蛋白质 6g', '胆碱 126mg', '热量 77 kcal'], benefits: '完全蛋白质，含有叶黄素保护视力', tips: '水煮蛋是最佳食用方式' },
  { name: '番茄', nutrients: ['番茄红素 3mg', '维生素C 14mg', '热量 18 kcal'], benefits: '富含抗氧化物质，预防心血管疾病', tips: '加热后番茄红素更易吸收' },
  { name: '燕麦', nutrients: ['纤维 10.6g', '蛋白质 17g', '热量 389 kcal'], benefits: '降低胆固醇，增加饱腹感，血糖稳定', tips: '早餐食用，可搭配果实和坚果' },
  { name: '三文鱼', nutrients: ['Omega-3 2.3g', '蛋白质 25g', '热量 280 kcal'], benefits: '保护心脑血管，减轻炎症', tips: '清蒸或烤制，保留营养价值' }
]

const cookingTipData = [
  { title: '快速炒菜的黄金法则', icon: 'icon_fire', content: '1. 火力要大（中大火）\n2. 食材需预先准备\n3. 油热后再放食材\n4. 快速翻炒，避免过熟' },
  { title: '如何保留食材营养', icon: 'icon_leaf', content: '• 缩短烹饪时间\n• 用清蒸或水煮替代油炸\n• 避免过度加热\n• 保留蔬菜皮肤（含纤维）' },
  { title: '健康烹饪油的选择', icon: 'icon_olive', content: '• 橄榄油：沙拉、低温烹饪\n• 菜籽油：炒菜（烟点200°C）\n• 花生油：高温炒菜\n• 避免：反复加热的油' },
  { title: '食材搭配原则', icon: 'icon_plate', content: '• 主食 + 蛋白质 + 蔬菜\n• 冷色蔬菜（绿菜、十字花科）\n• 暖色蔬菜（红、橙、黄）\n• 优质碳水化合物\n• 健康脂肪来源' },
  { title: '每周meal prep计划', icon: 'icon_calendar', content: '• 周日准备食材\n• 批量烹饪蛋白质\n• 预备蔬菜（切割、清洗）\n• 煮米或谷物\n• 便于快速组合健康餐' }
]

const healthAdviceData = [
  { title: '早餐很重要', content: '不吃早餐会导致代谢变慢，影响整天的能量水平。建议摄入：蛋白质15-20g + 复合碳水 + 蔬菜水果。' },
  { title: '多喝水很关键', content: '每天至少8杯水（2升）。补充水分有助于代谢、排毒、保持皮肤健康。饭前喝水还能增加饱腹感。' },
  { title: '定时进食，规律作息', content: '保持固定的用餐时间帮助调节血糖和能量水平。避免晚餐过晚或过饱，建议晚上7点前进食。' },
  { title: '少油少盐少糖', content: '• 盐：每天<6g\n• 糖：每天<50g（最好<25g）\n• 油：每天25-30g\n这些都会影响心血管健康。' },
  { title: '食物多样化', content: '每周摄入20+种不同食材。不同颜色的食物提供不同营养。红、绿、黄、橙、紫等各有其营养价值。' },
  { title: '运动配合饮食', content: '健身前2-3小时进食，选择：香蕉+花生酱、燕麦+牛奶、全麦面包+鸡蛋。运动后1小时补充营养。' },
  { title: '零食选择指南', content: '健康零食：坚果、酸奶、水果、黑巧克力、全麦饼干。避免：油炸、高糖、高钠的加工食品。' },
  { title: '外出就餐技巧', content: '• 选择蒸/煮而非炸\n• 要求少油少盐\n• 主动要求酱料分开\n• 选择完整食物而非加工食品\n• 适量进食，可打包剩余' }
]

function showDetail(item) {
  uni.showModal({
    title: item.name,
    content: `${item.nutrients.join('\n')}\n\n${item.benefits}\n\n烹饪建议：${item.tips}`,
    showCancel: false
  })
}
</script>

<style scoped>
.fk-page { min-height: 100vh; background: var(--bg-color); }
.fk-tabs {
  display: flex;
  background: var(--card-bg);
  position: sticky;
  top: 0;
  z-index: 10;
}
.fk-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 4rpx solid transparent;
}
.fk-tab.active { border-bottom-color: var(--accent); }
.fk-tab-icon { width: 40rpx; height: 40rpx; }
.fk-tab-label { font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }
.fk-tab.active .fk-tab-label { color: var(--accent); font-weight: bold; }
.fk-content { padding: 20rpx; }
.fk-card { background: var(--card-bg); border-radius: 16rpx; padding: 24rpx; margin-bottom: 16rpx; }
.fk-card-header { display: flex; align-items: center; }
.fk-card-emoji { width: 48rpx; height: 48rpx; margin-right: 16rpx; object-fit: cover; }
.fk-card-icon { width: 40rpx; height: 40rpx; margin-right: 16rpx; }
.fk-card-info { flex: 1; }
.fk-card-name { font-size: 30rpx; font-weight: bold; color: var(--text-color); display: block; }
.fk-card-brief { font-size: 24rpx; color: var(--text-secondary); }
.fk-arrow { font-size: 36rpx; color: var(--text-muted); }
.fk-card-tags { display: flex; gap: 12rpx; margin-top: 16rpx; }
.fk-tag {
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 16rpx;
}
.fk-tag-title {
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 26rpx;
  font-weight: bold;
  padding: 10rpx 20rpx;
  border-radius: 10rpx;
  display: inline-block;
  margin-bottom: 16rpx;
}
.fk-card-content {
  font-size: 26rpx;
  color: var(--text-muted);
  line-height: 1.7;
  margin-top: 16rpx;
  display: block;
}
</style>
