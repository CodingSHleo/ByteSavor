<script setup>
import { onLaunch } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { useSettingsStore } from '@/store/settings'

onLaunch(async () => {
  const authStore = useAuthStore()
  await authStore.init()
  const settingsStore = useSettingsStore()
  await settingsStore.init()
  console.log('ByteSavor V3.3 启动完成')
})
</script>

<style lang="scss">
@import "uni.scss";

/* ================================================================
   ByteSavor V3.3 — Layered Cards · 卡片分层设计
   设计理念：空间分割 / 色彩节奏 / 多层次阴影 / 紧凑克制
   ================================================================ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;

  /* ======== Munch · 多彩食材色 ======== */
  --bg:            #FFFBF7;
  --bg-white:      #FFFFFF;
  --bg-card:       #FFFFFF;
  --bg-elevated:   #FFF8F2;

  --text:          #2C2416;
  --text-secondary:#7B6F62;
  --text-muted:    #B0A699;
  --text-placeholder:#CFC7BD;

  /* 食材色系 */
  --tomato:        #E74C3C;   /* 番茄红 — 蛋白质/肉类 */
  --avocado:       #34C759;   /* 清新薄荷绿 — 蔬菜/健康 */
  --cheese:        #F0A500;   /* 芝士黄 — 碳水/谷物 */
  --berry:         #8E5EA2;   /* 浆果紫 — 水果/AI */
  --ocean:         #4A90D9;   /* 海洋蓝 — 海鲜/信息 */
  --cream:         #FFF0E0;   /* 奶油底 — 卡片背景 */

  /* 主色(绿) */
  --teal:          var(--avocado);
  --teal-light:    #6EE08A;
  --teal-bg:       #EBFAF0;
  --teal-border:   #A3E8B8;

  /* 强调(芝士黄) */
  --amber:         var(--cheese);
  --amber-bg:      #FFF8E8;
  --amber-border:  #FCE4A8;

  /* 语义色 */
  --green:         var(--avocado);
  --green-bg:      #F0F6EC;
  --red:           var(--tomato);
  --red-bg:        #FDF0EC;
  --purple:        var(--berry);
  --purple-bg:     #F6F0F8;
  --blue:          var(--ocean);
  --blue-light:    #6BAEE8;
  --blue-bg:       #EDF4FB;
  --blue-border:   #B8D5F2;

  /* 兼容旧变量 */
  --primary:       var(--avocado);
  --primary-bg:    var(--teal-bg);
  --primary-border:var(--teal-border);
  --accent:        var(--avocado);
  --accent-bg:     var(--teal-bg);
  --accent-border: var(--teal-border);
  --orange:        var(--cheese);
  --orange-bg:     var(--amber-bg);
  --success:       var(--avocado);
  --success-bg:    var(--green-bg);
  --danger:        var(--tomato);
  --danger-bg:     var(--red-bg);

  /* ======== 边框 ======== */
  --border:        #E5E7EB;
  --border-light:  #F3F4F6;

  /* ======== 阴影 — iOS 风格柔和 ======== */
  --shadow-sm:     0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:     0 2px 8px rgba(0,0,0,0.06);
  --shadow-lg:     0 4px 16px rgba(0,0,0,0.08);
  --shadow-xl:     0 2px 8px rgba(0,0,0,0.10);

  /* ======== 圆角 24px ======== */
  --radius-sm:   12rpx;
  --radius:      24rpx;
  --radius-md:   24rpx;
  --radius-lg:   24rpx;
  --radius-xl:   24rpx;
  --radius-full: 999rpx;

  /* ======== 动画 ======== */
  --ease:     cubic-bezier(0.25, 0.1, 0.25, 1);
  --fast:     150ms;
  --normal:   250ms;
  --slow:     350ms;

  /* ======== 旧变量兼容 ======== */
  --bg-color:       var(--bg);
  --card-bg:        var(--bg-card);
  --card-shadow:    var(--shadow-md);
  --card-hover-shadow:var(--shadow-lg);
  --card-hover:     var(--shadow-lg);
  --text-color:     var(--text);
  --input-bg:       var(--bg);
  --input-border:   var(--border);
  --border-color:   var(--border);
  --border-light-var:var(--border-light);
  --tag-bg:         var(--blue-bg);
  --tag-border:     var(--primary-border);
  --tag-text:       var(--blue);
  --font-serif:     var(--font);
  --transition-fast:var(--fast);
  --success:        var(--green);
  --success-bg:     var(--green-bg);
  --danger:         var(--red);
  --danger-bg:      var(--red-bg);
  --info-bg:        var(--blue-bg);
  --info-border:    var(--primary-border);
}

/* ================================================================
   页面基础
   ================================================================ */
* { box-sizing: border-box; }

/* ======== 手机端框架 ======== */
html, body {
  background: #E8E9EE;
  margin: 0; padding: 0;
  display: flex; justify-content: center;
}
#app {
  max-width: 430px;
  width: 100%;
  min-height: 100vh;
  background: var(--bg);
  position: relative;
  overflow-x: hidden;
  box-shadow: 0 0 40px rgba(0,0,0,0.10);
}

page {
  font-family: var(--font);
  font-size: 14px;
  color: var(--text);
  background-color: var(--bg);
  -webkit-font-smoothing: antialiased;
  letter-spacing: -0.01em;
  line-height: 1.5;
  overflow-x: hidden;
  max-width: 100vw;
}

/* ================================================================
   空间分割 — 不用线条，用留白和色块
   ================================================================ */
@keyframes fade-up {
  from { opacity: 0; transform: translateY(12rpx); }
  to   { opacity: 1; transform: translateY(0); }
}

.home-page, .explore-page, .profile-page, .settings-page,
.ir-page, .hd-page, .rd-page, .fk-page, .hist-page, .le-page,
.login-page, .register-page {
  animation: fade-up var(--slow) var(--ease) both;
  overflow-x: hidden;
  max-width: 100%;
}

/* ================================================================
   卡片系统 — 3级深度层次
   ================================================================ */
.card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-sm);
  transition: transform var(--normal) var(--ease),
              box-shadow var(--normal) var(--ease);
}
/* 毛玻璃变体 — 高级感 */
.card-glass {
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(10rpx);
  -webkit-backdrop-filter: blur(10rpx);
  border: 1px solid rgba(0,0,0,0.04);
}
/* 第二级 — 强调卡片 */
.card-elevated {
  box-shadow: var(--shadow-md);
}
/* 第三级 — 突出卡片 */
.card-prominent {
  box-shadow: var(--shadow-lg);
}

/* 卡片悬浮 */
.card:active,
.recipe-card:active,
.recipe-item:active,
.hist-card:active,
.menu-item:active,
.fk-card:active,
.le-item:active {
  transform: translateY(-2rpx);
  box-shadow: var(--shadow-lg) !important;
}

/* 卡片入场交错 */
.card, .recipe-card, .recipe-item, .hist-card,
.ir-ingredient-card, .le-item, .fk-card, .menu-item {
  animation: fade-up var(--normal) var(--ease) both;
}
.card:nth-child(1) { animation-delay: 0ms; }
.card:nth-child(2) { animation-delay: 40ms; }
.card:nth-child(3) { animation-delay: 80ms; }
.card:nth-child(4) { animation-delay: 120ms; }
.card:nth-child(n+5) { animation-delay: 160ms; }

/* ================================================================
   通用组件
   ================================================================ */
.section-title, .card-title {
  font-size: 32rpx;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 18rpx;
  display: block;
  letter-spacing: -0.02em;
}

button {
  font-family: var(--font);
  transition: all var(--normal) var(--ease);
}
button:active { transform: scale(0.97); }
button::after { border: none !important; }

input, textarea {
  font-family: var(--font);
  color: var(--text);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0 16rpx;
  font-size: 28rpx;
  transition: border-color var(--fast), box-shadow var(--fast);
}
input:focus, textarea:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(79,110,247,0.12);
  outline: none;
}

.btn-primary {
  background: var(--blue); color: #fff; border: none;
  border-radius: var(--radius); font-size: 30rpx; font-weight: 600;
  padding: 20rpx 0; width: 100%;
}
.btn-primary:active { background: var(--primary-dark); }
.btn-outline {
  background: transparent; color: var(--blue);
  border: 1.5px solid var(--primary-border);
  border-radius: var(--radius); font-size: 30rpx; font-weight: 600;
  padding: 20rpx 0; width: 100%;
}
.btn-danger {
  background: var(--red); color: #fff; border: none;
  border-radius: var(--radius); font-size: 30rpx; font-weight: 600;
  padding: 20rpx 0; width: 100%;
}

.error-banner {
  background: var(--red-bg); border: 1px solid var(--red);
  border-radius: var(--radius-sm); padding: 14rpx 18rpx;
  color: var(--red); font-size: 24rpx; margin-bottom: 16rpx;
}
.ai-tip {
  background: var(--purple-bg);
  border-radius: var(--radius-sm); padding: 14rpx 18rpx;
  color: var(--purple); font-size: 23rpx;
}

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ======== 底部导航栏 ======== */
.uni-tabbar, uni-tabbar {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -1px 8px rgba(0,0,0,0.04);
  border-top: 1px solid var(--border) !important;
}
/* 选中项微动效 */
.uni-tabbar .uni-tabbar__item.uni-tabbar__item--active {
  transition: transform var(--fast) ease;
}
.uni-tabbar .uni-tabbar__item.uni-tabbar__item--active .uni-tabbar__label {
  font-weight: 700;
}
</style>
