import re
import uuid
import requests
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
import os
import logging
from image_analyzer import analyze_image
from config import ALLOWED_EXTENSIONS, MODEL_SCOPE_COOKIE, DEFAULT_WIDTH, DEFAULT_HEIGHT, LORA_ARGS
from utils import allowed_file, extract_csrf_token, generate_trace_id

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
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            return jsonify({'success': True, 'prompt': result})
        else:
            # 分析失败也要删除临时文件
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
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
        
        # if success:
        #     return jsonify({'success': True, 'prompt': result})
        # else:
        #     return jsonify({'success': False, 'error': result})

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
                'sampler': "Euler simple",
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
            'controlNetFullArgs': [],
            'hiresFixFrontArgs': None
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

                            # 提取图片URL - 适配不同的响应结构
                            images = []
                            if isinstance(task_data['predictResult'], list):
                                images = [item.get('url') for item in task_data['predictResult'] if item and item.get('url')]
                            elif isinstance(task_data['predictResult'], dict) and task_data['predictResult'].get('results'):
                                images = [item.get('url') for item in task_data['predictResult']['results'] if item and item.get('url')]
                            
                            if images:
                                print(f"   ✅ 图片生成成功，获取到{len(images)}张图片")

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
                            # 处理成功状态 - 增强版本，支持多种URL提取方式
                            images = []
                            print(f"   🎉 任务成功状态，开始提取图片URL...")
                            logging.debug(f'任务成功状态，task_data结构: {str(task_data)[:500]}...')
                            
                            # 尝试从不同位置提取图片URL，增强兼容性
                            try:
                                # 从Data.data.predictResult中提取URL（根据日志中的实际响应结构）
                                if 'Data' in response_json and isinstance(response_json['Data'], dict):
                                    data_obj = response_json['Data']
                                    if 'data' in data_obj and isinstance(data_obj['data'], dict):
                                        inner_data = data_obj['data']
                                        if 'predictResult' in inner_data and isinstance(inner_data['predictResult'], dict):
                                            predict_result = inner_data['predictResult']
                                            if predict_result.get('imageUrl'):
                                                images = [predict_result['imageUrl']]
                                                print(f"   📍 从Data.data.predictResult.imageUrl提取图片URL")
                                            # 从predictResult中直接提取image_list字段
                                            elif predict_result.get('image_list'):
                                                images = predict_result['image_list']
                                                print(f"   📍 从Data.data.predictResult.image_list提取图片URL列表")
                                
                                # 备选方案1：从task_data.results中提取
                                if not images and task_data.get('results'):
                                    images = [item.get('url') for item in task_data['results'] if item and item.get('url')]
                                    print(f"   📍 从task_data.results提取到{len(images)}张图片")
                                
                                # 备选方案2：从task_data.predictResult中提取
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
        
        if success:
            return jsonify({'success': True, 'prompt': result})
        else:
            return jsonify({'success': False, 'error': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
