// API 管理类
class APIManager {
    constructor() {
        this.baseUrl = CONFIG.API.BASE_URL;
        this.timeout = CONFIG.API.TIMEOUT;
        this.pollInterval = CONFIG.API.POLL_INTERVAL;
        this.currentTaskId = null;
        this.currentRequest = null;
        this.isCancelled = false;
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
     * @param {string} imageUrl - 图片URL
     * @param {Object} settings - 设置参数
     * @returns {Promise<Object>} - 分析结果
     */
    async analyzeImage(imageUrl, settings) {
        const url = `${this.baseUrl}${CONFIG.API.ENDPOINTS.REVERSE_IMAGE}`;

        const requestData = {
            image_url: imageUrl
        };

        // 如果有OpenAI API Key，则添加到请求中
        if (settings.openaiKey) {
            requestData.openai_api_key = settings.openaiKey;
        }

        return await this.request(url, {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    }
    
    /**
     * 加载模型数据
     * @returns {Promise<Object>} - 模型数据
     */
    async loadModels() {
        try {
            // 从本地服务器加载模型配置
            const [checkpointData, loraData] = await Promise.all([
                this.request(`${this.baseUrl}/comfyui_modelscope/checkpoint.json`),
                this.request(`${this.baseUrl}/comfyui_modelscope/loraArgs.json`)
            ]);

            return {
                checkpoints: checkpointData,
                loras: loraData
            };
        } catch (error) {
            console.error('加载模型数据失败:', error);
            // 如果从服务器加载失败，使用默认的模型数据
            return this.getDefaultModels();
        }
    }

    /**
     * 获取默认模型数据
     * @returns {Object} - 默认模型数据
     */
    getDefaultModels() {
        return {
            checkpoints: [
                {
                    "CheckpointName": "Qwen_Image_v1",
                    "checkpointModelVersionId": 275167,
                    "checkpointShowInfo": "Qwen_Image_v1.safetensors",
                    "numInferenceSteps": 50,
                    "guidanceScale": 4
                },
                {
                    "CheckpointName": "造相-Z-Image-Turbo_master",
                    "checkpointModelVersionId": 469191,
                    "checkpointShowInfo": "造相-Z-Image-Turbo_master.safetensors",
                    "numInferenceSteps": 9,
                    "guidanceScale": 2.5
                }
            ],
            loras: [
                {
                    "LoraName": "FEIFEI",
                    "modelVersionId": 310150,
                    "scale": 1
                },
                {
                    "LoraName": "FEIFEI_V2",
                    "modelVersionId": 313167,
                    "scale": 1
                },
                {
                    "LoraName": "GUA",
                    "modelVersionId": 332699,
                    "scale": 1
                },
                {
                    "LoraName": "GUA_V2",
                    "modelVersionId": 334516,
                    "scale": 1
                },
                {
                    "LoraName": "GUA_V8",
                    "modelVersionId": 346999,
                    "scale": 1
                },
                {
                    "LoraName": "GUA_V9",
                    "modelVersionId": 365553,
                    "scale": 1
                }
            ]
        };
    }

    /**
     * 生成图片
     * @param {string} prompt - 提示词
     * @param {Object} settings - 设置参数
     * @returns {Promise<Object>} - 生成结果
     */
    async generateImage(prompt, settings) {
        const url = `${this.baseUrl}${CONFIG.API.ENDPOINTS.GENERATE}`;
        const F_prompt = "feifei,a photo-realistic shoot from a portrait camera angle about a young woman,big boobs,妃妃,";

        // 构建LoRA参数 - 使用默认的LoRA如果用户没有选择
        let loraArgs = CONFIG.DEFAULTS.LORA_ARGS || [{ modelVersionId: 310150, scale: 1 }];

        // 如果用户选择了LoRA模型，则使用用户选择的
        const userLoras = [];
        for (let i = 1; i <= 4; i++) {
            const loraKey = `lora${i}`;
            if (settings[loraKey] && settings[loraKey].modelVersionId) {
                userLoras.push({
                    modelVersionId: settings[loraKey].modelVersionId,
                    scale: settings[loraKey].scale || 1
                });
            }
        }
        if (userLoras.length > 0) {
            loraArgs = userLoras;
        }

        // 构建checkpoint参数
        let checkpointModelVersionId = 275167; // 默认值
        let checkpointShowInfo = "Qwen_Image_v1.safetensors"; // 默认值
        let numInferenceSteps = 50; // 默认值
        let guidanceScale = 4.0; // 默认值

        if (settings.checkpoint && settings.checkpoint.checkpointModelVersionId) {
            checkpointModelVersionId = settings.checkpoint.checkpointModelVersionId;
            checkpointShowInfo = settings.checkpoint.checkpointShowInfo || settings.checkpoint.CheckpointName;
            numInferenceSteps = settings.checkpoint.numInferenceSteps || 50;
            guidanceScale = settings.checkpoint.guidanceScale || 4.0;
        }

        const requestData = {
            prompt: F_prompt + prompt,
            cookie: settings.modelScopeCookie,
            width: settings.imageWidth || CONFIG.DEFAULTS.IMAGE_WIDTH,
            height: settings.imageHeight || CONFIG.DEFAULTS.IMAGE_HEIGHT
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
        console.log('🛑 [API] 取消当前任务');
        this.isCancelled = true;
        this.currentTaskId = null;

        // 如果有正在进行的请求，取消它
        if (this.currentRequest) {
            console.log('🚫 [API] 取消当前HTTP请求');
            this.currentRequest.abort();
            this.currentRequest = null;
        }
    }
    
    /**
     * 完整的图片处理流程（使用新的综合端点）
     * @param {File} file - 图片文件
     * @param {Object} settings - 设置参数
     * @param {Object} callbacks - 回调函数集合
     * @returns {Promise<Object>} - 处理结果
     */
    async processImage(file, settings, callbacks = {}) {
        console.log('🚀 [API] 开始使用综合端点处理图片');
        console.log('📁 [API] 图片文件:', file.name, file.size, file.type);

        const {
            onUploadProgress,
            onAnalyzeStart,
            onAnalyzeComplete,
            onGenerateStart,
            onGenerateProgress,
            onGenerateComplete,
            onError
        } = callbacks;

        // 重置取消状态
        this.isCancelled = false;

        try {
            console.log('📡 [API] 调用综合端点:', `${this.baseUrl}${CONFIG.API.ENDPOINTS.PROCESS_COMPLETE}`);

            // 创建FormData对象
            const formData = new FormData();
            formData.append('file', file);

            // 添加JSON数据部分
            const jsonData = {
                cookie: settings.modelScopeCookie,
                width: settings.imageWidth || CONFIG.DEFAULTS.IMAGE_WIDTH,
                height: settings.imageHeight || CONFIG.DEFAULTS.IMAGE_HEIGHT,
                openai_api_key: settings.openaiKey
            };
            formData.append('json_data', JSON.stringify(jsonData));

            console.log('📋 [API] 请求参数:', {
                hasFile: true,
                hasCookie: !!settings.modelScopeCookie,
                imageSize: `${settings.imageWidth}x${settings.imageHeight}`,
                hasOpenAIKey: !!settings.openaiKey
            });

            // 创建XMLHttpRequest来支持上传进度和长时间请求
            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                // 保存当前请求引用以便取消
                this.currentRequest = xhr;

                // 监听上传进度
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable && onUploadProgress) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        onUploadProgress(percent);
                        console.log(`📊 [API] 上传进度: ${percent}%`);
                    }
                });

                // 监听响应
                xhr.addEventListener('load', () => {
                    console.log('📥 [API] 综合端点响应:', xhr.status);
                    console.log('📄 [API] 响应内容:', xhr.responseText);

                    // 清理当前请求引用
                    this.currentRequest = null;

                    // 检查是否已被取消
                    if (this.isCancelled) {
                        console.log('🚫 [API] 请求已完成但任务已被取消');
                        reject(new Error('任务已取消'));
                        return;
                    }

                    try {
                        if (xhr.status === 200) {
                            const response = JSON.parse(xhr.responseText);

                            if (response.success) {
                                console.log('✅ [API] 综合处理成功');
                                console.log(`📝 [API] 反推文字长度: ${response.prompt?.length || 0}`);
                                console.log(`🖼️ [API] 生成图片数量: ${response.images?.length || 0}`);

                                const result = {
                                    success: true,
                                    images: response.images,
                                    prompt: response.prompt,
                                    task_id: response.task_id
                                };

                                if (onGenerateComplete) {
                                    onGenerateComplete(result);
                                }

                                resolve(result);
                            } else {
                                console.error('❌ [API] 综合处理失败:', response.error);
                                if (onError) {
                                    onError(new Error(response.error));
                                }
                                reject(new Error(response.error));
                            }
                        } else {
                            console.error('❌ [API] HTTP错误:', xhr.status);
                            if (onError) {
                                onError(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                            }
                            reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
                        }
                    } catch (error) {
                        console.error('❌ [API] 响应解析失败:', error);
                        if (onError) {
                            onError(error);
                        }
                        reject(error);
                    }
                });

                // 监听错误
                xhr.addEventListener('error', () => {
                    console.error('❌ [API] 网络错误');

                    // 清理当前请求引用
                    this.currentRequest = null;

                    if (onError) {
                        onError(new Error(CONFIG.ERRORS.NETWORK_ERROR));
                    }
                    reject(new Error(CONFIG.ERRORS.NETWORK_ERROR));
                });

                // 监听超时
                xhr.addEventListener('timeout', () => {
                    console.error('❌ [API] 请求超时');

                    // 清理当前请求引用
                    this.currentRequest = null;

                    if (onError) {
                        onError(new Error(CONFIG.ERRORS.TIMEOUT_ERROR));
                    }
                    reject(new Error(CONFIG.ERRORS.TIMEOUT_ERROR));
                });

                // 设置超时时间（5分钟，因为生成图片需要时间）
                xhr.timeout = 300000;

                // 发送请求
                xhr.open('POST', `${this.baseUrl}${CONFIG.API.ENDPOINTS.PROCESS_COMPLETE}`);
                xhr.send(formData);

                console.log('🚀 [API] 请求已发送，等待响应...');
            });

        } catch (error) {
            console.error('💥 [API] 综合处理异常:', error);
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
