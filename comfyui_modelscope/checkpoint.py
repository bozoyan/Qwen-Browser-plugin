"""
ModelScope Checkpoint节点
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

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
            checkpoint_names.append(f"{cp['checkpointShowInfo']} (ID: {cp['checkpointModelVersionId']})")
            
        return {
            "required": {
                "checkpoint": (checkpoint_names, {"default": checkpoint_names[0] if checkpoint_names else ""}),
                "custom_id": ("STRING", {"default": ""}),
                "custom_name": ("STRING", {"default": ""}),
                "use_custom": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("CHECKPOINT",)
    RETURN_NAMES = ("checkpoint",)
    
    FUNCTION = "get_checkpoint"
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        
    def get_checkpoint(self, checkpoint, custom_id, custom_name, use_custom):
        """
        获取checkpoint配置
        Args:
            checkpoint: 从下拉菜单选择的checkpoint
            custom_id: 自定义checkpoint ID
            custom_name: 自定义checkpoint名称
            use_custom: 是否使用自定义checkpoint
        Returns:
            dict: checkpoint配置
        """
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
                    
                    return ({
                        "modelVersionId": checkpoint_id,
                        "checkpointShowInfo": checkpoint_name
                    },)
                except ValueError:
                    logging.error(f"[ModelScope] 无效的checkpoint ID: {custom_id}")
                    use_custom = False
        
        if not use_custom:
            # 从下拉菜单选择的checkpoint
            plugin_dir = os.path.dirname(os.path.realpath(__file__))
            checkpoint_file = os.path.join(plugin_dir, "checkpoint.json")
            checkpoints = ConfigLoader.load_json_file(checkpoint_file, [])
            
            # 查找选中的checkpoint
            selected_checkpoint = None
            for cp in checkpoints:
                cp_display_name = f"{cp['checkpointShowInfo']} (ID: {cp['checkpointModelVersionId']})"
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
                    
            logging.info(f"[ModelScope] 使用checkpoint: {selected_checkpoint['checkpointShowInfo']} (ID: {selected_checkpoint['checkpointModelVersionId']})")
            
            return ({
                "modelVersionId": selected_checkpoint["checkpointModelVersionId"],
                "checkpointShowInfo": selected_checkpoint["checkpointShowInfo"]
            },)