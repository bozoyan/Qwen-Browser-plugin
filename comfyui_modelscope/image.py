"""
ModelScope图像生成节点
"""

import os
import time
import requests
import logging
import re

try:
    import torch
    import numpy as np
    from PIL import Image
    import io
except ImportError:
    torch = None
    numpy = None
    Image = None
    io = None

from .config_loader import ConfigLoader

class ModelScopeImageNode:
    """ModelScope图像生成节点"""
    
    CATEGORY = "🇨🇳BOZO/PIC"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "a photo of a beautiful woman"}),
                "width": ("INT", {"default": 928, "min": 256, "max": 2048, "step": 64}),
                "height": ("INT", {"default": 1664, "min": 256, "max": 2048, "step": 64}),
                "num_images": ("INT", {"default": 4, "min": 1, "max": 4, "step": 1}),
                "enable_hires": ("BOOLEAN", {"default": True}),
                
                "cookie": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "checkpoint": ("CHECKPOINT",),
                "lora1": ("LORA",),
                "lora2": ("LORA",),
                "lora3": ("LORA",),
                "lora4": ("LORA",),
            }
        }
    
    RETURN_TYPES = ("STRING", "IMAGE", "STRING")
    RETURN_NAMES = ("image_urls", "images", "status_log")
    
    FUNCTION = "generate_images"
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        
    def generate_images(self, prompt, width, height, num_images, enable_hires, cookie, 
                       checkpoint=None, lora1=None, lora2=None, lora3=None, lora4=None):
        """
        生成图像
        Args:
            prompt: 提示词
            width: 图像宽度
            height: 图像高度
            num_images: 生成图像数量
            enable_hires: 是否启用高清修复
            cookie: ModelScope Cookie
            checkpoint: Checkpoint节点
            lora1-4: LoRA节点
        Returns:
            tuple: (图像URL列表, 图像张量, 状态日志)
        """
        # 验证参数
        if not prompt:
            empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
            return ("", empty_tensor, "错误: 提示词不能为空")
            
        if width > 2048 or height > 2048:
            empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
            return ("", empty_tensor, f"错误: 图像尺寸不能超过2048x2048，当前为{width}x{height}")
            
        # 使用传入的cookie或配置文件中的cookie
        model_scope_cookie = cookie if cookie else self.config_loader.get("model_scope_cookie", "")
        
        if not model_scope_cookie:
            empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
            return ("", empty_tensor, "错误: 未配置ModelScope Cookie")
            
        # 构建LoRA参数
        lora_args = []
        for lora in [lora1, lora2, lora3, lora4]:
            if lora:
                lora_args.append(lora)
                
        # 构建checkpoint参数
        checkpoint_args = {}
        if checkpoint:
            checkpoint_args = {
                "checkpointModelVersionId": checkpoint["modelVersionId"],
                "checkpointShowInfo": checkpoint["checkpointShowInfo"]
            }
        else:
            # 使用默认checkpoint
            plugin_dir = os.path.dirname(os.path.realpath(__file__))
            checkpoint_file = os.path.join(plugin_dir, "checkpoint.json")
            checkpoints = ConfigLoader.load_json_file(checkpoint_file, [])
            if checkpoints:
                checkpoint_args = {
                    "checkpointModelVersionId": checkpoints[0]["checkpointModelVersionId"],
                    "checkpointShowInfo": checkpoints[0]["checkpointShowInfo"]
                }
        
        # 构建请求参数
        request_data = {
            "taskType": "TXT_2_IMG",
            "predictType": "TXT_2_IMG",
            "modelArgs": {
                **checkpoint_args,
                "loraArgs": lora_args,
                "predictType": "TXT_2_IMG"
            },
            "promptArgs": {
                "prompt": f"feifei,a photo-realistic shoot from a portrait camera angle about a young woman,big boobs,妃妃,{prompt}",
                "negativePrompt": ""
            },
            "basicDiffusionArgs": {
                "sampler": "Euler",
                "guidanceScale": 4,
                "seed": -1,
                "numInferenceSteps": 50,
                "numImagesPerPrompt": num_images,
                "width": width,
                "height": height
            },
            "advanced": False,
            "addWaterMark": False,
            "adetailerArgsMap": {},
            "hiresFixFrontArgs": {
                "modelName": "Nomos 8k SCHATL 4x",
                "scale": 4
            } if enable_hires else {},
            "controlNetFullArgs": []
        }
        
        # 提取CSRF Token
        csrf_token = self.extract_csrf_token(model_scope_cookie)
        if not csrf_token:
            logging.warning("[ModelScope] 无法从Cookie中提取CSRF Token，可能影响请求")
            
        # 构建请求头
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/json",
            "Cookie": model_scope_cookie,
            "Origin": "https://www.modelscope.cn",
            "Referer": "https://www.modelscope.cn/aigc/imageGeneration",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        
        if csrf_token:
            headers["X-CSRF-TOKEN"] = csrf_token
            
        # 发送请求
        api_url = "https://www.modelscope.cn/api/v1/muse/predict/task/submit"
        
        try:
            logging.info(f"[ModelScope] 开始生成图像，提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            logging.info(f"[ModelScope] 图像尺寸: {width}x{height}, 数量: {num_images}, 高清修复: {enable_hires}")
            
            response = requests.post(api_url, json=request_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 打印完整响应以便调试
            logging.info(f"[ModelScope] API响应: {result}")
            
            if not result.get("Success"):
                error_msg = result.get("Message", "未知错误")
                logging.error(f"[ModelScope] 提交任务失败: {error_msg}")
                return ("", None, f"提交任务失败: {error_msg}")
                
            # 检查响应数据结构
            if "Data" not in result:
                logging.error(f"[ModelScope] API响应格式不正确: {result}")
                empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
                return ("", empty_tensor, "API响应格式不正确")
                
            # 检查taskId位置
            task_id = None
            if "taskId" in result["Data"]:
                task_id = result["Data"]["taskId"]
            elif "data" in result["Data"] and "taskId" in result["Data"]["data"]:
                task_id = result["Data"]["data"]["taskId"]
            else:
                logging.error(f"[ModelScope] 无法从API响应中获取taskId: {result}")
                empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
                return ("", empty_tensor, "无法从API响应中获取taskId")
                
            logging.info(f"[ModelScope] 任务提交成功，任务ID: {task_id}")
            
            # 轮询任务状态，先等待几秒让任务开始处理
            logging.info("[ModelScope] 等待任务开始处理...")
            time.sleep(5)  # 初始等待5秒
            urls, status = self.poll_task_status(task_id, headers)
            
            if not urls:
                # 创建一个空的张量，避免ComfyUI报错
                empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
                return ("", empty_tensor, f"图像生成失败: {status}")
                
            # 下载图像并转换为ComfyUI格式
            images = []
            image_urls = []
            
            for url in urls:
                try:
                    img_response = requests.get(url, timeout=30)
                    img_response.raise_for_status()
                    
                    # 将图像转换为PIL对象
                    img = Image.open(io.BytesIO(img_response.content))
                    
                    # 转换为numpy数组
                    img_array = np.array(img).astype(np.float32) / 255.0
                    img_array = img_array[:, :, :3]  # 确保只有RGB通道
                    
                    # 转换为PyTorch张量
                    img_tensor = torch.from_numpy(img_array)[None,]
                    images.append(img_tensor)
                    image_urls.append(url)
                    
                except Exception as e:
                    logging.error(f"[ModelScope] 下载或处理图像失败: {e}")
                    continue
                    
            if not images:
                # 创建一个空的张量，避免ComfyUI报错
                empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
                return ("", empty_tensor, "所有图像下载或处理失败")
                
            # 合并所有图像
            combined_images = torch.cat(images, dim=0)
            
            log_message = f"成功生成{len(combined_images)}张图像，尺寸: {width}x{height}"
            logging.info(f"[ModelScope] {log_message}")
            
            return ("\n".join(image_urls), combined_images, log_message)
            
        except requests.exceptions.RequestException as e:
            logging.error(f"[ModelScope] 请求失败: {e}")
            # 创建一个空的张量，避免ComfyUI报错
            empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
            return ("", empty_tensor, f"请求失败: {e}")
        except Exception as e:
            logging.error(f"[ModelScope] 生成图像失败: {e}")
            # 创建一个空的张量，避免ComfyUI报错
            empty_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32) if torch else None
            return ("", empty_tensor, f"生成图像失败: {e}")
            
    def poll_task_status(self, task_id, headers, max_wait_time=600):
        """
        轮询任务状态
        Args:
            task_id: 任务ID
            headers: 请求头
            max_wait_time: 最大等待时间(秒)
        Returns:
            tuple: (图像URL列表, 状态消息)
        """
        api_url = f"https://www.modelscope.cn/api/v1/muse/predict/task/status?taskId={task_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(api_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                
                # 打印完整响应以便调试
                logging.debug(f"[ModelScope] 轮询API响应: {result}")
                
                if not result.get("Success"):
                    error_msg = result.get("Message", "未知错误")
                    logging.error(f"[ModelScope] 轮询任务状态失败: {error_msg}")
                    return ([], f"轮询任务状态失败: {error_msg}")
                    
                # 检查响应数据结构
                if "Data" not in result:
                    logging.error(f"[ModelScope] 轮询API响应格式不正确: {result}")
                    return ([], "轮询API响应格式不正确")
                    
                # 检查data位置
                task_data = None
                if "data" in result["Data"]:
                    task_data = result["Data"]["data"]
                else:
                    # 可能是直接在Data中
                    task_data = result["Data"]
                    
                if not task_data:
                    logging.error(f"[ModelScope] 无法从轮询API响应中获取任务数据: {result}")
                    return ([], "无法从轮询API响应中获取任务数据")
                status = task_data.get("status", "")
                
                if status == "COMPLETED" or status == "SUCCEED":
                    # 尝试从不同位置获取图像
                    images = []
                    
                    # 尝试从predictResult.images获取
                    if "predictResult" in task_data and isinstance(task_data["predictResult"], dict):
                        predict_result = task_data["predictResult"]
                        if "images" in predict_result and isinstance(predict_result["images"], list):
                            # 从每个图像对象中提取imageUrl字段
                            for img_obj in predict_result["images"]:
                                if isinstance(img_obj, dict) and "imageUrl" in img_obj:
                                    images.append(img_obj["imageUrl"])
                    
                    # 尝试从predictResult获取（旧格式）
                    elif "predictResult" in task_data and isinstance(task_data["predictResult"], list):
                        images = [item.get("url") for item in task_data.get("predictResult", []) if item and isinstance(item, dict) and item.get("url")]
                    
                    # 尝试从images获取
                    elif "images" in task_data and isinstance(task_data["images"], list):
                        for img_obj in task_data["images"]:
                            if isinstance(img_obj, dict) and "imageUrl" in img_obj:
                                images.append(img_obj["imageUrl"])
                            elif isinstance(img_obj, str):
                                images.append(img_obj)
                            elif isinstance(img_obj, dict) and "url" in img_obj:
                                images.append(img_obj["url"])
                    
                    # 尝试从result中获取
                    elif "result" in task_data and isinstance(task_data["result"], dict):
                        result_data = task_data["result"]
                        if "images" in result_data and isinstance(result_data["images"], list):
                            for img_obj in result_data["images"]:
                                if isinstance(img_obj, dict) and "imageUrl" in img_obj:
                                    images.append(img_obj["imageUrl"])
                                elif isinstance(img_obj, str):
                                    images.append(img_obj)
                                elif isinstance(img_obj, dict) and "url" in img_obj:
                                    images.append(img_obj["url"])
                        elif "image_urls" in result_data:
                            images = result_data.get("image_urls", [])
                    
                    # 添加调试信息
                    logging.info(f"[ModelScope] 任务完成，状态: {status}，生成了{len(images)}张图像")
                    if not images:
                        logging.warning(f"[ModelScope] 无法从响应中提取图像URL，任务数据: {task_data}")
                    else:
                        logging.info(f"[ModelScope] 成功提取图像URL: {images}")
                    
                    return (images, f"任务完成({status})")
                    
                elif status == "FAILED":
                    error_msg = task_data.get("errorMsg", "未知错误")
                    logging.error(f"[ModelScope] 任务失败: {error_msg}")
                    return ([], f"任务失败: {error_msg}")
                    
                elif status in ["PROCESSING", "QUEUING", "PENDING"]:
                    progress = task_data.get("progress", {})
                    percent = progress.get("percent", 0)
                    detail = progress.get("detail", "正在处理中...")
                    
                    logging.info(f"[ModelScope] 任务状态: {status}, 进度: {percent}%, 详情: {detail}")
                    
                    # 智能轮询间隔：排队时使用较长间隔，处理时使用较短间隔
                    if status == "QUEUING" or "排队" in detail:
                        # 排队时，间隔15秒
                        time.sleep(15)
                    elif status == "PROCESSING":
                        # 处理中，间隔8秒
                        time.sleep(8)
                    else:
                        # 其他状态，间隔10秒
                        time.sleep(10)
                        
                else:
                    logging.warning(f"[ModelScope] 未知任务状态: {status}")
                    # 未知状态，使用标准间隔
                    time.sleep(10)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"[ModelScope] 轮询请求失败: {e}")
                time.sleep(10)
                
        # 如果超时，返回空图像列表
        logging.warning(f"[ModelScope] 任务轮询超时，可能需要更长时间")
        return ([], "任务超时")
        
    def extract_csrf_token(self, cookie_str):
        """
        从Cookie字符串中提取CSRF Token
        Args:
            cookie_str: Cookie字符串
        Returns:
            str: CSRF Token，如果未找到则返回空字符串
        """
        try:
            # 清理cookie字符串
            cookie_str = cookie_str.strip()
            
            # 尝试从csrf_token格式提取
            match = re.search(r'csrf_token=([^;]+)', cookie_str)
            if match:
                token = match.group(1)
                # URL解码
                import urllib.parse
                token = urllib.parse.unquote(token)
                logging.debug(f"[ModelScope] 从Cookie中提取CSRF Token: {token}")
                return token
                
        except Exception as e:
            logging.error(f"[ModelScope] 提取CSRF Token失败: {e}")
            
        return ""