# Qwen图片编辑浏览器插件

基于魔搭社区(ModelScope)API的Chrome浏览器图片编辑插件,支持右键菜单快速编辑和侧边栏自定义编辑。

## 功能特性

### 功能1: 右键菜单快速编辑
- 在网页图片上右键点击,选择"使用Qwen编辑图片"
- 自动在侧边栏打开编辑界面
- 自动获取原图尺寸,使用原始分辨率进行编辑
- 输入编辑提示词后即可调用API生成图片
- 默认使用 `Qwen/Qwen-Image-Edit-2511` 模型

### 功能2: 侧边栏自定义编辑
- 点击插件图标打开侧边栏
- 支持多图输入(最多6张)
- 可自定义以下参数:
  - **模型选择**: 默认Qwen-Image-Edit-2511,支持自定义模型ID
  - **分辨率**: 支持预设和自定义
    - SD系列: 64x64 ~ 2048x2048
    - FLUX: 64x64 ~ 1024x1024
    - Qwen-Image: 64x64 ~ 1664x1664
  - **正向提示词**: 描述想要生成的内容
  - **负向提示词**: 描述不希望出现的内容
  - **采样步数**: 1-100,默认30
  - **引导系数**: 1.5-20,默认3.5
  - **随机种子**: 可选,留空为随机

### API Token配置
支持两种方式设置ModelScope Token:
1. **环境变量**: 设置 `MODELSCOPE_SDK_TOKEN` 环境变量(需要重启浏览器)
2. **手动设置**: 在侧边栏设置中手动输入Token

## 安装方法

1. 下载或克隆本仓库
2. 打开Chrome浏览器,访问 `chrome://extensions/`
3. 开启右上角的"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择 `extension_qwen_edit` 文件夹

## 获取ModelScope Token

1. 访问 [魔搭社区](https://modelscope.cn/)
2. 登录账号
3. 访问 [Token获取页面](https://modelscope.cn/my/myaccesstoken)
4. 复制您的专属Token
5. 在插件设置中粘贴Token

## 使用方法

### 快速编辑模式
1. 在任意网页图片上右键点击
2. 选择"使用Qwen编辑图片"
3. 侧边栏自动打开,显示原图
4. 输入编辑提示词(例如:"给图中的狗戴上一个生日帽")
5. 点击"开始编辑"按钮
6. 等待生成完成(通常需要30秒到几分钟)
7. 点击生成的图片可查看大图

### 自定义编辑模式
1. 点击浏览器工具栏的插件图标
2. 侧边栏打开,默认显示"自定义编辑"区域
3. 输入图片URL(支持多图)
4. 设置分辨率、提示词等参数
5. 点击"生成图片"按钮
6. 等待生成完成

### 设置参数
1. 点击侧边栏右上角的设置图标(⚙️)
2. 配置以下参数:
   - **ModelScope Token**: 必填,从魔搭社区获取
   - **默认模型**: 选择或输入自定义模型ID
   - **默认分辨率**: 设置宽度和高度
3. 点击"保存设置"

## API调用说明

插件基于魔搭社区的异步图片生成API,调用流程:

1. 提交生成任务到 `/v1/images/generations`
2. 获取任务ID (task_id)
3. 轮询任务状态 `/v1/tasks/{task_id}`
4. 任务完成后返回生成的图片URL

详细API文档请参考: [modelscope-魔搭API.md](./modelscope-魔搭API.md)

## 技术架构

### 文件结构
```
extension_qwen_edit/
├── manifest.json          # 插件配置文件
├── sidebar.html           # 侧边栏HTML
├── styles/
│   └── sidebar.css        # 侧边栏样式
├── scripts/
│   ├── background.js      # 后台服务(右键菜单、消息传递)
│   ├── content.js         # 内容脚本(捕获图片信息)
│   ├── api.js            # API调用模块
│   └── sidebar.js        # 侧边栏逻辑
├── icons/                 # 插件图标
├── edit.py               # Python API调用示例
└── README.md             # 说明文档
```

### 核心技术
- **Manifest V3**: 最新的Chrome扩展标准
- **Side Panel API**: Chrome侧边栏功能
- **Context Menus API**: 右键菜单
- **Storage API**: 本地存储配置
- **Fetch API**: HTTP请求

## 注意事项

1. **API限制**: 魔搭社区API可能有调用频率限制,请合理使用
2. **Token安全**: 请勿泄露您的Token,它具有账号权限
3. **图片URL**: 输入的图片URL必须公网可访问
4. **生成时间**: 图片生成需要30秒到几分钟不等,请耐心等待
5. **分辨率限制**: 不同模型支持的分辨率范围不同,请查看说明

## 常见问题

### Q: 提示"请先设置ModelScope Token"?
A: 请在设置中输入从魔搭社区获取的Token。

### Q: 生成失败怎么办?
A: 可能的原因:
- Token无效或过期
- 图片URL无法访问
- 参数超出模型支持范围
- 网络连接问题

### Q: 如何查看生成进度?
A: 生成过程中会显示进度条和任务状态,您也可以到魔搭社区后台查看。

### Q: 生成的图片如何保存?
A: 点击生成的图片会在新标签页打开,右键保存即可。也支持批量下载。

## 更新日志

### v2.0.0 (2024-12-24)
- 重构为侧边栏插件
- 添加右键菜单快速编辑功能
- 支持多图输入和自定义参数
- 改进UI和交互体验
- 添加环境变量Token支持

## 开发说明

如需修改或二次开发,请注意:
1. 修改API端点请编辑 `scripts/api.js`
2. 修改UI请编辑 `sidebar.html` 和 `styles/sidebar.css`
3. 修改功能逻辑请编辑 `scripts/sidebar.js`
4. 修改权限请编辑 `manifest.json`

## 许可证

本项目仅供学习和个人使用。

## 相关链接

- [魔搭社区](https://modelscope.cn/)
- [Qwen模型](https://modelscope.cn/models?name=qwen)
- [Chrome扩展开发文档](https://developer.chrome.com/docs/extensions/)
