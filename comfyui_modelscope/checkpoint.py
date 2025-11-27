"""
ModelScope Checkpoint节点
"""

import os
import logging

from .config_loader import ConfigLoader

class CheckpointNode:
    """ModelScope Checkpoint节点"""
    
    CATEGORY = "🇨🇳BOZO/PIC"
    
    @classmethod
    def INPUT_TYPES(cls):
        # 加载checkpoint列表
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        checkpoint_file = os.path.join(plugin_dir, "checkpoint.json")
        checkpoints = ConfigLoader.load_json_file(checkpoint_file, [])
        
        # 创建选项列表
        checkpoint_names = []
        for cp in checkpoints:
            checkpoint_names.append(f"{cp['CheckpointName']} (ID: {cp['checkpointModelVersionId']})")
            
        return {
            "required": {
                "checkpoint": (checkpoint_names, {"default": checkpoint_names[0] if checkpoint_names else ""}),
                "custom_id": ("STRING", {"default": ""}),
                "custom_name": ("STRING", {"default": ""}),
                "custom_steps": ("INT", {"default": 50, "min": 1, "max": 100, "step": 1}),
                "custom_scale": ("FLOAT", {"default": 4.0, "min": 1.0, "max": 20.0, "step": 0.5}),
                "use_custom": ("BOOLEAN", {"default": False}),
                "use_custom_params": ("BOOLEAN", {"default": False}),
                "save_to_config": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("CHECKPOINT",)
    RETURN_NAMES = ("checkpoint",)
    
    FUNCTION = "get_checkpoint"
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        
    def get_checkpoint(self, checkpoint, custom_id, custom_name, custom_steps, custom_scale, use_custom, use_custom_params, save_to_config):
        """
        获取checkpoint配置
        Args:
            checkpoint: 从下拉菜单选择的checkpoint
            custom_id: 自定义checkpoint ID
            custom_name: 自定义checkpoint名称
            custom_steps: 自定义推理步数
            custom_scale: 自定义引导比例
            use_custom: 是否使用自定义checkpoint
            use_custom_params: 是否使用自定义参数
            save_to_config: 是否保存到配置文件
        Returns:
            dict: checkpoint配置
        """
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        checkpoint_file = os.path.join(plugin_dir, "checkpoint.json")
        
        # 如果是自定义checkpoint
        if use_custom:
            if not custom_id:
                logging.warning("[ModelScope] 使用自定义checkpoint但未提供ID，使用默认checkpoint")
                use_custom = False
            else:
                # 使用自定义checkpoint
                try:
                    checkpoint_id = int(custom_id)
                    checkpoint_name = custom_name if custom_name else f"Custom_{checkpoint_id}"
                    
                    logging.info(f"[ModelScope] 使用自定义checkpoint: {checkpoint_name} (ID: {checkpoint_id})")
                    
                    result = {
                        "modelVersionId": checkpoint_id,
                        "checkpointShowInfo": checkpoint_name,
                        "numInferenceSteps": custom_steps if use_custom_params else 50,
                        "guidanceScale": custom_scale if use_custom_params else 4.0
                    }
                    
                    # 如果需要保存到配置文件
                    if save_to_config:
                        self.save_custom_checkpoint(checkpoint_id, checkpoint_name, custom_steps, custom_scale, use_custom_params)
                    
                    return (result,)
                except ValueError:
                    logging.error(f"[ModelScope] 无效的checkpoint ID: {custom_id}")
                    use_custom = False
        
        # 从下拉菜单选择的checkpoint
        checkpoints = ConfigLoader.load_json_file(checkpoint_file, [])
        
        # 查找选中的checkpoint
        selected_checkpoint = None
        for cp in checkpoints:
            cp_display_name = f"{cp['CheckpointName']} (ID: {cp['checkpointModelVersionId']})"
            if cp_display_name == checkpoint:
                selected_checkpoint = cp
                break
                
        if not selected_checkpoint:
            # 如果找不到选中的checkpoint，使用第一个
            if checkpoints:
                selected_checkpoint = checkpoints[0]
                logging.warning(f"[ModelScope] 无法找到选中的checkpoint，使用默认: {selected_checkpoint['checkpointShowInfo']}")
            else:
                logging.error("[ModelScope] 没有可用的checkpoint")
                return ({},)
        
        # 确定使用的参数
        num_inference_steps = custom_steps if use_custom_params else selected_checkpoint.get("numInferenceSteps", 50)
        guidance_scale = custom_scale if use_custom_params else selected_checkpoint.get("guidanceScale", 4.0)
        
        # 如果使用了自定义参数且需要保存
        if use_custom_params and save_to_config:
            self.update_checkpoint_params(selected_checkpoint, num_inference_steps, guidance_scale)
                
        logging.info(f"[ModelScope] 使用checkpoint: {selected_checkpoint['checkpointShowInfo']} (ID: {selected_checkpoint['checkpointModelVersionId']})")
        logging.info(f"[ModelScope] 参数: steps={num_inference_steps}, scale={guidance_scale}")
        
        return ({
            "modelVersionId": selected_checkpoint["checkpointModelVersionId"],
            "checkpointShowInfo": selected_checkpoint["checkpointShowInfo"],
            "numInferenceSteps": num_inference_steps,
            "guidanceScale": guidance_scale
        },)
    
    def save_custom_checkpoint(self, checkpoint_id, checkpoint_name, steps, scale, use_custom_params):
        """保存自定义checkpoint到配置文件"""
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        checkpoint_file = os.path.join(plugin_dir, "checkpoint.json")
        checkpoints = ConfigLoader.load_json_file(checkpoint_file, [])
        
        # 检查是否已存在
        for cp in checkpoints:
            if cp["checkpointModelVersionId"] == checkpoint_id:
                # 更新现有checkpoint
                cp["CheckpointName"] = checkpoint_name
                if use_custom_params:
                    cp["numInferenceSteps"] = steps
                    cp["guidanceScale"] = scale
                break
        else:
            # 添加新checkpoint
            new_checkpoint = {
                "CheckpointName": checkpoint_name,
                "checkpointModelVersionId": checkpoint_id,
                "checkpointShowInfo": f"{checkpoint_name}.safetensors",
                "numInferenceSteps": steps if use_custom_params else 50,
                "guidanceScale": scale if use_custom_params else 4.0
            }
            checkpoints.append(new_checkpoint)
        
        # 保存到文件
        try:
            import json
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoints, f, indent=4, ensure_ascii=False)
            logging.info(f"[ModelScope] 自定义checkpoint已保存到配置文件")
        except Exception as e:
            logging.error(f"[ModelScope] 保存checkpoint配置失败: {e}")
    
    def update_checkpoint_params(self, checkpoint, steps, scale):
        """更新现有checkpoint的参数"""
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        checkpoint_file = os.path.join(plugin_dir, "checkpoint.json")
        checkpoints = ConfigLoader.load_json_file(checkpoint_file, [])
        
        # 查找并更新
        for cp in checkpoints:
            if cp["checkpointModelVersionId"] == checkpoint["checkpointModelVersionId"]:
                cp["numInferenceSteps"] = steps
                cp["guidanceScale"] = scale
                break
        
        # 保存到文件
        try:
            import json
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoints, f, indent=4, ensure_ascii=False)
            logging.info(f"[ModelScope] Checkpoint参数已更新到配置文件")
        except Exception as e:
            logging.error(f"[ModelScope] 更新checkpoint参数失败: {e}")