# Token设置优化更新 (v2.1)

## 更新日期
2024-12-24

## 主要变更

### 移除环境变量支持
- ❌ 移除了 `MODELSCOPE_SDK_TOKEN` 环境变量的读取逻辑
- ✅ 改为纯手动输入模式,简化了配置流程

### 新的Token输入界面

#### 1. 美观的输入框设计
- **样式**: 现代化的密码输入框,带边框高亮效果
- **字体**: 使用等宽字体 (Monaco/Courier New) 显示Token
- **颜色**: 浅灰背景,聚焦时变为白色并显示蓝色边框

#### 2. 可见性切换按钮
- **位置**: 输入框右侧
- **图标**: 👁️ (显示) / 🙈 (隐藏)
- **功能**: 点击可切换Token的显示/隐藏状态

#### 3. 实时验证反馈
输入框下方显示Token状态:

**未设置** (黄色)
```
⚠️ 未设置Token
```

**已设置** (绿色)
```
✅ Token已设置
```

**格式错误** (红色)
```
❌ Token格式不正确(太短)
```

### 功能特性

1. **自动验证**: 输入时实时检查Token长度
2. **保存验证**: 点击保存时验证Token是否为空和格式
3. **状态持久化**: Token保存在Chrome存储中,下次打开自动加载
4. **友好提示**: 显示获取Token的链接

### 代码改进

#### sidebar.html
```html
<!-- 新的Token输入结构 -->
<div class="token-input-wrapper">
  <input type="password" id="apiToken" class="token-input" placeholder="请输入你的ModelScope Token" />
  <button id="toggleTokenVisibility" class="visibility-toggle" type="button">
    <span class="eye-icon">👁️</span>
  </button>
</div>
<div class="token-status" id="tokenStatus">
  <span class="status-icon">⚠️</span>
  <span class="status-text">未设置Token</span>
</div>
```

#### sidebar.js
- 新增 `toggleTokenVisibility()`: 切换Token显示/隐藏
- 新增 `validateToken()`: 实时验证Token格式
- 优化 `loadSettings()`: 加载并验证Token
- 优化 `saveSettings()`: 保存前验证Token
- 优化 `resetSettings()`: 重置Token状态

#### background.js
- 移除 `getEnvToken` 消息处理
- 简化 `getApiKey` 逻辑,只从storage读取

### 用户使用流程

1. 打开插件设置
2. 在 "ModelScope Token" 输入框中粘贴Token
3. 点击右侧 👁️ 图标可查看Token
4. 确认下方显示 "✅ Token已设置"
5. 点击 "保存设置"
6. Token将保存在浏览器本地,无需重复输入

### 获取Token

访问: https://modelscope.cn/my/myaccesstoken

### 技术细节

- **输入类型**: `password` (默认隐藏)
- **最小长度**: 20字符
- **存储位置**: `chrome.storage.local`
- **存储键**: `modelScopeToken`
- **验证规则**: 非空且长度≥20

### 兼容性

- ✅ Chrome 88+
- ✅ Edge 88+
- ✅ 其他基于Chromium的浏览器

### 后续计划

- [ ] 添加Token格式强度检测
- [ ] 支持多个Token切换
- [ ] 添加Token过期提醒
- [ ] 一键复制Token功能
