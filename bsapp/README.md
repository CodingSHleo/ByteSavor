# ByteSavor 前端

## 技术栈

- uni-app（Vue 3 + Vite 5）
- 纯 JavaScript，无 TypeScript
- 微信小程序 + H5 双端

## 跑起来

```bash
cd bsapp
npm install
npm run dev:h5        # H5 浏览器调试
npm run dev:mp-weixin # 微信小程序
```

## 目录结构

```
bsapp/src/
├── api/index.js      # 所有后端接口调用
├── pages/            # 页面
│   ├── home/         # 首页（食材、推荐、Agent输入）
│   ├── ingredient-recognition/  # 拍照识别
│   ├── recipe-detail/  # 菜谱详情
│   ├── explore/      # 探索发现
│   ├── register/     # 注册/登录
│   ├── profile/      # 个人中心
│   ├── health-dashboard/  # 健康看板
│   ├── history/      # 历史记录
│   ├── list-export/  # 购物清单导出
│   ├── settings/     # 设置
│   └── food-knowledge/  # 饮食知识
├── components/       # 公共组件
├── store/            # Pinia 状态管理
│   ├── auth.js       # 登录态
│   ├── history.js    # 历史记录
│   └── settings.js   # 用户设置
├── utils/i18n.js     # 中英文国际化
└── static/           # 图标/图片
```

## 后端对接

API 地址在 `src/api/index.js` 的 `BASE_URL`，改成你的后端地址。

## 拍照识别流程

1. 点拍照或选相册 → 浏览器原生 input 采集图片
2. 图片转 base64 → 发给后端 `/v1/sense/analyze`
3. 后端调 Qwen-VL 识别食材 → 返回食材列表
4. 用户确认食材 → 调 `/v1/decision/meal-plan` 推荐菜谱
