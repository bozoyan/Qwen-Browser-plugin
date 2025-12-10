#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from flask import Flask, send_from_directory, request, make_response
from flask_cors import CORS
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, OPENAI_API_KEY
from routes import main_bp


from task_poller import task_poller_bp

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    app.secret_key = 'a_very_secret_key'  # 使用一个固定的密钥

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            res = make_response()
            res.headers['Access-Control-Allow-Origin'] = '*'
            res.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            res.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
            return res

    # 从config.py加载配置
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['OPENAI_API_KEY'] = OPENAI_API_KEY

    # 确保上传文件夹存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # 注册蓝图
    app.register_blueprint(main_bp)

    app.register_blueprint(task_poller_bp)

    # 添加uploads目录的静态文件服务
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # 添加comfyui模型配置文件的静态服务
    @app.route('/comfyui_modelscope/<path:filename>')
    def comfyui_modelscope_file(filename):
        # 构建comfyui_modelscope目录的路径
        comfyui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comfyui_modelscope')
        return send_from_directory(comfyui_dir, filename)

    return app



if __name__ == '__main__':

    app = create_app()
    app.run(host='0.0.0.0', port=8005, debug=True)
