"""
ComfyUI ModelScope Plugin
提供基于ModelScope API的图像生成节点
"""

from .image import ModelScopeImageNode
from .checkpoint import CheckpointNode
from .lora import LoraNode
from .config_loader import ConfigLoader
import os
import folder_paths

try:
    import comfy.utils
    import comfy.model_management
    import comfy.samplers
    import comfy.sd
    import comfy.model_base
except ImportError:
    pass

NODE_CLASS_MAPPINGS = {
    "ModelScopeImageNode": ModelScopeImageNode,
    "CheckpointNode": CheckpointNode,
    "LoraNode": LoraNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ModelScopeImageNode": "ModelScope 图像生成",
    "CheckpointNode": "ModelScope Checkpoint",
    "LoraNode": "ModelScope LoRA"
}

# 确保配置文件存在
plugin_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(plugin_dir, "config.json")

if not os.path.exists(config_path):
    from .config_loader import ConfigLoader
    ConfigLoader.create_default_config()

WEB_DIRECTORY = "./js"

print(f"[ModelScope] Plugin loaded from {plugin_dir}")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']