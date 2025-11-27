"""
配置加载器
用于加载和管理插件配置
"""

import os
import json
import logging

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_file=None):
        """
        初始化配置加载器
        Args:
            config_file: 配置文件路径，默认为插件目录下的config.json
        """
        if config_file is None:
            self.config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
        else:
            self.config_file = config_file
            
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logging.info(f"[ModelScope] 配置文件加载成功: {self.config_file}")
                    return config
            else:
                logging.warning(f"[ModelScope] 配置文件不存在: {self.config_file}")
                return self.create_default_config()
        except Exception as e:
            logging.error(f"[ModelScope] 加载配置文件失败: {e}")
            return self.get_default_config()
            
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logging.info(f"[ModelScope] 配置文件保存成功: {self.config_file}")
            return True
        except Exception as e:
            logging.error(f"[ModelScope] 保存配置文件失败: {e}")
            return False
            
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        
    def create_default_config(self, save=True):
        """创建默认配置文件"""
        default_config = self.get_default_config()
        
        if save:
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                logging.info(f"[ModelScope] 默认配置文件创建成功: {self.config_file}")
            except Exception as e:
                logging.error(f"[ModelScope] 创建默认配置文件失败: {e}")
                
        return default_config
        
    def get_default_config(self):
        """获取默认配置"""
        return {
            "api_key": "",
            "model_scope_cookie": "",
            "default_width": 928,
            "default_height": 1664,
            "max_width": 2048,
            "max_height": 2048
        }
        
    @staticmethod
    def load_json_file(file_path, default_value=None):
        """加载JSON文件"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    # 记录成功加载的文件
                    file_name = os.path.basename(file_path)
                    logging.info(f"[ModelScope] 配置文件加载成功: {file_path}")
                    return content
            else:
                logging.warning(f"[ModelScope] 文件不存在: {file_path}")
                return default_value if default_value is not None else []
        except Exception as e:
            logging.error(f"[ModelScope] 加载文件失败: {e}")
            return default_value if default_value is not None else []