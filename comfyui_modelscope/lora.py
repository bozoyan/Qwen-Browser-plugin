"""
ModelScope LoRA节点
"""

import os
import logging

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
                "save_to_config": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("LORA",)
    RETURN_NAMES = ("lora",)
    
    FUNCTION = "get_lora"
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        
    def get_lora(self, lora, custom_id, custom_name, custom_scale, use_custom, scale, save_to_config):
        """
        获取LoRA配置
        Args:
            lora: 从下拉菜单选择的LoRA
            custom_id: 自定义LoRA ID
            custom_name: 自定义LoRA名称
            custom_scale: 自定义LoRA权重
            use_custom: 是否使用自定义LoRA
            scale: LoRA权重
            save_to_config: 是否保存到配置文件
        Returns:
            dict: LoRA配置
        """
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        lora_file = os.path.join(plugin_dir, "loraArgs.json")
        
        # 如果是自定义LoRA
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
                    
                    result = {
                        "modelVersionId": lora_id,
                        "scale": custom_scale
                    }
                    
                    # 如果需要保存到配置文件
                    if save_to_config:
                        self.save_custom_lora(lora_id, lora_name, custom_scale)
                    
                    return (result,)
                except ValueError:
                    logging.error(f"[ModelScope] 无效的LoRA ID: {custom_id}")
                    use_custom = False
        
        # 从下拉菜单选择的LoRA
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
        final_scale = scale
        # 如果scale与原始值不同且需要保存
        if scale != selected_lora.get("scale", 1.0) and save_to_config:
            self.update_lora_scale(selected_lora, scale)
        else:
            final_scale = selected_lora.get("scale", 1.0)
                    
        logging.info(f"[ModelScope] 使用LoRA: {selected_lora['LoraName']} (ID: {selected_lora['modelVersionId']}, Scale: {final_scale})")
        
        return ({
            "modelVersionId": selected_lora["modelVersionId"],
            "scale": final_scale
        },)
    
    def save_custom_lora(self, lora_id, lora_name, scale):
        """保存自定义LoRA到配置文件"""
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        lora_file = os.path.join(plugin_dir, "loraArgs.json")
        loras = ConfigLoader.load_json_file(lora_file, [])
        
        # 检查是否已存在
        for lora in loras:
            if lora["modelVersionId"] == lora_id:
                # 更新现有LoRA
                lora["LoraName"] = lora_name
                lora["scale"] = scale
                break
        else:
            # 添加新LoRA
            new_lora = {
                "LoraName": lora_name,
                "modelVersionId": lora_id,
                "scale": scale
            }
            loras.append(new_lora)
        
        # 保存到文件
        try:
            import json
            with open(lora_file, 'w', encoding='utf-8') as f:
                json.dump(loras, f, indent=4, ensure_ascii=False)
            logging.info(f"[ModelScope] 自定义LoRA已保存到配置文件")
        except Exception as e:
            logging.error(f"[ModelScope] 保存LoRA配置失败: {e}")
    
    def update_lora_scale(self, lora, scale):
        """更新现有LoRA的scale"""
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        lora_file = os.path.join(plugin_dir, "loraArgs.json")
        loras = ConfigLoader.load_json_file(lora_file, [])
        
        # 查找并更新
        for l in loras:
            if l["modelVersionId"] == lora["modelVersionId"]:
                l["scale"] = scale
                break
        
        # 保存到文件
        try:
            import json
            with open(lora_file, 'w', encoding='utf-8') as f:
                json.dump(loras, f, indent=4, ensure_ascii=False)
            logging.info(f"[ModelScope] LoRA参数已更新到配置文件")
        except Exception as e:
            logging.error(f"[ModelScope] 更新LoRA参数失败: {e}")