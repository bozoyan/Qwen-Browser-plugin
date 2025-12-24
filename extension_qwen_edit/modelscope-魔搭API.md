## 概要#

魔搭通过API-Inference，将开源模型服务化并通过API接口进行标准化，让开发者能以更轻量和迅捷的方式体验开源模型，并集成到不同的AI应用中，从而展开富有创造力的尝试，包括与工具结合调用，来构建多种多样的AI应用原型。

## 前提条件：创建账号并获取Token#

API-Inference面向ModelScope注册用户免费提供，请在登陆后获取您专属的访问令牌（Access Token）。

## 使用方法#

### 大语言模型 LLM#

当前魔搭平台的API-Inference，针对大语言模型提供OpenAI API兼容的接口。 对于LLM模型的API，使用前，请先安装OpenAI SDK:

```
pip install openai
```

NOTE

其他流行的接口也陆续支持中，例如[Anthropic API](https://docs.anthropic.com/en/api)，可参见下面的 “大语言模型 LLM（Anthropic API兼容接口）” 部分。

安装后就可以通过标准的OpenAI调用方式使用。具体调用方式，在每个模型页面右侧的API-Inference范例中以提供，**请以模型页面的 API-Inference 示范代码为准**，尤其例如对于reasoning模型，调用的方式与标准LLM会有一些细微区别。以下范例仅供参考。

```javascript
from openai import OpenAI

client = OpenAI(
    api_key="MODELSCOPE_ACCESS_TOKEN", # 请替换成您的ModelScope Access Token
    base_url="https://api-inference.modelscope.cn/v1/"
)


response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-32B-Instruct", # ModelScope Model-Id
    messages=[
        {
            'role': 'system',
            'content': 'You are a helpful assistant.'
        },
        {
            'role': 'user',
            'content': '用python写一下快排'
        }
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end='', flush=True)
```

在这个范例里，使用魔搭的API-Inference，有几个需要适配的有几个地方：

- base url: 指向魔搭API-Inference服务 `https://api-inference.modelscope.cn/v1/`。
- api_key: 使用魔搭的访问令牌(Access Token), 可以从您的魔搭账号中获取：[https://modelscope.cn/my/myaccesstoken](https://modelscope.cn/my/myaccesstoken) 。
- 模型名字(model):使用魔搭上开源模型的Model Id，例如`Qwen/Qwen2.5-Coder-32B-Instruct` 。

### 大语言模型 LLM（Anthropic API兼容接口）#

针对LLM模型，API-Inference也支持与Anthropic API兼容的调用方式。要使用Anthropic模式，请在使用前，安装Anthropic SDK:

```
pip install anthropic
```

IMPORTANT

Anthropic API兼容调用方式当前整处于beta测试阶段。如果您在使用过程中遇到任何问题，请联系我们[提供反馈](https://modelscope.cn/docs/community/contact-us)。

安装Anthropic SDK后，即可调用，以下为使用范例。

#### 流式调用#

```javascript
import anthropic

client = anthropic.Anthropic(
    api_key="MODELSCOPE_ACCESS_TOKEN", # 请替换成您的ModelScope Access Token
    base_url="https://api-inference.modelscope.cn")

with client.messages.stream(
    model="Qwen/Qwen2.5-7B-Instruct", # ModelScope Model-Id
    messages=[
        {"role": "user", "content": "write a python quicksort"}
    ],
    max_tokens = 1024
) as stream:
  for text in stream.text_stream:
      print(text, end="", flush=True)
```

#### 非流式调用#

```javascript
import anthropic

client = anthropic.Anthropic(
    api_key="MODELSCOPE_ACCESS_TOKEN", # 请替换成您的ModelScope Access Token
    base_url="https://api-inference.modelscope.cn")

message = client.messages.create(
    model="Qwen/Qwen2.5-7B-Instruct", # ModelScope Model-Id
    messages=[
        {"role": "user", "content": "write a python quicksort"}
    ],
    max_tokens = 1024
)
print(message.content[0].text)
```

在这个范例里，使用魔搭的API-Inference，有几个需要适配的有几个地方：

- base url: 指向魔搭API-Inference服务 `https://api-inference.modelscope.cn` 。
- api_key: 使用魔搭的访问令牌(Access Token), 可以从您的魔搭账号中获取：[https://modelscope.cn/my/myaccesstoken](https://modelscope.cn/my/myaccesstoken) 。
- 模型名字(model):使用魔搭上开源模型的Model Id，例如`Qwen/Qwen2.5-Coder-32B-Instruct` 。

更多Anthropic API的接口用法以及参数，可以参考 [Anthropic API官方文档](https://docs.anthropic.com/en/api)。

### 视觉模型#

对于视觉VL模型，同样可以通过OpenAI API调用，例如：

```javascript
from openai import OpenAI

client = OpenAI(
    api_key="MODELSCOPE_ACCESS_TOKEN", # 请替换成您的ModelScope Access Token
    base_url="https://api-inference.modelscope.cn/v1"
)

response = client.chat.completions.create(
    model="Qwen/QVQ-72B-Preview", # ModelScope Model-Id
    messages = [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "You are a helpful and harmless assistant. You are Qwen developed by Alibaba. You should think step-by-step."}
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/QVQ/demo.png"}
                },
                {   "type": "text",
                    "text": "What value should be filled in the blank space?"
                },
            ],
        }
    ],
    stream=True
    )


for chunk in response:
    print(chunk.choices[0].delta.content, end='', flush=True)
```

### AIGC模型调用API

支持API调用的模型列表，可以通过[AIGC模型](https://www.modelscope.cn/aigc/models)页面进行搜索。 API的调用示例如下:

```typescript
import requests
import time
import json
from PIL import Image
from io import BytesIO

base_url = 'https://api-inference.modelscope.cn/'
api_key = "<MODELSCOPE_SDK_TOKEN>"

common_headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

response = requests.post(
    f"{base_url}v1/images/generations",
    headers={**common_headers, "X-ModelScope-Async-Mode": "true"},
    data=json.dumps({
        "model": "Qwen/Qwen-Image",
        # "loras": "<lora-repo-id>", # optional lora(s)
        """
        LoRA(s) Configuration:
        - for Single LoRA:
        "loras": "<lora-repo-id>"
        - for Multiple LoRAs:
        "loras": {"<lora-repo-id1>": 0.6, "<lora-repo-id2>": 0.4}
        - Upto 6 LoRAs, all weight-coeffients must sum to 1.0
        """
        "prompt": "A golden cat"
    }, ensure_ascii=False).encode('utf-8')
)


response.raise_for_status()
task_id = response.json()["task_id"]

while True:
    result = requests.get(
        f"{base_url}v1/tasks/{task_id}",
        headers={**common_headers, "X-ModelScope-Task-Type": "image_generation"},
    )
    result.raise_for_status()
    data = result.json()

    if data["task_status"] == "SUCCEED":
        image = Image.open(BytesIO(requests.get(data["output_images"][0]).content))
        image.save("result_image.jpg")
        break
    elif data["task_status"] == "FAILED":
        print("Image Generation Failed.")
        break

    time.sleep(5)
```

### AIGC模型调用API更多参数说明

参数名	参数说明	是否必须	参数类型	示例	取值范围
model	模型id	是	string	MAILAND/majicflus_v1	ModelScope上的AIGC 模型ID
prompt	正向提示词，大部分模型建议使用英文提示词效果较好。	是	string	A mysterious girl walking down the corridor.	长度小于2000
negative_prompt	负向提示词	否	string	lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry	长度小于2000
size	生成图像分辨率大小	否	string	1024x1024	分辨率范围:
SD系列:[64x64,2048x2048]，FLUX:[64x64,1024x1024]，Qwen-Image:[64x64,1664x1664]
seed	随机种子	否	int	12345	[0,2^31-1]
steps	采样步数	否	int	30	[1,100]
guidance	提示词引导系数	否	float	3.5	[1.5,20]
image_url	待编辑图片的url地址，该参数只适用于支持图片编辑的模型	否	string	https://resources.modelscope.cn/aigc/image_edit.png	确保公网可访问
loras	LoRA模型，用于风格迁移或细节增强。请在ModelScope AIGC专区模型库查找与基础模型兼容的LoRA模型	否	string | dict	单个LoRA: "<lora-repo-id>"
多个LoRA: {"<lora-repo-id1>": 0.6, "<lora-repo-id2>": 0.4}	多LoRA权重总和须为1.0，最多6个