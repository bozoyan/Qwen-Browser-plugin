"""
示例工作流程
演示如何在ComfyUI中使用ModelScope插件生成图像
"""

import json
import os

# 示例工作流程JSON
WORKFLOW_EXAMPLE = {
    "3": {
        "inputs": {
            "seed": 12345,
            "steps": 20,
            "cfg": 8,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1,
            "model": [
                "4",
                0
            ],
            "positive": [
                "6",
                0
            ],
            "negative": [
                "7",
                0
            ],
            "latent_image": [
                "5",
                0
            ]
        },
        "class_type": "KSampler",
        "_meta": {
            "title": "KSampler"
        }
    },
    "4": {
        "inputs": {
            "ckpt_name": "v1-5-pruned-emaonly.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {
            "title": "Load Checkpoint"
        }
    },
    "5": {
        "inputs": {
            "width": 512,
            "height": 512,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage",
        "_meta": {
            "title": "Empty Latent Image"
        }
    },
    "6": {
        "inputs": {
            "text": "a beautiful landscape with mountains and a lake",
            "clip": [
                "4",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "Positive"
        }
    },
    "7": {
        "inputs": {
            "text": "blurry, low quality, distorted",
            "clip": [
                "4",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "Negative"
        }
    },
    "8": {
        "inputs": {
            "samples": [
                "3",
                0
            ],
            "vae": [
                "4",
                2
            ]
        },
        "class_type": "VAEDecode",
        "_meta": {
            "title": "VAE Decode"
        }
    },
    "9": {
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": [
                "8",
                0
            ]
        },
        "class_type": "SaveImage",
        "_meta": {
            "title": "Save Image"
        }
    },
    "10": {
        "inputs": {
            "prompt": "a beautiful landscape with mountains and a lake",
            "width": 928,
            "height": 1664,
            "num_images": 4,
            "enable_hires": True,
            "api_key": "",
            "cookie": "在这里填写您的ModelScope Cookie",
            "checkpoint": [
                "11",
                0
            ],
            "lora1": [
                "12",
                0
            ],
            "lora2": [
                "13",
                0
            ]
        },
        "class_type": "ModelScopeImageNode",
        "_meta": {
            "title": "ModelScope 图像生成"
        }
    },
    "11": {
        "inputs": {
            "checkpoint": "Qwen_Image_v1 (ID: 275167)",
            "custom_id": "",
            "custom_name": "",
            "use_custom": False
        },
        "class_type": "CheckpointNode",
        "_meta": {
            "title": "ModelScope Checkpoint"
        }
    },
    "12": {
        "inputs": {
            "lora": "FEIFEI (ID: 310150, Scale: 1)",
            "custom_id": "",
            "custom_name": "",
            "custom_scale": 1.0,
            "use_custom": False,
            "scale": 1.2
        },
        "class_type": "LoraNode",
        "_meta": {
            "title": "ModelScope LoRA"
        }
    },
    "13": {
        "inputs": {
            "lora": "GUA_V2 (ID: 334516, Scale: 1)",
            "custom_id": "",
            "custom_name": "",
            "custom_scale": 1.0,
            "use_custom": False,
            "scale": 0.8
        },
        "class_type": "LoraNode",
        "_meta": {
            "title": "ModelScope LoRA"
        }
    },
    "14": {
        "inputs": {
            "filename_prefix": "ModelScope",
            "images": [
                "10",
                1
            ]
        },
        "class_type": "SaveImage",
        "_meta": {
            "title": "Save Image"
        }
    }
}

def save_example_workflow():
    """保存示例工作流程到文件"""
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    workflow_file = os.path.join(plugin_dir, "example_workflow.json")
    
    with open(workflow_file, 'w', encoding='utf-8') as f:
        json.dump(WORKFLOW_EXAMPLE, f, indent=2)
    
    print(f"示例工作流程已保存到: {workflow_file}")

if __name__ == "__main__":
    save_example_workflow()