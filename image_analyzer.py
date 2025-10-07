import base64
import logging
import re
# from io import BytesIO  # 新增：用于内存中处理图片
# from PIL import Image  # 新增：用于图片格式转换
from openai import OpenAI

def analyze_image(image_path, api_key):
    """调用Qwen3-VL API分析图片"""
    try:
        # 读取并转换图片为WebP格式（关键修改）
        # try:
        #     with Image.open(image_path) as img:
        #         # 创建内存缓冲区存储转换后的WebP数据
        #         webp_buffer = BytesIO()
        #         # 转换为WebP格式（quality可调整，1-100）
        #         img.save(webp_buffer, format="WebP", quality=90)
        #         # 移动到缓冲区起始位置，读取二进制数据
        #         webp_buffer.seek(0)
        #         # 编码为base64
        #         base64_image = base64.b64encode(webp_buffer.read()).decode("utf-8")
        # except Exception as e:
        #     error_msg = f"图片格式转换失败（可能原图损坏或格式不支持）: {str(e)}"
        #     logging.error(error_msg)
        #     return False, error_msg
        
        # 读取并编码图片
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # 使用Qwen3-VL反推
        try:
            # 初始化OpenAI客户端
            client = OpenAI(
                base_url='https://api-inference.modelscope.cn/v1',
                # api_key= api_key,
                api_key= "ms-" + api_key,   #老版本的 KEY
            )
            
            # 构建提示词，包含用户要求的所有反推要点
            prompt = """在完全遵循图片内容的情况下，直接返回图片描述内容。生成一段 300 字以内类似下面这段提示词的提示词，并且注重描述画面的真实感，需要描述画面风格（如真实人像摄影、中国水墨画，油画，水彩画等）、画面中光线或明暗程度，镜头角度，画面构图比例等，如果是人像摄影，涉及到人脸脸部特写镜头需要描述人物表情，皮肤细节，人物性别国籍，如果是全身则需要描述清楚人物的姿势造型。如果是中国画等绘画作品需要描述具体的画种风格，这些描述都需要用自然语言回答，不要出现精准的数字，不允许出现特殊符号。
## 原则
    1. 使用**客观、精确和基于事实的语言**。撰写技巧：主体场景+画质风格+构图视角+光线氛围+技术参数，前后可以接关键词。
    2. 不要描述象征性的含义或氛围（例如，“传达决心”、“增强情绪”、“强调奋斗”、“营造神秘感”）。
    3. 不要使用隐喻或诗意的表达方式（例如，“月光在水面上翩翩起舞”）。
    4. 不要评价内容、技巧或呈现方式（例如，“展示”、“揭示”、“亮点”）。
示例 1： 这是一副专业写真作品，在户外海滩场景中，自然光线从斜上方照射，营造明亮氛围。近景构图下，一个亚洲女人妃妃戴浅卡其色棒球帽，帽檐边缘柔和，帽身有自然褶皱。头发为浅棕色中长发，发丝在风与光线下呈现动态，几缕发丝垂落肩头。穿深棕色吊带背心，肩带贴合肩部曲线，背心布料自然垂坠，胸前有小型十字刺绣纹理。右手向前伸展，似自拍动作。安妮·莱博维茨风格的艺术人像摄影，柔和的伦勃朗光勾勒出肌肉线条，氛围宁静而充满力量感，中画幅相机质感，影调丰富细腻，35mm广角镜头捕捉。
背景是草地、岩石与海洋：近处草地有自然起伏与草叶纹理；中景是灰黑色岩石，表面纹理清晰；远处是蓝色海洋，海面有波光反射，天空晴朗无云。
脸部皮肤呈现自然光泽，眼神看向镜头方向，神态自然。
整体自然光中，衣物褶皱、发丝动态、草地纹理、岩石质感、海洋波光等细节高度还原，呈现真实质感。

示例 2：这是一副专业人像摄影作品。在室内房间场景中，光线均匀柔和。中景构图下，一个亚洲女人妃妃穿传统风格服饰：白色上衣有红色镶边与花卉刺绣，宽袖设计；红色下裙搭配同色系腰带，肩部系红色飘带。头发为黑色直发，前额齐刘海，头顶戴两朵红色布艺花饰（花瓣纹理清晰，绿叶点缀），发间垂落红色丝带。
左手轻搭在身前，右手似整理衣物或持物（动作自然）。背景是浅色调窗帘，旁侧有带花纹布套的座椅。
脸部特写：皮肤呈现自然光泽，毛孔细节锐利；眼神看向镜头方向，画面干净柔和，富士胶片色调，50mm镜头带来的浅景深效果。
衣物细节：上衣褶皱随动作自然起伏，红色镶边边缘锐利；下裙面料垂坠感明显，腰带系结纹理清晰；飘带边缘柔和，布艺花饰的针脚与色彩过渡细腻。
背景元素：窗帘纹理均匀，座椅布套花纹细节锐利（色彩柔和）。整体在均匀光线下，皮肤、发丝、衣物、配饰的质感高度还原，呈现真实细节。"""
            
            # 发送请求
            response = client.chat.completions.create(
                model='Qwen/Qwen3-VL-30B-A3B-Instruct',
                # model='Qwen/Qwen2.5-VL-72B-Instruct',  # ModelScope Model-Id
                # model='Qwen/Qwen3-VL-235B-A22B-Instruct',  # ModelScope Model-Id
                messages=[{
                    'role': 'user',
                    'content': [{
                        'type': 'text',
                        'text': prompt,
                    }, {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/png;base64,{base64_image}",
                            # 'url': f"data:image/webp;base64,{base64_image}",
                        },
                    }],
                }],
                stream=False,
                timeout=60.0,  # 增加超时时间
            )
            
            # 处理响应
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                if content:
                    # 去除多余的空格和换行
                    filtered_content = re.sub(r'\s+', ' ', content).strip()
                    
                    # 限制字符数在500以内
                    if len(filtered_content) > 500:
                        # 尝试在合适的位置截断，避免破坏句子结构
                        truncated_content = filtered_content[:500]
                        last_period = truncated_content.rfind('。')
                        last_comma = truncated_content.rfind('，')
                        
                        if last_period > 400:  # 确保截断后至少保留400个字符
                            filtered_content = truncated_content[:last_period + 1]
                        elif last_comma > 400:
                            filtered_content = truncated_content[:last_comma + 1]
                        else:
                            filtered_content = truncated_content
                    
                    return True, filtered_content
                else:
                    return False, "未获取到反推结果，请重试。"
            else:
                return False, "Qwen3-VL API返回格式异常。"
        except Exception as e:
            error_msg = f"Qwen3-VL反推时出错: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = f"反推图片时出错: {str(e)}"
        logging.error(error_msg)
        return False, error_msg
