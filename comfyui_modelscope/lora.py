"""
ModelScope LoRA节点
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from .config_loader import ConfigLoader

class LoraNode:
    """ModelScope LoRA节点"""
    
    CATEGORY = "🇨🇳BOZO/PIC"
    
    @classmethod
    def INPUT_TYPES(cls):
        # 加载LoRA列表
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        lora_file = os.path.join(plugin_dir, "loraArgs.json")
        loras = ConfigLoader.load_json_file(lora_file, [])
        
        # 创建选项列表
        lora_names = []
        for lora in loras:
            lora_names.append(f"{lora['LoraName']} (ID: {lora['modelVersionId']}, Scale: {lora['scale']})")
            
        return {
            "required": {
                "lora": (lora_names, {"default": lora_names[0] if lora_names else ""}),
                "custom_id": ("STRING", {"default": ""}),
                "custom_name": ("STRING", {"default": ""}),
                "custom_scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}),
                "use_custom": ("BOOLEAN", {"default": False}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}),
            }
        }
    
    RETURN_TYPES = ("LORA",)
    RETURN_NAMES = ("lora",)
    
    FUNCTION = "get_lora"
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        
    def get_lora(self, lora, custom_id, custom_name, custom_scale, use_custom, scale):
        """
        获取LoRA配置
        Args:
            lora: 从下拉菜单选择的LoRA
            custom_id: 自定义LoRA ID
            custom_name: 自定义LoRA名称
            custom_scale: 自定义LoRA权重
            use_custom: 是否使用自定义LoRA
            scale: LoRA权重
        Returns:
            dict: LoRA配置
        """
        if use_custom:
            if not custom_id:
                logging.warning("[ModelScope] 使用自定义LoRA但未提供ID，使用默认LoRA")
                use_custom = False
            else:
                # 使用自定义LoRA
                try:
                    lora_id = int(custom_id)
                    lora_name = custom_name if custom_name else f"Custom_{lora_id}"
                    
                    logging.info(f"[ModelScope] 使用自定义LoRA: {lora_name} (ID: {lora_id}, Scale: {custom_scale})")
                    
                    return ({
                        "modelVersionId": lora_id,
                        "scale": custom_scale
                    },)
                except ValueError:
                    logging.error(f"[ModelScope] 无效的LoRA ID: {custom_id}")
                    use_custom = False
        
        if not use_custom:
            # 从下拉菜单选择的LoRA
            plugin_dir = os.path.dirname(os.path.realpath(__file__))
            lora_file = os.path.join(plugin_dir, "loraArgs.json")
            loras = ConfigLoader.load_json_file(lora_file, [])
            
            # 查找选中的LoRA
            selected_lora = None
            for l in loras:
                l_display_name = f"{l['LoraName']} (ID: {l['modelVersionId']}, Scale: {l['scale']})"
                if l_display_name == lora:
                    selected_lora = l
                    break
                    
            if not selected_lora:
                # 如果找不到选中的LoRA，使用第一个
                if loras:
                    selected_lora = loras[0]
                    logging.warning(f"[ModelScope] 无法找到选中的LoRA，使用默认: {selected_lora['LoraName']}")
                else:
                    logging.error("[ModelScope] 没有可用的LoRA")
                    return ({},)
                    
            # 使用用户提供的scale值覆盖默认值
            selected_lora["scale"] = scale
                    
            logging.info(f"[ModelScope] 使用LoRA: {selected_lora['LoraName']} (ID: {selected_lora['modelVersionId']}, Scale: {selected_lora['scale']})")
            
            return ({
                "modelVersionId": selected_lora["modelVersionId"],
                "scale": selected_lora["scale"]
            },)