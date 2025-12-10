// 浏览器插件配置文件
const CONFIG = {
    // API 配置
    API: {
        // 本地服务器地址 (需要先启动 web_app.py)
        BASE_URL: 'http://localhost:8005',
        
        // API 端点
        ENDPOINTS: {
            UPLOAD: '/upload',
            ANALYZE: '/analyze_from_url',
            GENERATE: '/api/generate_image',
            REVERSE_IMAGE: '/reverse_image',
            PROCESS_COMPLETE: '/process_image_complete',  // 新增的综合端点
            POLL_TASK: '/poll_task',
            TASK_STATUS: '/task_status'
        },
        
        // 请求超时时间 (毫秒)
        TIMEOUT: 30000,
        
        // 轮询间隔 (毫秒)
        POLL_INTERVAL: 2000
    },
    
    // 默认设置
    DEFAULTS: {
        // OpenAI API Key (可在设置中修改)
        OPENAI_API_KEY: '',
        
        // ModelScope Cookie (可在设置中修改)
        MODEL_SCOPE_COOKIE: '',
        
        // 图片生成参数
        IMAGE_WIDTH: 928,
        IMAGE_HEIGHT: 1664,
        
        // LoRA 参数
        LORA_ARGS: [
            { modelVersionId: 310150, scale: 1 }
            // { modelVersionId: 313167, scale: 1 }
        ]
    },
    
    // 文件上传配置
    UPLOAD: {
        // 允许的文件类型
        ALLOWED_TYPES: ['image/webp','image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp'],
        
        // 允许的文件扩展名
        ALLOWED_EXTENSIONS: ['.webp','.png', '.jpg', '.jpeg', '.gif', '.bmp'],
        
        // 最大文件大小 (字节)
        MAX_SIZE: 16 * 1024 * 1024, // 16MB
        
        // 文件名验证正则
        FILENAME_REGEX: /^[a-zA-Z0-9._-]+$/
    },
    
    // UI 配置
    UI: {
        // Toast 显示时间 (毫秒)
        TOAST_DURATION: 3000,
        
        // 动画持续时间 (毫秒)
        ANIMATION_DURATION: 300,
        
        // 缩略图大小
        THUMBNAIL_SIZE: 40,
        
        // 主预览区域高度
        PREVIEW_HEIGHT: 200
    },
    
    // 存储键名
    STORAGE_KEYS: {
        OPENAI_API_KEY: 'openai_api_key',
        MODEL_SCOPE_COOKIE: 'model_scope_cookie',
        IMAGE_WIDTH: 'image_width',
        IMAGE_HEIGHT: 'image_height',
        SETTINGS: 'extension_settings'
    },
    
    // 错误消息
    ERRORS: {
        FILE_TOO_LARGE: '文件大小超过限制 (最大 16MB)',
        INVALID_FILE_TYPE: '不支持的文件类型',
        UPLOAD_FAILED: '文件上传失败',
        ANALYZE_FAILED: '图片分析失败',
        GENERATE_FAILED: '图片生成失败',
        NETWORK_ERROR: '网络连接错误',
        SERVER_ERROR: '服务器错误',
        TIMEOUT_ERROR: '请求超时',
        INVALID_RESPONSE: '服务器响应无效',
        MISSING_API_KEY: '请先在设置中配置 OpenAI API Key',
        MISSING_COOKIE: '请先在设置中配置 ModelScope Cookie'
    },
    
    // 成功消息
    SUCCESS: {
        UPLOAD_COMPLETE: '文件上传成功',
        ANALYZE_COMPLETE: '图片分析完成',
        GENERATE_COMPLETE: '图片生成完成',
        SETTINGS_SAVED: '设置保存成功',
        SETTINGS_RESET: '设置重置成功'
    },
    
    // 状态码
    STATUS: {
        PENDING: 'pending',
        PROCESSING: 'processing',
        COMPLETED: 'completed',
        FAILED: 'failed',
        CANCELLED: 'cancelled'
    },
    
    // 分辨率配置
    RESOLUTIONS: {
        "SM": {
            "21:9": {"width": 1024, "height": 394},
            "16:9": {"width": 1024, "height": 576},
            "4:3": {"width": 1024, "height": 768},
            "1:1": {"width": 1024, "height": 1024},
            "3:4": {"width": 768, "height": 1024},
            "9:16": {"width": 576, "height": 1024}
        },
        "HD": {
            "1:1": {"width": 1328, "height": 1328},
            "2:3": {"width": 1056, "height": 1584},
            "3:4": {"width": 1104, "height": 1472},
            "4:3": {"width": 1472, "height": 1104},
            "3:2": {"width": 1584, "height": 1056},
            "16:9": {"width": 1664, "height": 936},
            "9:16": {"width": 936, "height": 1664}
        },
        "2k": {
            "1:1": {"width": 2048, "height": 2048},
            "2:3": {"width": 1664, "height": 2496},
            "3:4": {"width": 1728, "height": 2304},
            "4:3": {"width": 2304, "height": 1728},
            "3:2": {"width": 2496, "height": 1664},
            "16:9": {"width": 2560, "height": 1440},
            "9:16": {"width": 1440, "height": 2560}
        }
    },

    // 日志级别
    LOG_LEVELS: {
        INFO: 'info',
        SUCCESS: 'success',
        WARNING: 'warning',
        ERROR: 'error'
    }
};

// 导出配置 (兼容不同的模块系统)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}
