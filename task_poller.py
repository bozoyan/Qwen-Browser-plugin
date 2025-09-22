from flask import request, jsonify, Blueprint
from config import MODEL_SCOPE_COOKIE
import logging
import time
import requests
import json

task_poller_bp = Blueprint('task_poller', __name__)

@task_poller_bp.route('/poll_task', methods=['POST'])
def poll_task():
    """轮询任务状态"""
    data = request.get_json()
    task_id = data.get('task_id')

    if not task_id:
        return jsonify({'success': False, 'error': '缺少任务ID'})

    base_poll_url = 'https://www.modelscope.cn/api/v1/muse/predict/task/status'
    poll_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Cookie': MODEL_SCOPE_COOKIE,
        'Referer': 'https://www.modelscope.cn/aigc/imageGeneration',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    try:
        poll_url = f'{base_poll_url}?taskId={task_id}'
        poll_response = requests.get(poll_url, headers=poll_headers, timeout=10)
        poll_response.raise_for_status()
        response_json = poll_response.json()

        logging.info(f'轮询任务 {task_id} 状态: {response_json}')

        if response_json.get('Success') and response_json.get('Data'):
            task_data = response_json['Data'].get('data', {})
            status = task_data.get('status', '')

            if status == 'COMPLETED':
                images = [item.get('url') for item in task_data.get('predictResult', []) if item and item.get('url')]
                if images:
                    return jsonify({'success': True, 'status': 'COMPLETED', 'images': images})
                else:
                    return jsonify({'success': False, 'status': 'FAILED', 'error': '图片生成成功但未找到图片URL'})
            elif status == 'FAILED':
                error_msg = task_data.get('errorMsg', '未知错误')
                return jsonify({'success': False, 'status': 'FAILED', 'error': error_msg})
            else: # PROCESSING, QUEUING, PENDING
                progress = task_data.get('progress', {})
                percent = progress.get('percent', 0)
                detail = progress.get('detail', '正在处理中...')
                return jsonify({'success': True, 'status': status, 'progress': percent, 'message': detail})
        else:
            return jsonify({'success': False, 'error': '轮询API返回格式异常'})

    except requests.exceptions.RequestException as e:
        logging.error(f'轮询任务状态时出错: {e}')
        return jsonify({'success': False, 'error': f'轮询任务状态时出错: {e}'})

@task_poller_bp.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Polls the ModelScope API for the status of a given task ID."""
    try:
        cookie = MODEL_SCOPE_COOKIE
        if not cookie:
            return jsonify({'status': 'failed', 'error': 'Cookie not configured'})

        poll_url = f'https://www.modelscope.cn/api/v1/muse/predict/task/status?taskId={task_id}'
        poll_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Cookie': cookie,
            'Referer': 'https://www.modelscope.cn/aigc/imageGeneration',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }

        poll_response = requests.get(poll_url, headers=poll_headers, timeout=10)
        poll_response.raise_for_status()
        response_json = poll_response.json()

        logging.info(f'Polling task {task_id} status: {response_json}')

        if response_json.get('Success') and response_json.get('Data'):
            task_data = response_json.get('Data', {}).get('data', {})
            status = task_data.get('status', '')

            if status == 'COMPLETED':
                images = [item.get('url') for item in task_data.get('predictResult', []) if item and item.get('url')]
                if images:
                    return jsonify({'status': 'completed', 'result': {'image_url': images[0]}})
                else:
                    return jsonify({'status': 'failed', 'error': 'Image generation succeeded but no image URL found'})
            elif status == 'FAILED':
                error_msg = task_data.get('errorMsg', 'Unknown error')
                return jsonify({'status': 'failed', 'error': error_msg})
            else: # PROCESSING, QUEUING, PENDING
                return jsonify({'status': status})
        else:
            return jsonify({'status': 'failed', 'error': 'Polling API returned an unexpected format'})

    except requests.exceptions.RequestException as e:
        logging.error(f"Error polling task status for {task_id}: {e}")
        return jsonify({'status': 'failed', 'error': f'Error polling task status: {e}'})