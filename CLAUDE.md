# CLAUDE.md

该文件为使用 Claude Code（claude.ai/code）在本仓库中的代码工作提供了指导。

## 项目概述

这是一个基于Qwen3-VL-235B-A22B-Instruct模型的图像反推与生成工具，包含浏览器扩展和Flask后端。用户可以右键点击网页图像，系统会自动生成图像描述，然后使用该描述创建四张新的AI生成图像。

## 核心架构

### 后端 (Python Flask)
- **web_app.py**: Flask应用主入口，配置CORS、静态文件服务和端口(8005)
- **routes.py**: API路由定义，包含上传、分析、生成等核心端点
- **image_analyzer.py**: 图像分析核心逻辑，调用Qwen3-VL API进行图像反推
- **config.py**: 配置文件，包含API密钥、Cookie、LoRA模型参数等敏感信息
- **task_poller.py**: 轮询任务状态处理
- **utils.py**: 工具函数，包含文件验证、CSRF令牌提取等

### 前端 (Chrome Extension)
项目包含两个版本：
- **extension/**: 原始缩略图版本 (manifest v3)
- **extension_popup/**: 大图显示弹窗版本

每个扩展都包含：
- manifest.json: 扩展配置
- scripts/background.js: 后台服务，处理上下文菜单创建
- scripts/content.js: 内容脚本，注入模态窗口和处理API调用
- scripts/popup.js: 弹窗UI逻辑

## 开发命令

### 安装依赖
```bash
pip install -r requirements.txt
# 使用国内镜像加速安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 启动后端服务器
```bash
python web_app.py
```
服务器将在 `http://127.0.0.1:8005` 启动

### 加载浏览器扩展
1. 打开Chrome浏览器
2. 导航到 `chrome://extensions`
3. 启用"开发者模式"
4. 点击"加载已解压的扩展程序"，选择对应的文件夹

## 配置说明

### 关键配置文件 (config.py)
- **OPENAI_API_KEY**: ModelScope API密钥
- **MODEL_SCOPE_COOKIE**: ModelScope网站Cookie
- **LORA_ARGS**: LoRA模型配置和缩放参数
- **DEFAULT_WIDTH/HEIGHT**: 图像生成默认尺寸

### 模型配置
项目支持多个预定义模型：
- GUA V1-V9 系列
- Q_FEI_ckpt-12, Q_FEIFEI_ckpt-10
- Qwen-image 精细细节模型

## 技术特点

### 图像处理流程
1. 用户右键点击图像触发扩展
2. 扩展捕获图像并上传到Flask后端
3. `image_analyzer.py` 使用Qwen3-VL API分析图像
4. 生成300字以内的描述性提示词
5. 使用ModelScope API生成四张新图像

### 关键依赖
- Flask>=2.0.0, Flask-Cors>=3.0.0
- openai>=1.0.0 (用于Qwen3-VL API调用)
- requests>=2.25.1, Werkzeug>=2.0.0
- pillow (图像处理)

### 文件上传限制
- 最大文件大小: 16MB
- 支持格式: webp, png, jpg, jpeg, gif, bmp

## 注意事项

### 安全配置
- config.py包含敏感信息，切勿提交到版本控制
- 使用固定的CORS允许所有来源，生产环境应限制特定域名
- 文件上传需要验证文件类型和大小

### API调用
- Qwen3-VL API使用ModelScope端点
- 图像生成使用ModelScope的推理服务
- 需要有效的API密钥和Cookie才能正常工作

### 错误处理
- 图像分析失败时检查原始图像是否损坏
- API超时时可以到ModelScope图片库查看生成结果
- 参考README中的错误排查部分

## 扩展开发

### 修改上下文菜单
编辑 `extension/scripts/background.js` 中的`chrome.contextMenus.create`配置

### 自定义模态窗口UI
修改 `extension/scripts/content.js` 中的DOM创建逻辑

### API端点扩展
在`routes.py`中添加新的蓝图路由，前端通过`extension/scripts/api.js`调用