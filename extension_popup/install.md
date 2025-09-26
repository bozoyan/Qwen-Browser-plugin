# 浏览器插件安装指南

## 快速安装步骤

### 1. 准备图标文件

插件需要PNG格式的图标文件。请按以下步骤创建：

1. 访问 https://convertio.co/svg-png/ 或其他SVG转PNG工具
2. 上传 `extension/icons/icon.svg` 文件
3. 分别转换为以下尺寸并保存到 `extension/icons/` 目录：
   - `icon16.png` (16x16像素)
   - `icon48.png` (48x48像素)
   - `icon128.png` (128x128像素)

### 2. 启动后端服务

```bash
# 在项目根目录执行
python web_app.py
```

确保看到类似输出：
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:8005
* Running on http://[::1]:8005
```

### 3. 安装Chrome插件

1. 打开Chrome浏览器
2. 在地址栏输入：`chrome://extensions/`
3. 开启右上角的"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择项目中的 `extension` 文件夹
6. 插件安装成功后会显示在扩展列表中

### 4. 配置插件

1. 点击Chrome工具栏中的插件图标
2. 点击设置按钮（⚙️）
3. 填入必要配置：
   - **OpenAI API Key**: 用于图片分析
   - **ModelScope Cookie**: 用于图片生成
   - **图片尺寸**: 根据需要调整

### 5. 测试功能

1. 打开 `extension/test.html` 进行功能测试
2. 或直接在插件中上传图片测试

## 故障排除

### 插件无法加载
- 确保 `extension/icons/` 目录下有所需的PNG图标文件
- 检查 `manifest.json` 文件格式是否正确

### 无法连接后端服务
- 确保 `python web_app.py` 正在运行
- 检查端口8005是否被占用
- 尝试访问 http://localhost:8005/health 测试连接

### API调用失败
- 检查OpenAI API Key是否有效
- 确认ModelScope Cookie是否正确
- 查看浏览器开发者工具的Console和Network标签

## 开发调试

### 查看插件日志
1. 右键点击插件图标
2. 选择"检查弹出内容"
3. 在开发者工具中查看Console日志

### 重新加载插件
1. 访问 `chrome://extensions/`
2. 找到插件，点击刷新按钮
3. 或者先移除再重新加载

### 测试页面
打开 `extension/test.html` 可以：
- 检查插件状态
- 测试后端连接
- 查看调试信息
- 使用测试图片

## 文件清单

确保以下文件存在且完整：

```
extension/
├── manifest.json          ✅ 插件配置
├── popup.html            ✅ 弹窗页面
├── scripts/              
│   ├── config.js         ✅ 配置文件
│   ├── utils.js          ✅ 工具函数
│   ├── ui.js             ✅ UI管理
│   ├── api.js            ✅ API管理
│   └── popup.js          ✅ 主入口
├── styles/
│   └── popup.css         ✅ 样式文件
├── icons/
│   ├── icon.svg          ✅ SVG图标
│   ├── icon16.png        ❌ 需要创建
│   ├── icon48.png        ❌ 需要创建
│   └── icon128.png       ❌ 需要创建
├── test.html             ✅ 测试页面
├── install.md            ✅ 安装指南
└── README.md             ✅ 使用说明
```

## 注意事项

1. **Chrome版本**: 需要Chrome 88+支持Manifest V3
2. **网络权限**: 插件需要访问OpenAI和ModelScope API
3. **本地服务**: 必须先启动Python后端服务
4. **API配额**: 注意OpenAI API的使用限制和费用

安装完成后，插件就可以正常使用了！