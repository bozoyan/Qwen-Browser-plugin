"""
ModelScope API任务轮询模块
支持新的UUID格式任务ID和旧的数字格式任务ID
基于正确的响应格式：{"Code":200,"Data":{"data":{...}},"Success":true}
"""

import requests
import re
import time
import logging
from typing import Dict, Optional, Tuple, Any
from flask import request, jsonify, Blueprint
from config import MODEL_SCOPE_COOKIE

task_poller_bp = Blueprint('task_poller', __name__)

class ModelScopeTaskPoller:
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.headers = {
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://www.modelscope.cn',
            'Referer': 'https://www.modelscope.cn/studios?tab=0'
        }

    def poll_task_with_numeric_id(self, task_id: str, max_attempts: int = 60, interval: int = 5) -> Tuple[bool, Dict]:
        """使用数字ID轮询任务状态（传统方式）- 适配正确的响应格式"""
        url = f"https://www.modelscope.cn/api/v1/muse/predict/task/status?taskId={task_id}"

        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()

                data = response.json()
                print(f"📊 轮询任务 {task_id} (第{attempt+1}次): {data}")

                # 基于正确响应格式：{"Code":200,"Data":{"data":{...}},"Success":true}
                if data.get('Success') == True and data.get('Code') == 200 and data.get('Data'):
                    if isinstance(data['Data'], dict) and data['Data'].get('data'):
                        task_data = data['Data']['data']
                        status = task_data.get('status', '').upper()

                        if status in ['SUCCEED', 'SUCCESS', 'COMPLETED']:
                            print(f"✅ 任务 {task_id} 完成")
                            return True, data
                        elif status == 'FAILED':
                            print(f"❌ 任务 {task_id} 失败")
                            return False, data
                        elif status in ['PENDING', 'RUNNING', 'PROCESSING', 'QUEUING']:
                            print(f"⏳ 任务 {task_id} 仍在处理中...")
                            time.sleep(interval)
                            continue
                        else:
                            print(f"⚠️ 任务 {task_id} 未知状态: {status}")
                    else:
                        print(f"⚠️ Data.data结构异常: {data.get('Data')}")

                elif data.get('Code') == 40000 or 'NumberFormatException' in str(data.get('Data', {}).get('message', '')):
                    print(f"🔄 检测到ID格式错误，UUID格式不支持数字轮询")
                    # 返回False而不是None，以便在poll_task_with_fallback中处理
                    return False, {'error': 'UUID format not supported', 'original_data': data}

                else:
                    print(f"⚠️ 任务 {task_id} 轮询响应异常: {data}")

            except requests.RequestException as e:
                print(f"❌ 轮询任务 {task_id} 网络错误: {e}")
                time.sleep(interval)

        print(f"⏰ 任务 {task_id} 轮询超时")
        return False, {'error': '轮询超时', 'timeout': True}

    def poll_task_with_fallback(self, task_id: str, id_type: str = 'auto', max_attempts: int = 60, interval: int = 5) -> Tuple[bool, Dict]:
        """
        智能轮询，支持自动检测ID类型并回退

        Args:
            task_id: 任务ID
            id_type: 'numeric', 'uuid', 'auto'
            max_attempts: 最大尝试次数
            interval: 轮询间隔（秒）

        Returns:
            Tuple[success, data]: 是否成功和响应数据
        """
        print(f"🔄 开始智能轮询任务 {task_id} (类型: {id_type})")

        if id_type == 'auto':
            # 自动检测ID类型
            if task_id.isdigit():
                id_type = 'numeric'
                print(f"🔢 检测到数字格式ID，使用数字轮询")
            elif self.is_uuid_format(task_id):
                id_type = 'uuid'
                print(f"🆔 检测到UUID格式ID，使用UUID轮询")
            else:
                # 尝试先作为数字ID处理
                id_type = 'numeric'
                print(f"❓ 未确定ID格式，尝试数字轮询")

        # 首先尝试指定的类型
        if id_type == 'numeric':
            result, data = self.poll_task_with_numeric_id(task_id, max_attempts, interval)

            # 如果检测到UUID格式错误，提供错误指导
            if result is False and 'NumberFormatException' in str(data):
                print(f"🔄 数字轮询失败，UUID格式ID不被标准轮询API支持")
                # 返回包含指导信息的错误
                return False, self.create_error_response_with_guidance(task_id, data)

            return result, data

        elif id_type == 'uuid':
            # UUID格式的ID需要特殊处理
            print(f"❌ UUID格式的任务ID目前不被轮询API支持")
            return False, self.create_error_response_with_guidance(task_id, {'error': 'UUID format not supported by polling API'})

        else:
            return False, {'error': f'不支持的ID类型: {id_type}'}

    def is_uuid_format(self, value: str) -> bool:
        """检查是否为UUID格式"""
        import re
        uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        return bool(re.match(uuid_pattern, value))

    def get_modelscope_gallery_link(self) -> str:
        """获取ModelScope图片库链接"""
        return "https://www.modelscope.cn/studios"

    def create_error_response_with_guidance(self, task_id: str, error_data: Dict) -> Dict:
        """创建包含指导信息的错误响应"""
        error_response = {
            'success': False,
            'error': '轮询失败',
            'task_id': task_id,
            'guidance': {
                'message': '由于ModelScope API格式变化，无法获取任务结果',
                'suggestions': [
                    '请手动到ModelScope图片库查看生成的图片',
                    '任务可能仍在后台处理中，稍后可能会有结果',
                    '如果问题持续，请检查API配置或联系技术支持'
                ],
                'gallery_link': self.get_modelscope_gallery_link(),
                'task_id': task_id
            },
            'original_error': error_data
        }

        return error_response


def create_task_poller(cookie: str) -> ModelScopeTaskPoller:
    """创建任务轮询器实例"""
    return ModelScopeTaskPoller(cookie)


def poll_task_smart(cookie: str, task_id: str, **kwargs) -> Tuple[bool, Dict]:
    """
    便捷函数：智能轮询任务状态

    Args:
        cookie: ModelScope Cookie
        task_id: 任务ID
        **kwargs: 其他参数传递给poll_task_with_fallback

    Returns:
        Tuple[success, data]: 是否成功和响应数据
    """
    poller = create_task_poller(cookie)
    return poller.poll_task_with_fallback(task_id, **kwargs)


@task_poller_bp.route('/poll_task', methods=['POST'])
def poll_task():
    """智能轮询任务状态端点"""
    data = request.get_json()
    task_id = data.get('task_id')
    id_type = data.get('id_type', 'auto')
    max_attempts = data.get('max_attempts', 60)
    interval = data.get('interval', 5)

    if not task_id:
        return jsonify({'success': False, 'error': '缺少任务ID'})

    try:
        poller = create_task_poller(MODEL_SCOPE_COOKIE)
        success, result_data = poller.poll_task_with_fallback(
            task_id=task_id,
            id_type=id_type,
            max_attempts=max_attempts,
            interval=interval
        )

        if success:
            return jsonify({'success': True, 'data': result_data})
        else:
            # 检查是否需要提供指导信息
            if 'timeout' in result_data or 'NumberFormatException' in str(result_data.get('message', '')):
                guided_response = poller.create_error_response_with_guidance(task_id, result_data)
                return jsonify(guided_response)
            else:
                return jsonify({'success': False, 'error': result_data})

    except Exception as e:
        logging.error(f'智能轮询任务 {task_id} 异常: {e}')
        return jsonify({'success': False, 'error': f'轮询异常: {str(e)}'})


@task_poller_bp.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """兼容性端点：轮询任务状态"""
    try:
        poller = create_task_poller(MODEL_SCOPE_COOKIE)
        success, result_data = poller.poll_task_with_fallback(task_id, max_attempts=1, interval=1)

        if success:
            return jsonify({'status': 'completed', 'result': result_data})
        else:
            return jsonify({'status': 'failed', 'error': result_data})

    except Exception as e:
        logging.error(f"获取任务状态 {task_id} 异常: {e}")
        return jsonify({'status': 'failed', 'error': f'获取任务状态异常: {str(e)}'})