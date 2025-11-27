# ComfyUI ModelScope 插件

这是一个用于ComfyUI的插件，提供了通过ModelScope API生成图像的功能。

## 功能特点

- 通过ModelScope API生成高质量图像
- 支持自定义Checkpoint和LoRA模型
- 支持高清修复功能
- 可配置生成图像的数量和尺寸
- 提供详细的日志输出

## 安装方法

1. 将此插件文件夹复制到ComfyUI的`custom_nodes`目录中
2. 重启ComfyUI

## 节点说明

### ModelScope 图像生成 (ModelScopeImageNode)

主节点，用于生成图像。

**输入参数：**

- `prompt`: 图像提示词（必填）
- `width`: 图像宽度（默认：928，最大：2048）
- `height`: 图像高度（默认：1664，最大：2048）
- `num_images`: 生成图像数量（默认：4，范围：1-4）
- `enable_hires`: 是否启用高清修复（默认：True）
- `api_key`: API密钥
- `cookie`: ModelScope Cookie
- `checkpoint`: Checkpoint节点（可选）
- `lora1-4`: LoRA节点（最多4个，可选）

**输出：**

- `image_urls`: 生成的图像URL列表
- `images`: ComfyUI格式的图像张量
- `status_log`: 状态日志

### ModelScope Checkpoint (CheckpointNode)

Checkpoint选择节点，用于选择或自定义大模型。

**输入参数：**

- `checkpoint`: 从下拉菜单选择预定义的Checkpoint（格式：模型名称 (ID: 模型ID)）
- `custom_id`: 自定义Checkpoint ID
- `custom_name`: 自定义Checkpoint名称
- `use_custom`: 是否使用自定义Checkpoint

**输出：**

- `checkpoint`: Checkpoint配置

### ModelScope LoRA (LoraNode)

LoRA选择节点，用于选择或自定义LoRA模型。

**输入参数：**

- `lora`: 从下拉菜单选择预定义的LoRA
- `custom_id`: 自定义LoRA ID
- `custom_name`: 自定义LoRA名称
- `custom_scale`: 自定义LoRA权重
- `use_custom`: 是否使用自定义LoRA
- `scale`: LoRA权重

**输出：**

- `lora`: LoRA配置

## 配置方法

1. 在ComfyUI菜单中找到"ModelScope 配置"选项
2. 输入您的API Key和ModelScope Cookie
3. 点击"保存"按钮

或者直接编辑`config.json`文件：

```json
{
    "api_key": "您的API密钥",
    "model_scope_cookie": "您的ModelScope Cookie",
    "default_width": 928,
    "default_height": 1664,
    "max_width": 2048,
    "max_height": 2048
}
```

## 使用示例

1. 添加`ModelScope 图像生成`节点
2. 添加`ModelScope Checkpoint`节点并连接到图像生成节点
3. 添加`ModelScope LoRA`节点并连接到图像生成节点（可选）
4. 在提示词框中输入描述
5. 点击"Queue Prompt"开始生成图像

## 日志查看

所有操作日志都会在ComfyUI的终端中显示，包括：
- 提交任务信息
- 任务状态
- 图像生成结果
- 错误信息（如果有）

## 注意事项

- 图像尺寸不能超过2048x2048
- 需要有效的ModelScope Cookie才能使用API
- 生成的图像会自动下载并转换为ComfyUI格式
- 如果任务处理时间过长，可能会超时

## 文件说明

- `__init__.py`: 插件入口文件
- `config.json`: 配置文件
- `checkpoint.json`: Checkpoint模型列表
- `loraArgs.json`: LoRA模型列表
- `image.py`: 图像生成节点
- `checkpoint.py`: Checkpoint节点
- `lora.py`: LoRA节点
- `config_loader.py`: 配置加载器
- `js/modelscope.js`: 前端JavaScript文件
- `README.md`: 说明文档

## 问题反馈

如果遇到问题，请查看ComfyUI终端中的日志输出，或者提交Issue。