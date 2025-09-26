import base64
import logging
import re
from openai import OpenAI

def analyze_image(image_path, api_key):
    """调用Qwen2.5-VL API分析图片"""
    try:

        
        # 读取并编码图片
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # 使用Qwen2.5-VL反推
        try:
            # 初始化OpenAI客户端
            client = OpenAI(
                base_url='https://api-inference.modelscope.cn/v1',
                api_key=api_key,
            )
            
            # 构建提示词，包含用户要求的所有反推要点
            prompt = """在完全遵循图片内容的情况下，生成一段 300 字以内类似下面这段提示词的提示词，并且注重描述真实感，需要描述镜头角度，构图等，如果是脸部特写镜头需要描述人物表情，皮肤细节，人物国籍性别，如果是全身则需要描述清楚人物姿势等，用自然语言回答，不要出现精准的数字，不允许出现特殊符号
## 原则
    1. 使用**客观、精确和基于事实的语言**。
    2. 不要描述象征性的含义或氛围（例如，“传达决心”、“增强情绪”、“强调奋斗”、“营造神秘感”）。
    3. 不要使用隐喻或诗意的表达方式（例如，“月光在水面上翩翩起舞”）。
    4. 不要评价内容、技巧或呈现方式（例如，“展示”、“揭示”、“亮点”）。
示例 1： 在户外海滩场景中，自然光线从斜上方照射，营造明亮氛围。近景构图下，一个亚洲女人妃妃戴浅卡其色棒球帽，帽檐边缘柔和，帽身有自然褶皱。头发为浅棕色中长发，发丝在风与光线下呈现动态，几缕发丝垂落肩头。穿深棕色吊带背心，肩带贴合肩部曲线，背心布料自然垂坠，胸前有小型十字刺绣纹理。右手向前伸展，似自拍动作。
背景是草地、岩石与海洋：近处草地有自然起伏与草叶纹理；中景是灰黑色岩石，表面纹理清晰；远处是蓝色海洋，海面有波光反射，天空晴朗无云。
脸部皮肤呈现自然光泽，眼神看向镜头方向，神态自然。
整体自然光中，衣物褶皱、发丝动态、草地纹理、岩石质感、海洋波光等细节高度还原，呈现真实质感。

示例 2：在室内房间场景中，光线均匀柔和。中景构图下，一个亚洲女人妃妃穿传统风格服饰：白色上衣有红色镶边与花卉刺绣，宽袖设计；红色下裙搭配同色系腰带，肩部系红色飘带。头发为黑色直发，前额齐刘海，头顶戴两朵红色布艺花饰（花瓣纹理清晰，绿叶点缀），发间垂落红色丝带。
左手轻搭在身前，右手似整理衣物或持物（动作自然）。背景是浅色调窗帘，旁侧有带花纹布套的座椅。
脸部特写：皮肤呈现自然光泽，毛孔细节锐利；眼神看向镜头方向，
衣物细节：上衣褶皱随动作自然起伏，红色镶边边缘锐利；下裙面料垂坠感明显，腰带系结纹理清晰；飘带边缘柔和，布艺花饰的针脚与色彩过渡细腻。
背景元素：窗帘纹理均匀，座椅布套花纹细节锐利（色彩柔和）。整体在均匀光线下，皮肤、发丝、衣物、配饰的质感高度还原，呈现真实细节。"""
            
            # 发送请求
            response = client.chat.completions.create(
                # model='stepfun-ai/Step3',  # ModelScope Model-Id
                model='Qwen/Qwen3-VL-235B-A22B-Instruct',  # ModelScope Model-Id
                messages=[{
                    'role': 'user',
                    'content': [{
                        'type': 'text',
                        'text': prompt,
                    }, {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/webp;base64,{base64_image}",
                            # 'url': f"data:image/jpeg;base64,{base64_image}",
                            # 'url': f"data:image/png;base64,{base64_image}",
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
