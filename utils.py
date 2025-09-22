import os
import json
import logging
import re
import uuid
from config import ALLOWED_EXTENSIONS

def allowed_file(filename):
    """检查文件扩展名是否被允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_csrf_token(cookie_string):
    """从cookie字符串中提取csrf-token"""
    if not cookie_string:
        return None
    match = re.search(r'csrfToken=([^;]+)', cookie_string)
    if match:
        return match.group(1)
    return None

def generate_trace_id():
    """生成一个唯一的trace-id"""
    return str(uuid.uuid4())