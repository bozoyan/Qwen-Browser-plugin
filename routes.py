import re
import uuid
import requests
import json
import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from image_analyzer import analyze_image
from config import ALLOWED_EXTENSIONS, MODEL_SCOPE_COOKIE, DEFAULT_WIDTH, DEFAULT_HEIGHT, LORA_ARGS, out_pic, model_info
from utils import allowed_file, extract_csrf_token, generate_trace_id
from task_poller import poll_task_smart, create_task_poller

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点，用于插件检测服务器状态"""
    return jsonify({
        'success': True,
        'message': '图片反推+魔搭生图服务运行正常',
        'status': 'healthy',
        'timestamp': str(datetime.now())
    })

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        session['image_path'] = file_path
        session['image_filename'] = filename

        return jsonify({'success': True, 'filename': filename})
    return jsonify({'success': False, 'error': 'File type not allowed'})

@main_bp.route('/analyze', methods=['POST'])
def analyze():
    image_path = session.get('image_path')
    if not image_path or not os.path.exists(image_path):
        return jsonify({'success': False, 'message': '请先上传图片！'})
    
    try:
        success, result = analyze_image(image_path, api_key=current_app.config['OPENAI_API_KEY'])
        if success:
            # 分析完成后再删除临时文件
            if os.path.exists(image_path):
                os.remove(image_path)
            return jsonify({'success': True, 'prompt': result})
        else:
            # 分析失败也要删除临时文件
            if os.path.exists(image_path):
                os.remove(image_path)
            return jsonify({'success': False, 'error': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/analyze_from_url', methods=['POST'])
def analyze_from_url():
    data = request.get_json()
    image_url = data.get('url')

    if not image_url:
        return jsonify({'success': False, 'message': '缺少图片URL！'})

    try:
        # 发送GET请求下载图片
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # 如果请求失败，则抛出异常

        # 创建一个临时文件来保存图片
        temp_dir = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # 从URL中提取文件名，如果无法提取则生成一个唯一的文件名
        filename = os.path.basename(image_url.split('?')[0])
        if not filename:
            filename = str(uuid.uuid4()) + '.jpg'
        else:
            filename = secure_filename(filename)

        temp_image_path = os.path.join(temp_dir, filename)

        with open(temp_image_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 图片下载成功后，调用analyze_image进行分析
        success, result = analyze_image(temp_image_path, api_key=current_app.config['OPENAI_API_KEY'])
        
        # 分析完成后删除临时文件
        # if os.path.exists(temp_image_path):
        #     os.remove(temp_image_path)

        if success:
            return jsonify({'success': True, 'prompt': result})
        else:
            return jsonify({'success': False, 'error': result})

    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'下载图片失败: {e}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'图片分析出错: {e}'})

@main_bp.route('/api/generate_image', methods=['POST'])
def generate_image_proxy():
    """生成图片的后端代理API"""
    try:
        # 获取请求参数
        data = request.get_json()
        prompt = data.get('prompt', '')
        cookie = MODEL_SCOPE_COOKIE  # 直接使用config中的cookie
        width = DEFAULT_WIDTH  # 直接使用config中的默认宽度
        height = DEFAULT_HEIGHT  # 直接使用config中的默认高度
        check_status_only = data.get('check_status_only', False)
        
        if not prompt:
            return jsonify({'success': False, 'error': '请输入提示词'})
        
        if not cookie:
            return jsonify({'success': False, 'error': 'Cookie未配置，请在config.py中设置MODEL_SCOPE_COOKIE'})
        
        logging.info(f'开始生成图片，提示词: {prompt[:50]}{"..." if len(prompt) > 50 else ""}')
        
        # 打印详细的请求参数信息
        # 构建请求参数
        api_url = 'https://www.modelscope.cn/api/v1/muse/predict/task/submit'
        
        print("=" * 80)
        print("🚀 SUBMIT任务 - 开始提交图片生成任务")
        print("=" * 80)
        print(f"📝 提示词: {prompt}")
        print(f"📏 图片尺寸: {width}x{height}")
        print(f"🍪 Cookie (前50字符): {cookie[:50]}...")
        print(f"🔗 API URL: {api_url}")
        # 如果是只查询状态，直接尝试查询当前用户最新的任务
        if check_status_only:
            # 简单模拟查询逻辑

            # 这里可以根据需要实现更复杂的逻辑，例如根据用户session或cookie查找最近的任务
            return jsonify({
                'success': True,
                'status': 'PROCESSING',
                'progress': 0,
                'message': '请先发送完整的生成请求',
                'is_completed': False
            })
        F_prompt="feifei,a photo-realistic shoot from a portrait camera angle about a young woman,big boobs,妃妃,"        
        # 构建请求参数 - 尝试多种可能的任务类型参数名称
        request_body = {
            'taskType': 'TXT_2_IMG',  # 原始参数名
            'type': 'TXT_2_IMG',      # 可能的替代参数名1
            'task_type': 'TXT_2_IMG', # 可能的替代参数名2
            'predictType': 'TXT_2_IMG', # 可能的替代参数名3
            'modelArgs': {
                'checkpointModelVersionId': 275167,   # 大模型地址
                'checkpointShowInfo': "Qwen_Image_v1.safetensors",   # 大模型名称
                'loraArgs': LORA_ARGS,
                'predictType': "TXT_2_IMG"
            },
            'promptArgs': {
                'prompt': F_prompt + prompt,
                'negativePrompt': ""
            },
            'basicDiffusionArgs': {
                'sampler': "Euler",
                'guidanceScale': 4,
                'seed': -1,
                'numInferenceSteps': 50,
                'numImagesPerPrompt': 4,
                'width': int(width),
                'height': int(height)
            },
            'advanced': False,
            'addWaterMark': False,
            'adetailerArgsMap': {},
            'hiresFixFrontArgs': {
                # 'modelName': "R-ESRGAN 4x+",
                'modelName': "Nomos 8k SCHATL 4x",
                "scale": 4
            },
            'controlNetFullArgs': []
        }
        
        # 提取CSRF Token - 增强版本，支持更多格式
        def extract_csrf_token_enhanced(cookie_str):
            # 清理cookie字符串，确保格式正确
            cookie_str = cookie_str.strip()
            
            # 尝试从csrf_token格式提取
            match = re.search(r'csrf_token=([^;]+)', cookie_str)
            if match:
                token = match.group(1)
                # 处理可能的URL编码或引号
                return token.strip('"')
            
            # 尝试从csrftoken格式提取
            match = re.search(r'csrftoken=([^;]+)', cookie_str)
            if match:
                token = match.group(1)
                return token.strip('"')
            
            # 尝试从csrf_session格式提取
            match = re.search(r'csrf_session=([^;]+)', cookie_str)
            if match:
                token = match.group(1)
                return token.strip('"')
            
            # 尝试从XSRF-TOKEN格式提取
            match = re.search(r'XSRF-TOKEN=([^;]+)', cookie_str)
            if match:
                token = match.group(1)
                return token.strip('"')
            
            # 如果没有找到CSRF Token，记录警告但继续执行
            logging.warning('未从Cookie中提取到CSRF Token')
            return ''
        
        # 生成Trace ID
        def generate_trace_id_enhanced():
            import uuid
            return str(uuid.uuid4())
        
        # 发送请求到ModelScope API - 增强的请求头，更接近真实浏览器
        headers = {
            'Content-Type': 'application/json',
            'Cookie': cookie,
            'X-Csrftoken': extract_csrf_token_enhanced(cookie),
            'X-Modelscope-Trace-Id': generate_trace_id_enhanced(),
            'X-Modelscope-Accept-Language': 'zh_CN',
            'Referer': 'https://www.modelscope.cn/aigc/imageGeneration?tab=advanced&presetId=5804',
            'Origin': 'https://www.modelscope.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Bx-V': '2.5.31',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Host': 'www.modelscope.cn',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        # 详细记录请求信息以便调试
        print("📦 请求体详细信息:")
        print(f"   taskType: {request_body.get('taskType')}")
        print(f"   modelArgs.checkpointModelVersionId: {request_body['modelArgs']['checkpointModelVersionId']}")
        print(f"   modelArgs.checkpointShowInfo: {request_body['modelArgs']['checkpointShowInfo']}")
        print(f"   modelArgs.loraArgs: {request_body['modelArgs']['loraArgs']}")
        print(f"   promptArgs.prompt: {request_body['promptArgs']['prompt'][:50]}...")
        print(f"   basicDiffusionArgs.width: {request_body['basicDiffusionArgs']['width']}")
        print(f"   basicDiffusionArgs.height: {request_body['basicDiffusionArgs']['height']}")
        print(f"   basicDiffusionArgs.numImagesPerPrompt: {request_body['basicDiffusionArgs']['numImagesPerPrompt']}")
        
        csrf_token = extract_csrf_token_enhanced(cookie)
        trace_id = generate_trace_id_enhanced()
        print(f"🔐 CSRF Token: {csrf_token}")
        print(f"🆔 Trace ID: {trace_id}")

        
        print("🌐 开始发送请求到ModelScope API...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=request_body,
            timeout=30  # 设置30秒超时
        )
        
        print("📥 收到API响应:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        print(f"   响应内容: {response.text}")

        
        if not response.ok:
            print(f"❌ API请求失败!")
            print(f"   状态码: {response.status_code}")
            print(f"   错误信息: {response.text}")

            return jsonify({'success': False, 'error': f'API请求失败，状态码: {response.status_code}'})
        
        result = response.json()
        print("✅ API请求成功!")
        print(f"📋 解析后的响应: {result}")

        
        # 检查是否有错误信息
        if 'Data' in result and result['Data'] and 'code' in result['Data'] and result['Data']['code'] != 0:
            error_msg = result['Data'].get('message', '未知错误')
            print(f"❌ API返回业务错误: {error_msg}")

            if '会话已过期' in error_msg:
                return jsonify({'success': False, 'error': 'Cookie已过期，请重新登录获取新的Cookie'})
            return jsonify({'success': False, 'error': f'API返回错误: {error_msg}'})
        
        # 提取任务ID
        task_id = None
        print("🔍 开始提取任务ID...")
        if 'data' in result and result['data'] and 'taskId' in result['data']:
            task_id = result['data']['taskId']
            print(f"   从 result.data.taskId 提取到: {task_id}")
        elif 'Data' in result and result['Data'] and 'data' in result['Data'] and result['Data']['data'] and 'taskId' in result['Data']['data']:
            task_id = result['Data']['data']['taskId']
            print(f"   从 result.Data.data.taskId 提取到: {task_id}")
        elif 'Data' in result and result['Data'] and 'taskId' in result['Data']:
            task_id = result['Data']['taskId']
            print(f"   从 result.Data.taskId 提取到: {task_id}")
        elif 'taskId' in result:
            task_id = result['taskId']
            print(f"   从 result.taskId 提取到: {task_id}")
        
        if not task_id:
            print("❌ 未能提取到任务ID!")
            print(f"   完整响应结构: {result}")
            logging.error(f'未获取到任务ID，API响应结构: {result}')
            return jsonify({'success': False, 'error': '未获取到任务ID，请检查Cookie是否有效'})
        
        print(f"🎯 成功获取任务ID: {task_id}")
        logging.info(f'获取到任务ID: {task_id}')
        
        # 轮询获取图片结果
        import time
        base_poll_url = 'https://www.modelscope.cn/api/v1/muse/predict/task/status'
        max_retries = 60
        retry_interval = 3
        
        print("=" * 80)
        print("🔄 STATUS查询 - 开始轮询任务状态")
        print("=" * 80)
        print(f"🎯 任务ID: {task_id}")
        print(f"🔗 查询URL: {base_poll_url}")
        print(f"⏱️ 最大重试次数: {max_retries}")
        print(f"⏰ 重试间隔: {retry_interval}秒")
        
        # 为轮询请求创建请求头
        poll_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Bx-V': '2.5.31',
            'Connection': 'keep-alive',
            'Cookie': cookie,
            'Host': 'www.modelscope.cn',
            'Referer': 'https://www.modelscope.cn/aigc/imageGeneration?tab=advanced&presetId=5804',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'X-Modelscope-Accept-Language': 'zh_CN',
            'X-Modelscope-Trace-Id': generate_trace_id_enhanced()
        }
        
        for i in range(max_retries):
            time.sleep(retry_interval)
            
            try:
                print(f"\n🔍 第{i+1}/{max_retries}次查询任务状态")

                
                # 使用GET方法和URL查询参数
                poll_url = f'{base_poll_url}?taskId={task_id}'
                
                print(f"   📡 请求URL: {poll_url}")
                print(f"   🍪 Cookie (前50字符): {cookie[:50]}...")

                
                poll_response = requests.get(
                    poll_url,
                    headers=poll_headers,
                    timeout=10
                )
                
                print(f"   📥 响应状态码: {poll_response.status_code}")
                print(f"   📄 响应内容: {poll_response.text}")
                
                if poll_response.status_code == 200:
                    try:
                        response_json = poll_response.json()
                        print(f"   ✅ 成功解析JSON: {response_json}")

                        
                        # 处理不同格式的响应结构 - 参考111.py的完善逻辑
                        task_data = None
                        status = ''
                        progress = {}
                        percent = 0
                        detail = ''
                        
                        print(f"   🔍 解析响应结构...")
                        
                        # 优先处理实际日志中看到的响应结构
                        if response_json.get('Success') and response_json.get('Data'):
                            data = response_json['Data']
                            print(f"   📊 Data字段: {data}")
                            
                            # 检查Data中是否有data字段（实际日志中的结构）
                            if data.get('data'):
                                task_data = data['data']
                            # 同时兼容之前代码期望的结构
                            elif data.get('success') and data.get('data'):
                                task_data = data['data']
                            
                            # 如果获取到了task_data
                            if task_data:
                                status = task_data.get('status', '')
                                progress = task_data.get('progress', {})
                                percent = progress.get('percent', 0) if progress else 0
                                detail = progress.get('detail', '') if progress else ''
                                
                                print(f"   📈 任务状态: {status}")
                                print(f"   📊 进度: {percent}%")
                                print(f"   📝 详情: {detail}")

                        else:
                            print(f"   ❌ 响应结构异常 - Success: {response_json.get('Success')}, Data: {response_json.get('Data')}")
                        
                        # 处理任务状态 - 增强版本，支持更多状态
                        if task_data and status == 'COMPLETED' and task_data.get('predictResult'):
                            print(f"   🎉 任务完成！获取结果...")

                            # 提取图片URL - 适配新的响应结构
                            images = []
                            prompt_text = ""

                            # 新结构：从predictResult.images中提取
                            if isinstance(task_data['predictResult'], dict) and task_data['predictResult'].get('images'):
                                images_data = task_data['predictResult']['images']
                                if isinstance(images_data, list):
                                    images = [item.get('imageUrl') for item in images_data if item and item.get('imageUrl')]
                                    # 从第一张图片获取prompt（所有图片的prompt应该是相同的）
                                    if images_data and images_data[0] and images_data[0].get('prompt'):
                                        prompt_text = images_data[0]['prompt']

                            # 旧的兼容性处理
                            elif isinstance(task_data['predictResult'], list):
                                images = [item.get('url') for item in task_data['predictResult'] if item and item.get('url')]
                            elif isinstance(task_data['predictResult'], dict) and task_data['predictResult'].get('results'):
                                images = [item.get('url') for item in task_data['predictResult']['results'] if item and item.get('url')]
                            
                            if images:
                                print(f"   ✅ 图片生成成功，获取到{len(images)}张图片")

                                # 保存图片到本地并创建JSON文档
                                try:
                                    # 获取任务ID和请求ID
                                    request_id = response_json.get('RequestId') or response_json.get('Data', {}).get('requestId') or ''

                                    # 创建任务文件夹
                                    task_folder = os.path.join(out_pic, task_id)
                                    os.makedirs(task_folder, exist_ok=True)

                                    # 下载图片到本地
                                    downloaded_images = []
                                    for img_url in images:
                                        try:
                                            # 从URL中提取文件名
                                            img_filename = os.path.basename(img_url.split('?')[0])
                                            if not img_filename or '.' not in img_filename:
                                                img_filename = f"image_{len(downloaded_images) + 1}.jpg"

                                            img_path = os.path.join(task_folder, img_filename)

                                            # 下载图片
                                            img_response = requests.get(img_url, timeout=30)
                                            img_response.raise_for_status()

                                            with open(img_path, 'wb') as f:
                                                f.write(img_response.content)

                                            downloaded_images.append(img_filename)
                                            print(f"   📥 图片已保存: {img_path}")

                                        except Exception as img_error:
                                            print(f"   ❌ 下载图片失败 {img_url}: {img_error}")
                                            logging.error(f"下载图片失败 {img_url}: {img_error}")

                                    # 创建JSON文档
                                    json_data = {
                                        'id': task_id,
                                        'requestId': request_id,
                                        'prompt': prompt_text,  # 添加prompt字段
                                        'reverse_image': '',  # 这里暂时为空，因为生成图片接口没有原始图片URL
                                        'url': images
                                    }

                                    json_file = os.path.join(task_folder, f"{task_id}.json")
                                    with open(json_file, 'w', encoding='utf-8') as f:
                                        json.dump(json_data, f, ensure_ascii=False, indent=2)

                                    print(f"   📄 JSON文档已创建: {json_file}")
                                    logging.info(f"任务 {task_id} 完成，保存了{len(downloaded_images)}张图片和JSON文档")

                                except Exception as save_error:
                                    print(f"   ❌ 保存图片或创建JSON失败: {save_error}")
                                    logging.error(f"保存图片或创建JSON失败: {save_error}")

                                return jsonify({'success': True, 'images': images, 'task_id': task_id})
                            else:
                                print(f"   ❌ 图片生成成功但未找到图片URL")
                                logging.error('图片生成成功但未找到图片URL')
                                return jsonify({'success': False, 'error': '图片生成成功但未找到图片URL'})
                        elif task_data and status == 'FAILED':
                            error_msg = task_data.get('errorMsg', '未知错误')
                            print(f"   ❌ 任务失败: {error_msg}")
                            logging.error(f'任务失败: {error_msg}')
                            return jsonify({'success': False, 'error': f'任务失败: {error_msg}'})
                        elif task_data and status in ('PROCESSING', 'QUEUING', 'PENDING'):
                            # 任务仍在处理中，返回进度信息给前端
                            queue_info = detail
                            if status == 'PENDING' and task_data.get('taskQueue'):
                                task_queue = task_data['taskQueue']
                                queue_info = f"排队中，共有{task_queue.get('total', '未知')}人在排队，您在第{task_queue.get('currentPosition', '未知')}位"
                            elif status == 'QUEUING':
                                if not queue_info:
                                    queue_info = "正在排队，请稍候..."
                            elif status == 'PROCESSING':
                                if not queue_info:
                                    queue_info = f"正在生成图片中...进度: {percent}%"
                            
                            print(f"   ⏳ 任务{status}中: {queue_info}")
                            logging.info(f'任务{status}中: {queue_info}')
                            continue
                        elif task_data and status in ('SUCCESS', 'SUCCEED'):
                            # 处理成功状态 - 适配新的API响应结构
                            images = []
                            prompt_text = ""
                            print(f"   🎉 任务成功状态，开始提取图片URL...")
                            logging.debug(f'任务成功状态，task_data结构: {str(task_data)[:500]}...')
                            
                            try:
                                # 新结构：从predictResult.images中提取
                                if isinstance(task_data.get('predictResult'), dict) and task_data['predictResult'].get('images'):
                                    images_data = task_data['predictResult']['images']
                                    if isinstance(images_data, list):
                                        images = [item.get('imageUrl') for item in images_data if item and item.get('imageUrl')]
                                        # 从第一张图片获取prompt（所有图片的prompt应该是相同的）
                                        if images_data and images_data[0] and images_data[0].get('prompt'):
                                            prompt_text = images_data[0]['prompt']
                                    print(f"   📍 从task_data.predictResult.images提取到{len(images)}张图片")
                                
                                # 备选方案1：从task_data.results中提取
                                if not images and task_data.get('results'):
                                    images = [item.get('url') for item in task_data['results'] if item and item.get('url')]
                                    print(f"   📍 从task_data.results提取到{len(images)}张图片")
                                
                                # 备选方案2：从task_data.predictResult中提取（旧兼容）
                                if not images and task_data.get('predictResult'):
                                    predict_result = task_data['predictResult']
                                    if isinstance(predict_result, list):
                                        images = [item.get('url') for item in predict_result if item and item.get('url')]
                                    elif isinstance(predict_result, dict):
                                        if predict_result.get('results'):
                                            images = [item.get('url') for item in predict_result['results'] if item and item.get('url')]
                                        elif predict_result.get('url'):
                                            images = [predict_result['url']]
                                        # 直接从predictResult中提取image_list
                                        elif predict_result.get('image_list'):
                                            images = predict_result['image_list']
                                    print(f"   📍 从task_data.predictResult提取到{len(images)}张图片")
                                
                                # 备选方案3：递归搜索响应中所有URL
                                if not images:
                                    def find_urls(obj, urls=None):
                                        if urls is None:
                                            urls = []
                                        if isinstance(obj, dict):
                                            for k, v in obj.items():
                                                if k.lower() in ('url', 'imageurl', 'image_url') and isinstance(v, str):
                                                    urls.append(v)
                                                elif isinstance(v, (dict, list)):
                                                    find_urls(v, urls)
                                        elif isinstance(obj, list):
                                            for item in obj:
                                                find_urls(item, urls)
                                        return urls
                                    
                                    # 递归搜索所有可能的URL
                                    all_urls = find_urls(response_json)
                                    # 过滤出看起来像图片的URL
                                    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
                                    candidate_images = [url for url in all_urls if url.lower().endswith(image_extensions)]
                                    
                                    if candidate_images:
                                        images = candidate_images
                                        print(f"   📍 通过递归搜索找到了{len(images)}张图片URL")
                                
                                # 记录详细日志便于调试
                                if not images:
                                    print(f"   ❌ 未能提取图片URL，响应结构可能已更改")
                                    logging.error('未能提取图片URL，响应结构可能已更改')
                                    logging.debug(f'详细response_json: {str(response_json)[:1000]}')
                            except Exception as e:
                                print(f"   ❌ 提取图片URL时异常: {e}")
                                logging.error(f'提取图片URL时异常: {str(e)}')
                            
                            if images:
                                print(f"   ✅ 图片生成成功，获取到{len(images)}张图片")
                                logging.info(f'图片生成成功，获取到{len(images)}张图片')

                                # 保存图片到本地并创建JSON文档
                                try:
                                    # 获取任务ID和请求ID
                                    request_id = response_json.get('RequestId') or response_json.get('Data', {}).get('requestId') or ''

                                    # 创建任务文件夹
                                    task_folder = os.path.join(out_pic, task_id)
                                    os.makedirs(task_folder, exist_ok=True)

                                    # 下载图片到本地
                                    downloaded_images = []
                                    for img_url in images:
                                        try:
                                            # 从URL中提取文件名
                                            img_filename = os.path.basename(img_url.split('?')[0])
                                            if not img_filename or '.' not in img_filename:
                                                img_filename = f"image_{len(downloaded_images) + 1}.jpg"

                                            img_path = os.path.join(task_folder, img_filename)

                                            # 下载图片
                                            img_response = requests.get(img_url, timeout=30)
                                            img_response.raise_for_status()

                                            with open(img_path, 'wb') as f:
                                                f.write(img_response.content)

                                            downloaded_images.append(img_filename)
                                            print(f"   📥 图片已保存: {img_path}")

                                        except Exception as img_error:
                                            print(f"   ❌ 下载图片失败 {img_url}: {img_error}")
                                            logging.error(f"下载图片失败 {img_url}: {img_error}")

                                    # 创建JSON文档
                                    json_data = {
                                        'id': task_id,
                                        'requestId': request_id,
                                        'prompt': prompt_text,  # 添加prompt字段
                                        'reverse_image': '',  # 这里暂时为空，因为生成图片接口没有原始图片URL
                                        'url': images
                                    }

                                    json_file = os.path.join(task_folder, f"{task_id}.json")
                                    with open(json_file, 'w', encoding='utf-8') as f:
                                        json.dump(json_data, f, ensure_ascii=False, indent=2)

                                    print(f"   📄 JSON文档已创建: {json_file}")
                                    logging.info(f"任务 {task_id} 完成，保存了{len(downloaded_images)}张图片和JSON文档")

                                except Exception as save_error:
                                    print(f"   ❌ 保存图片或创建JSON失败: {save_error}")
                                    logging.error(f"保存图片或创建JSON失败: {save_error}")

                                logging.info(f'图片生成成功，获取到{len(images)}张图片')
                                return jsonify({'success': True, 'images': images, 'task_id': task_id})
                            else:
                                print(f"   ❌ 图片生成成功但未找到图片URL")
                                logging.error('图片生成成功但未找到图片URL')
                                logging.debug(f'最终response_json结构: {str(response_json)[:500]}...')
                                return jsonify({'success': False, 'error': '图片生成成功但未找到图片URL'})
                        elif response_json.get('code') == 0 and response_json.get('data'):
                            # 尝试兼容旧结构
                            data = response_json['data']
                            status = data.get('status', '')
                            
                            if status == 'SUCCESS':
                                # 提取图片URL
                                images = [result['url'] for result in data['results']]
                                print(f"   ✅ 图片生成成功，获取到{len(images)}张图片")

                                # 保存图片到本地并创建JSON文档
                                try:
                                    # 获取任务ID和请求ID
                                    request_id = response_json.get('RequestId') or response_json.get('Data', {}).get('requestId') or ''

                                    # 创建任务文件夹
                                    task_folder = os.path.join(out_pic, task_id)
                                    os.makedirs(task_folder, exist_ok=True)

                                    # 下载图片到本地
                                    downloaded_images = []
                                    for img_url in images:
                                        try:
                                            # 从URL中提取文件名
                                            img_filename = os.path.basename(img_url.split('?')[0])
                                            if not img_filename or '.' not in img_filename:
                                                img_filename = f"image_{len(downloaded_images) + 1}.jpg"

                                            img_path = os.path.join(task_folder, img_filename)

                                            # 下载图片
                                            img_response = requests.get(img_url, timeout=30)
                                            img_response.raise_for_status()

                                            with open(img_path, 'wb') as f:
                                                f.write(img_response.content)

                                            downloaded_images.append(img_filename)
                                            print(f"   📥 图片已保存: {img_path}")

                                        except Exception as img_error:
                                            print(f"   ❌ 下载图片失败 {img_url}: {img_error}")
                                            logging.error(f"下载图片失败 {img_url}: {img_error}")

                                    # 创建JSON文档
                                    json_data = {
                                        'id': task_id,
                                        'requestId': request_id,
                                        'prompt': '',  # 旧结构中没有prompt信息
                                        'reverse_image': '',  # 这里暂时为空，因为生成图片接口没有原始图片URL
                                        'url': images
                                    }

                                    json_file = os.path.join(task_folder, f"{task_id}.json")
                                    with open(json_file, 'w', encoding='utf-8') as f:
                                        json.dump(json_data, f, ensure_ascii=False, indent=2)

                                    print(f"   📄 JSON文档已创建: {json_file}")
                                    logging.info(f"任务 {task_id} 完成，保存了{len(downloaded_images)}张图片和JSON文档")

                                except Exception as save_error:
                                    print(f"   ❌ 保存图片或创建JSON失败: {save_error}")
                                    logging.error(f"保存图片或创建JSON失败: {save_error}")

                                logging.info(f'图片生成成功，获取到{len(images)}张图片')
                                return jsonify({'success': True, 'images': images, 'task_id': task_id})
                            elif status == 'FAILED':
                                error_msg = data.get('errorMsg', '未知错误')
                                print(f"   ❌ 图片生成失败: {error_msg}")

                                return jsonify({'success': False, 'error': f'图片生成失败: {error_msg}'})
                        else:
                            print(f"   ⚠️ 未知状态或数据结构: status={status}, task_data={task_data}")

                            
                    except Exception as e:
                        print(f"   ❌ JSON解析失败: {e}")
                        print(f"   📄 原始响应内容: {poll_response.text}")
                        logging.error(f'解析JSON响应失败: {e}')
                        continue
                else:
                    print(f"   ❌ 请求失败，状态码: {poll_response.status_code}")
                    print(f"   📄 响应内容: {poll_response.text}")
                    logging.error(f'轮询请求失败，状态码: {poll_response.status_code}')
                    continue
                    
            except Exception as e:
                print(f"   ❌ 请求异常: {e}")
                logging.error(f'轮询请求异常: {e}')
                continue
        
        print("=" * 80)
        print("⏰ 轮询超时 - 任务未在预期时间内完成")
        print("=" * 80)
        logging.error('轮询超时，任务未在预期时间内完成')
        return jsonify({'success': False, 'error': '任务超时，请稍后重试'})

    except requests.exceptions.RequestException as e:
        logging.error(f'请求ModelScope API时出错: {e}')
        return jsonify({'success': False, 'error': f'请求ModelScope API时出错: {e}'})
    except Exception as e:
        logging.error(f'生成图片时出错: {e}')
        return jsonify({'success': False, 'error': f'生成图片时出错: {e}'})

@main_bp.route('/reverse_image', methods=['POST'])
def reverse_image():
    data = request.get_json()
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({'success': False, 'message': '缺少图片URL！'})

    temp_image_path = ''
    try:
        # 发送GET请求下载图片
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # 如果请求失败，则抛出异常

        # 创建一个临时文件来保存图片
        temp_dir = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # 从URL中提取文件名，如果无法提取则生成一个唯一的文件名
        filename = os.path.basename(image_url.split('?')[0])
        if not filename:
            filename = str(uuid.uuid4()) + '.jpg'
        else:
            filename = secure_filename(filename)

        temp_image_path = os.path.join(temp_dir, filename)

        with open(temp_image_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 图片下载成功后，调用analyze_image进行分析
        success, result = analyze_image(temp_image_path, api_key=current_app.config['OPENAI_API_KEY'])

        # 分析完成后保留临时文件，用于reverse_image字段
        if success:
            return jsonify({
                'success': True,
                'prompt': result,
                'temp_image_path': temp_image_path  # 返回临时文件路径
            })
        else:
            # 分析失败则删除临时文件
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            return jsonify({'success': False, 'error': result})
    except Exception as e:
        # 发生异常则删除临时文件
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/process_image_complete', methods=['POST'])
def process_image_complete():
    """
    综合处理图片的完整流程：上传 -> 反推 -> 生成图片
    仿照 /api/generate_image 的实现方式
    """
    print("=" * 80)
    print("🚀 PROCESS_IMAGE_COMPLETE - 开始综合图片处理")
    print("=" * 80)

    try:
        # 1. 获取上传的文件
        if 'file' not in request.files:
            print("❌ 没有文件被上传")
            return jsonify({'success': False, 'error': '没有文件被上传'})

        file = request.files['file']
        if file.filename == '':
            print("❌ 文件名为空")
            return jsonify({'success': False, 'error': '文件名为空'})

        print(f"📁 接收到文件: {file.filename}, 大小: {file.content_length}")

        # 验证文件类型
        if not allowed_file(file.filename):
            print(f"❌ 不支持的文件类型: {file.filename}")
            return jsonify({'success': False, 'error': f'不支持的文件类型: {file.filename}'})

        # 2. 获取JSON数据（可能来自表单或请求体）
        json_data = {}
        if request.is_json:
            json_data = request.get_json() or {}
        else:
            # 从表单字段获取JSON数据
            json_data_str = request.form.get('json_data', '{}')
            try:
                json_data = json.loads(json_data_str)
            except json.JSONDecodeError:
                json_data = {}

        # 获取自定义参数
        cookie = json_data.get('cookie', MODEL_SCOPE_COOKIE)
        width = json_data.get('width', DEFAULT_WIDTH)
        height = json_data.get('height', DEFAULT_HEIGHT)
        num_images = json_data.get('num_images', 4)
        enable_hires = json_data.get('enable_hires', True)
        openai_api_key = json_data.get('openai_api_key', current_app.config.get('OPENAI_API_KEY', ''))

        # 获取模型参数
        checkpoint = json_data.get('checkpoint', '')
        lora1 = json_data.get('lora1', '')
        lora2 = json_data.get('lora2', '')
        lora3 = json_data.get('lora3', '')
        lora4 = json_data.get('lora4', '')

        print(f"📏 生成参数: {width}x{height}, 数量: {num_images}")
        print(f"🎨 模型设置: Checkpoint={checkpoint}")
        print(f"🔗 LoRA设置: {lora1}, {lora2}, {lora3}, {lora4}")
        print(f"🍪 Cookie长度: {len(cookie) if cookie else 0}")
        print(f"🔑 OpenAI Key长度: {len(openai_api_key) if openai_api_key else 0}")

        if not cookie:
            print("❌ 缺少ModelScope Cookie")
            return jsonify({'success': False, 'error': '缺少ModelScope Cookie'})

        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # 验证文件是否保存成功
        if not os.path.exists(file_path):
            print(f"❌ 文件保存失败: {file_path}")
            return jsonify({'success': False, 'error': '文件保存失败'})

        actual_size = os.path.getsize(file_path)
        print(f"✅ 文件已保存: {file_path} (大小: {actual_size} bytes)")

        if actual_size == 0:
            print(f"❌ 文件大小为0，可能下载失败")
            return jsonify({'success': False, 'error': '文件损坏或下载失败'})

        # 3. 分析图片
        print("🔍 开始分析图片...")
        try:
            success, prompt = analyze_image(file_path, api_key=openai_api_key)
            if not success:
                print(f"❌ 图片分析失败: {prompt}")
                return jsonify({'success': False, 'error': f'图片分析失败: {prompt}'})

            print(f"✅ 图片分析成功，反推文字长度: {len(prompt)}")
            print(f"📝 反推文字预览: {prompt[:1000]}...")

        except Exception as e:
            print(f"❌ 图片分析异常: {str(e)}")
            return jsonify({'success': False, 'error': f'图片分析异常: {str(e)}'})

        # 4. 生成图片
        print("🎨 开始生成图片...")
        try:

            # 构建自定义请求参数
            api_url = 'https://www.modelscope.cn/api/v1/muse/predict/task/submit'

            # 处理checkpoint参数（可能是字符串或字典）

            # 构建LoRA参数 - 需要数组格式
            lora_args = []  # 改为数组格式
            active_loras = []

            # 处理LoRA参数（可能是字典或字符串）
            lora_list = [lora1, lora2, lora3, lora4]
            lora_scales = [1.0, 0.8, 0.6, 0.4]

            for i, (lora, scale) in enumerate(zip(lora_list, lora_scales)):
                if lora:
                    if isinstance(lora, dict):
                        # 如果是字典格式，直接提取信息
                        lora_id = lora.get('modelVersionId')
                        lora_name = lora.get('LoraName', f'LoRA_{i+1}')
                        if lora_id:
                            active_loras.append(lora_name)
                            # 创建LoRA对象格式的参数
                            lora_obj = {
                                'loraName': lora_name,
                                'modelVersionId': lora_id,
                                'scale': scale
                            }
                            lora_args.append(lora_obj)
                            print(f"🔗 [PROCESS] 从字典获取LoRA: Name={lora_name}, ID={lora_id}, Scale={scale}")
                    elif isinstance(lora, str) and lora.strip():
                        # 如果是字符串格式，尝试从model_info获取ID
                        lora_name = lora.strip()
                        lora_id = None

                        # 在model_info中查找对应的ID
                        if lora_name in model_info:
                            lora_id = model_info[lora_name]['id']

                        if lora_id:
                            active_loras.append(lora_name)
                            # 创建LoRA对象格式的参数
                            lora_obj = {
                                'loraName': lora_name,
                                'modelVersionId': lora_id,
                                'scale': scale
                            }
                            lora_args.append(lora_obj)
                            print(f"🔗 [PROCESS] 从字符串获取LoRA: Name={lora_name}, ID={lora_id}, Scale={scale}")
                        else:
                            print(f"⚠️ [PROCESS] 未找到LoRA {lora_name} 的ID，跳过")

            print(f"🔧 [PROCESS] 构建自定义请求参数:")

            # 获取checkpoint ID（如果选择了的话）
            checkpoint_id = None
            checkpoint_name = None

            # 处理checkpoint参数（可能是字符串或字典）
            if checkpoint:
                if isinstance(checkpoint, dict):
                    # 如果是字典格式，直接提取ID和名称
                    checkpoint_id = checkpoint.get('checkpointModelVersionId')
                    checkpoint_name = checkpoint.get('checkpointShowInfo', checkpoint.get('CheckpointName', ''))
                    print(f"🎯 [PROCESS] 从字典获取checkpoint: ID={checkpoint_id}, Name={checkpoint_name}")
                elif isinstance(checkpoint, str) and checkpoint.strip():
                    # 如果是字符串格式，从model_info中查找
                    checkpoint_name = checkpoint.strip()
                    checkpoint_id = model_info.get(checkpoint_name, {}).get('id', None)
                    print(f"🎯 [PROCESS] 从字符串获取checkpoint: Name={checkpoint_name}, ID={checkpoint_id}")
                else:
                    print(f"⚠️ [PROCESS] checkpoint格式异常: {checkpoint}")
            else:
                print("📝 [PROCESS] 未设置checkpoint，将使用默认模型")

            # 构建模型参数
            model_args = {
                'predictType': 'TXT_2_IMG'
            }

            # 如果选择了checkpoint，添加到modelArgs
            if checkpoint_id:
                model_args['checkpointModelVersionId'] = checkpoint_id
                if checkpoint_name:
                    model_args['checkpointShowInfo'] = checkpoint_name

            # 如果有LoRA，添加LoRA参数
            if lora_args:
                model_args['loraArgs'] = lora_args

            print(f"🎯 [PROCESS] 参数处理完成:")
            print(f"   Checkpoint: {checkpoint_name} (ID: {checkpoint_id})")
            print(f"   Active LoRAs: {active_loras}")
            print(f"   LoRA Args (数组格式): {lora_args}")
            for i, lora in enumerate(lora_args):
                print(f"      LoRA {i+1}: {lora}")

            # 构建基础提示词
            base_prompt = "feifei,a photo-realistic shoot from a portrait camera angle about a young woman,big boobs,妃妃,"  # 可以根据需要调整

            request_body = {
                'taskType': 'TXT_2_IMG',
                'type': 'TXT_2_IMG',
                'task_type': 'TXT_2_IMG',
                'predictType': 'TXT_2_IMG',
                'modelArgs': model_args,
                'promptArgs': {
                    'prompt': base_prompt + prompt,
                    'negativePrompt': "low quality, worst quality, blurry, watermark, signature"
                },
                'basicDiffusionArgs': {
                    'sampler': "Euler",
                    'guidanceScale': 4,
                    'seed': -1,
                    'numInferenceSteps': 50,
                    'numImagesPerPrompt': int(num_images),
                    'width': int(width),
                    'height': int(height)
                },
                'advanced': False,
                'addWaterMark': False,
                'adetailerArgsMap': {},
                'hiresFixFrontArgs': {
                    'modelName': "Nomos 8k SCHATL 4x",
                    "scale": 4
                },
                'controlNetFullArgs': []
            }

            print(f"🎯 [PROCESS] 最终请求体构建完成:")
            print(f"   API URL: {api_url}")
            print(f"   Task Type: {request_body['taskType']}")
            print(f"   Prompt: {(request_body['promptArgs']['prompt'][:100] + '...') if len(request_body['promptArgs']['prompt']) > 100 else request_body['promptArgs']['prompt']}")
            print(f"   Model Args: {json.dumps(request_body['modelArgs'], indent=2, ensure_ascii=False)}")
            print(f"   Basic Diffusion Args: {json.dumps(request_body['basicDiffusionArgs'], indent=2, ensure_ascii=False)}")

            # 提取CSRF Token
            def extract_csrf_token_enhanced(cookie_str):
                cookie_str = cookie_str.strip()
                match = re.search(r'csrf_token=([^;]+)', cookie_str)
                if match:
                    token = match.group(1)
                    return token.strip('"')
                match = re.search(r'csrftoken=([^;]+)', cookie_str)
                if match:
                    return match.group(1).strip('"')
                return ''

            # 构建请求头
            headers = {
                'Content-Type': 'application/json',
                'Cookie': cookie,
                'X-Csrftoken': extract_csrf_token_enhanced(cookie),
                'X-Modelscope-Trace-Id': str(uuid.uuid4()),
                'X-Modelscope-Accept-Language': 'zh_CN',
                'Referer': 'https://www.modelscope.cn/aigc/imageGeneration?tab=advanced&presetId=5804',
                'Origin': 'https://www.modelscope.cn',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
            }

            print("📡 发送生成请求到ModelScope...")
            print(f"🌐 请求URL: {api_url}")
            print(f"🔐 CSRF Token: {extract_csrf_token_enhanced(cookie)}")
            print(f"📋 请求头包含: {list(headers.keys())}")

            response = requests.post(api_url, headers=headers, json=request_body, timeout=30)

            if response.status_code != 200:
                print(f"❌ ModelScope API请求失败: {response.status_code}")
                print(f"📄 响应内容: {response.text}")
                return jsonify({'success': False, 'error': f'ModelScope API请求失败: {response.status_code}'})

            result = response.json()
            print("✅ ModelScope API请求成功")
            print(f"📄 完整响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")

            # 检查响应结果
            if not result.get('Success'):
                error_msg = result.get('Message', '未知错误')
                print(f"❌ ModelScope返回错误: {error_msg}")
                return jsonify({'success': False, 'error': f'ModelScope返回错误: {error_msg}'})

            # 提取任务ID - 优先查找数字格式的taskId
            task_id = None

            # 尝试结构1: result.data.taskId (数字格式)
            if 'data' in result and result['data'] and isinstance(result['data'], dict):
                potential_id = result['data'].get('taskId')
                if potential_id and str(potential_id).isdigit():
                    task_id = str(potential_id)
                    print(f"🎯 从 result.data.taskId 获取数字格式任务ID: {task_id}")

            # 尝试结构2: result.Data.data.taskId (数字格式)
            if not task_id and 'Data' in result and isinstance(result['Data'], dict):
                if 'data' in result['Data'] and isinstance(result['Data']['data'], dict):
                    potential_id = result['Data']['data'].get('taskId')
                    if potential_id and str(potential_id).isdigit():
                        task_id = str(potential_id)
                        print(f"🎯 从 result.Data.data.taskId 获取数字格式任务ID: {task_id}")

            # 尝试结构3: 直接在result中找taskId (数字格式)
            if not task_id:
                potential_id = result.get('taskId')
                if potential_id and str(potential_id).isdigit():
                    task_id = str(potential_id)
                    print(f"🎯 从 result.taskId 获取数字格式任务ID: {task_id}")

            # 尝试结构4: 直接在result.Data中找taskId (数字格式)
            if not task_id and 'Data' in result and isinstance(result['Data'], dict):
                potential_id = result['Data'].get('taskId')
                if potential_id and str(potential_id).isdigit():
                    task_id = str(potential_id)
                    print(f"🎯 从 result.Data.taskId 获取数字格式任务ID: {task_id}")

            # 只有在没有找到数字格式taskId时，才查找UUID格式的requestId
            if not task_id:
                print("🔍 未找到数字格式的taskId，尝试查找UUID格式的requestId...")

                # 尝试结构5: result.Data.requestId (UUID格式 - 备用)
                if 'Data' in result and isinstance(result['Data'], dict):
                    potential_id = result['Data'].get('requestId')
                    if potential_id:
                        task_id = potential_id
                        print(f"⚠️ 使用UUID格式的requestId作为备用: {task_id}")
                        print(f"🔍 注意: UUID格式的ID可能不被轮询API支持")

                # 尝试结构6: 直接在result中找requestId
                if not task_id:
                    potential_id = result.get('requestId')
                    if potential_id:
                        task_id = potential_id
                        print(f"⚠️ 使用UUID格式的requestId: {task_id}")

            # 尝试结构4: 优先查找数字格式的taskId（轮询API需要数字格式）
            if not task_id:
                print("🔍 优先搜索数字格式的taskId（轮询API需要）...")
                def find_numeric_task_id(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            current_path = f"{path}.{key}" if path else key
                            # 优先搜索taskId字段
                            if key.lower() in ['taskid', 'task_id'] and value:
                                task_id_str = str(value)
                                if task_id_str.isdigit():
                                    print(f"🎯 找到数字格式的taskId: {current_path} = {task_id_str}")
                                    return task_id_str
                                else:
                                    print(f"⚠️ 找到taskId但非数字格式: {current_path} = {task_id_str}")
                            found = find_numeric_task_id(value, current_path)
                            if found:
                                return found
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            found = find_numeric_task_id(item, f"{path}[{i}]")
                            if found:
                                return found
                    return None

                # 首先查找数字格式的taskId
                numeric_task_id = find_numeric_task_id(result)
                if numeric_task_id:
                    task_id = numeric_task_id
                    print(f"✅ 使用数字格式taskId进行轮询: {task_id}")
                else:
                    # 如果没找到数字ID，查找任何可能的ID字段
                    print("🔍 未找到数字taskId，搜索所有可能的任务ID字段...")
                    def find_any_task_id(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                current_path = f"{path}.{key}" if path else key
                                # 搜索可能的ID字段
                                if key.lower() in ['taskid', 'task_id', 'id'] and value:
                                    print(f"🎯 找到可能的任务ID字段: {current_path} = {value}")
                                    return value
                                # 搜索可能是ID的字符串字段
                                if isinstance(value, str) and len(value) > 5:
                                    # 检查是否看起来像ID（包含数字、字母组合）
                                    if any(c.isdigit() for c in value) and len(value) < 50:
                                        if 'request' in key.lower() or 'id' in key.lower() or key.lower() == 'code':
                                            print(f"🎯 找到可能的ID字段: {current_path} = {value}")
                                            return value
                                found = find_any_task_id(value, current_path)
                                if found:
                                    return found
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                found = find_any_task_id(item, f"{path}[{i}]")
                                if found:
                                    return found
                        return None

                    task_id = find_any_task_id(result)

            if not task_id:
                print("❌ 无法获取任务ID")
                print(f"🔍 响应结构分析:")
                print(f"   Success: {result.get('Success')}")
                print(f"   Message: {result.get('Message')}")
                print(f"   数据键: {list(result.keys())}")

                # 显示可能的数据结构
                if 'Data' in result:
                    print(f"   Data类型: {type(result['Data'])}")
                    if isinstance(result['Data'], dict):
                        print(f"   Data键: {list(result['Data'].keys())}")
                        print(f"   Data内容: {result['Data']}")
                        if 'data' in result['Data']:
                            print(f"   Data.data类型: {type(result['Data']['data'])}")
                            print(f"   Data.data内容: {result['Data']['data']}")
                            if isinstance(result['Data']['data'], dict):
                                print(f"   Data.data键: {list(result['Data']['data'].keys())}")
                        else:
                            print("   🔍 检查其他可能的字段:")
                            for key in result['Data'].keys():
                                value = result['Data'][key]
                                if value and isinstance(value, str) and len(value) > 10:
                                    print(f"      {key}: {value} (可能是ID)")
                                elif isinstance(value, dict):
                                    print(f"      {key}: {list(value.keys())} (字典)")

                return jsonify({'success': False, 'error': '无法获取任务ID'})

            print(f"🎯 获取到任务ID: {task_id}")

            # 检查任务ID格式
            if task_id and isinstance(task_id, str) and '-' in task_id:
                print(f"⚠️ 警告: 检测到UUID格式的任务ID ({task_id})，轮询API可能需要数字格式")
                print(f"🔍 搜索完整的响应，寻找数字格式的taskId...")

                # 再次搜索完整响应，寻找数字格式的ID
                def find_numeric_task_id(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            current_path = f"{path}.{key}" if path else key
                            if key.lower() in ['taskid', 'task_id'] and value:
                                if isinstance(value, (int, str)) and str(value).isdigit():
                                    print(f"🎯 找到数字格式的任务ID: {current_path} = {value}")
                                    return str(value)
                            found = find_numeric_task_id(value, current_path)
                            if found:
                                return found
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            found = find_numeric_task_id(item, f"{path}[{i}]")
                            if found:
                                return found
                    return None

                numeric_task_id = find_numeric_task_id(result)
                if numeric_task_id:
                    print(f"✅ 找到数字格式的任务ID，使用: {numeric_task_id}")
                    task_id = numeric_task_id
                else:
                    print(f"❌ 未找到数字格式的任务ID，可能需要调整API调用方式")
                    # 尝试使用其他方法获取数字ID
                    print(f"🔍 尝试从完整响应中提取所有数字字段...")
                    print(f"📄 完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

            # 4. 使用智能轮询器查询任务状态
            print("🔄 使用智能轮询器查询任务状态...")
            print(f"🎯 任务ID: {task_id}")

            try:
                # 使用新的智能轮询器
                success, result_data = poll_task_smart(
                    cookie=cookie,
                    task_id=task_id,
                    max_attempts=60,
                    interval=3
                )

                if success and result_data.get('Success'):
                    # 任务成功，处理结果数据
                    # 根据实际响应结构：result_data.Data.data
                    if result_data.get('Data') and isinstance(result_data['Data'], dict):
                        inner_data = result_data['Data']
                        if inner_data.get('data') and isinstance(inner_data['data'], dict):
                            task_data = inner_data['data']
                        else:
                            task_data = inner_data
                    else:
                        task_data = {}

                    print(f"   📊 任务数据结构: {str(task_data)[:200]}...")

                    # 提取图片URL - 基于正确响应格式
                    images = []
                    if task_data.get('predictResult') and isinstance(task_data['predictResult'], dict):
                        predict_result = task_data['predictResult']

                        # 基于实际响应结构：predictResult.images[].imageUrl
                        if predict_result.get('images') and isinstance(predict_result['images'], list):
                            images_data = predict_result['images']
                            for item in images_data:
                                if item and isinstance(item, dict) and item.get('imageUrl'):
                                    images.append(item['imageUrl'])

                            print(f"✅ 从ModelScope新结构获取到{len(images)}张图片")
                            for i, img_url in enumerate(images, 1):
                                print(f"   图片{i}: {img_url}")

                    if images:
                        print(f"🎉 图片生成成功，获取到{len(images)}张图片")

                        # 5. 返回最终结果
                        result = {
                            'success': True,
                            'prompt': prompt,
                            'images': images,
                            'task_id': task_id
                        }

                        print("🎉 综合处理完成！")
                        print(f"📝 反推文字长度: {len(prompt)}")
                        print(f"🖼️ 生成图片数量: {len(images)}")

                        return jsonify(result)
                    else:
                        print("❌ 未能提取图片URL")
                        logging.error('未能提取图片URL')
                        return jsonify({'success': False, 'error': '图片生成成功但未找到图片URL'})
                else:
                    # 任务失败或超时
                    error_info = result_data if isinstance(result_data, dict) else {}
                    error_msg = error_info.get('error', '任务失败或超时')

                    # 如果有指导信息，返回给用户
                    if 'guidance' in error_info:
                        print(f"💡 任务失败，提供指导信息")
                        return jsonify(error_info)
                    elif 'UUID format not supported' in str(error_msg):
                        print(f"❌ UUID格式ID不被轮询API支持")
                        # 创建指导信息
                        guided_response = {
                            'success': False,
                            'error': 'UUID格式ID不被轮询API支持',
                            'task_id': task_id,
                            'guidance': {
                                'message': 'ModelScope API现在返回UUID格式的任务ID，但轮询API仍需要数字格式ID',
                                'suggestions': [
                                    '请手动到ModelScope图片库查看生成的图片',
                                    '任务ID: ' + task_id,
                                    '或者等待找到支持UUID格式轮询的新API端点'
                                ],
                                'gallery_link': 'https://www.modelscope.cn/studios',
                                'task_id': task_id
                            }
                        }
                        return jsonify(guided_response)
                    else:
                        print(f"❌ 任务失败: {error_msg}")
                        return jsonify({'success': False, 'error': error_msg})

            except Exception as e:
                print(f"❌ 智能轮询异常: {e}")
                logging.error(f'智能轮询异常: {e}')
                return jsonify({'success': False, 'error': f'轮询异常: {str(e)}'})

        except Exception as e:
            print(f"❌ 图片生成异常: {str(e)}")
            return jsonify({'success': False, 'error': f'图片生成异常: {str(e)}'})

    except Exception as e:
        print(f"❌ 综合处理异常: {str(e)}")
        return jsonify({'success': False, 'error': f'综合处理异常: {str(e)}'})
