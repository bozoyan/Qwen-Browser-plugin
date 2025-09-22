// API 管理类
class APIManager {
    constructor() {
        this.baseUrl = CONFIG.API.BASE_URL;
        this.timeout = CONFIG.API.TIMEOUT;
        this.pollInterval = CONFIG.API.POLL_INTERVAL;
        this.currentTaskId = null;
    }
    
    /**
     * 发送HTTP请求
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise<Object>} - 响应数据
     */
    async request(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error(CONFIG.ERRORS.TIMEOUT_ERROR);
            }
            
            throw error;
        }
    }
    
    /**
     * 上传文件
     * @param {File} file - 要上传的文件
     * @param {Function} onProgress - 进度回调函数
     * @returns {Promise<Object>} - 上传结果
     */
    async uploadFile(file, onProgress) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            
            const xhr = new XMLHttpRequest();
            
            // 监听上传进度
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    onProgress(percent);
                }
            });
            
            // 监听响应
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (error) {
                        reject(new Error(CONFIG.ERRORS.INVALID_RESPONSE));
                    }
                } else {
                    reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                }
            });
            
            // 监听错误
            xhr.addEventListener('error', () => {
                reject(new Error(CONFIG.ERRORS.NETWORK_ERROR));
            });
            
            // 监听超时
            xhr.addEventListener('timeout', () => {
                reject(new Error(CONFIG.ERRORS.TIMEOUT_ERROR));
            });
            
            // 设置超时时间
            xhr.timeout = this.timeout;
            
            // 发送请求
            xhr.open('POST', `${this.baseUrl}${CONFIG.API.ENDPOINTS.UPLOAD}`);
            xhr.send(formData);
        });
    }
    
    /**
     * 分析图片
     * @param {string} filename - 文件名
     * @param {Object} settings - 设置参数
     * @returns {Promise<Object>} - 分析结果
     */
    async analyzeImage(filename, settings) {
        const url = `${this.baseUrl}${CONFIG.API.ENDPOINTS.ANALYZE}`;
        
        const requestData = {
            filename: filename,
            openai_api_key: settings.openaiKey
        };
        
        return await this.request(url, {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    }
    
    /**
     * 生成图片
     * @param {string} prompt - 提示词
     * @param {Object} settings - 设置参数
     * @returns {Promise<Object>} - 生成结果
     */
    async generateImage(prompt, settings) {
        const url = `${this.baseUrl}${CONFIG.API.ENDPOINTS.GENERATE}`;
        const F_prompt = "feifei,a photo-realistic shoot from a portrait camera angle about a woman,妃妃,";

        const requestData = {
            prompt: F_prompt + prompt,
            model_scope_cookie: settings.modelScopeCookie,
            width: settings.imageWidth,
            height: settings.imageHeight,
            lora_args: CONFIG.DEFAULTS.LORA_ARGS
        };
        
        return await this.request(url, {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    }
    
    /**
     * 获取队列状态
     * @param {string} taskId - 任务ID
     * @returns {Promise<Object>} - 队列状态
     */
    async getQueueStatus(taskId) {
        const url = `${this.baseUrl}${CONFIG.API.ENDPOINTS.QUEUE_STATUS}/${taskId}`;
        return await this.request(url);
    }
    
    /**
     * 获取结果
     * @param {string} taskId - 任务ID
     * @returns {Promise<Object>} - 结果数据
     */
    async getResult(taskId) {
        const url = `${this.baseUrl}${CONFIG.API.ENDPOINTS.RESULT}/${taskId}`;
        return await this.request(url);
    }
    
    /**
     * 轮询任务状态
     * @param {string} taskId - 任务ID
     * @param {Function} onProgress - 进度回调函数
     * @param {Function} onComplete - 完成回调函数
     * @param {Function} onError - 错误回调函数
     */
    async pollTaskStatus(taskId, onProgress, onComplete, onError) {
        this.currentTaskId = taskId;
        
        const poll = async () => {
            try {
                // 检查是否已取消
                if (this.currentTaskId !== taskId) {
                    return;
                }
                
                const status = await this.getQueueStatus(taskId);
                
                if (onProgress) {
                    onProgress(status);
                }
                
                switch (status.status) {
                    case CONFIG.STATUS.COMPLETED:
                        // 获取结果
                        const result = await this.getResult(taskId);
                        if (onComplete) {
                            onComplete(result);
                        }
                        break;
                        
                    case CONFIG.STATUS.FAILED:
                        if (onError) {
                            onError(new Error(status.error || '任务执行失败'));
                        }
                        break;
                        
                    case CONFIG.STATUS.CANCELLED:
                        if (onError) {
                            onError(new Error('任务已取消'));
                        }
                        break;
                        
                    case CONFIG.STATUS.PENDING:
                    case CONFIG.STATUS.PROCESSING:
                        // 继续轮询
                        setTimeout(poll, this.pollInterval);
                        break;
                        
                    default:
                        if (onError) {
                            onError(new Error('未知任务状态: ' + status.status));
                        }
                        break;
                }
                
            } catch (error) {
                if (onError) {
                    onError(error);
                }
            }
        };
        
        // 开始轮询
        poll();
    }
    
    /**
     * 取消当前任务
     */
    cancelCurrentTask() {
        this.currentTaskId = null;
    }
    
    /**
     * 完整的图片处理流程
     * @param {File} file - 图片文件
     * @param {Object} settings - 设置参数
     * @param {Object} callbacks - 回调函数集合
     * @returns {Promise<Object>} - 处理结果
     */
    async processImage(file, settings, callbacks = {}) {
        const {
            onUploadProgress,
            onAnalyzeStart,
            onAnalyzeComplete,
            onGenerateStart,
            onGenerateProgress,
            onGenerateComplete,
            onError
        } = callbacks;
        
        try {
            // 1. 上传文件
            const uploadResult = await this.uploadFile(file, onUploadProgress);
            
            if (!uploadResult.success) {
                throw new Error(uploadResult.error || CONFIG.ERRORS.UPLOAD_FAILED);
            }
            
            // 2. 分析图片
            if (onAnalyzeStart) {
                onAnalyzeStart();
            }
            
            const analyzeResult = await this.analyzeImage(uploadResult.filename, settings);
            
            if (!analyzeResult.success) {
                throw new Error(analyzeResult.error || CONFIG.ERRORS.ANALYZE_FAILED);
            }
            
            if (onAnalyzeComplete) {
                onAnalyzeComplete(analyzeResult);
            }
            
            // 3. 生成图片
            if (onGenerateStart) {
                onGenerateStart();
            }
            
            const generateResult = await this.generateImage(analyzeResult.prompt, settings);
            
            if (!generateResult.success) {
                throw new Error(generateResult.error || CONFIG.ERRORS.GENERATE_FAILED);
            }
            
            // 4. 轮询生成状态
            return new Promise((resolve, reject) => {
                this.pollTaskStatus(
                    generateResult.task_id,
                    onGenerateProgress,
                    (result) => {
                        if (onGenerateComplete) {
                            onGenerateComplete(result);
                        }
                        resolve(result);
                    },
                    (error) => {
                        if (onError) {
                            onError(error);
                        }
                        reject(error);
                    }
                );
            });
            
        } catch (error) {
            if (onError) {
                onError(error);
            }
            throw error;
        }
    }
    
    /**
     * 检查服务器连接
     * @returns {Promise<boolean>} - 连接状态
     */
    async checkConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                timeout: 5000
            });
            
            return response.ok;
            
        } catch (error) {
            return false;
        }
    }
}

// 导出API管理类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIManager;
} else if (typeof window !== 'undefined') {
    window.APIManager = APIManager;
}
