// 工具函数库
class Utils {
    /**
     * 验证文件类型和大小
     * @param {File} file - 要验证的文件
     * @returns {Object} - 验证结果 {valid: boolean, error: string}
     */
    static validateFile(file) {
        if (!file) {
            return { valid: false, error: '请选择文件' };
        }
        
        // 检查文件大小
        if (file.size > CONFIG.UPLOAD.MAX_SIZE) {
            return { valid: false, error: CONFIG.ERRORS.FILE_TOO_LARGE };
        }
        
        // 检查文件类型
        if (!CONFIG.UPLOAD.ALLOWED_TYPES.includes(file.type)) {
            return { valid: false, error: CONFIG.ERRORS.INVALID_FILE_TYPE };
        }
        
        // 检查文件扩展名
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!CONFIG.UPLOAD.ALLOWED_EXTENSIONS.includes(extension)) {
            return { valid: false, error: CONFIG.ERRORS.INVALID_FILE_TYPE };
        }
        
        return { valid: true };
    }
    
    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     * @returns {string} - 格式化后的大小
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * 生成唯一ID
     * @returns {string} - 唯一ID
     */
    static generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    /**
     * 格式化时间戳
     * @param {number} timestamp - 时间戳
     * @returns {string} - 格式化后的时间
     */
    static formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('zh-CN', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间
     * @returns {Function} - 防抖后的函数
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 限制时间
     * @returns {Function} - 节流后的函数
     */
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    /**
     * 深拷贝对象
     * @param {Object} obj - 要拷贝的对象
     * @returns {Object} - 拷贝后的对象
     */
    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => Utils.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = Utils.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    }
    
    /**
     * 检查是否为有效的URL
     * @param {string} url - 要检查的URL
     * @returns {boolean} - 是否有效
     */
    static isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
    
    /**
     * 转义HTML字符
     * @param {string} text - 要转义的文本
     * @returns {string} - 转义后的文本
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 创建图片预览URL
     * @param {File} file - 图片文件
     * @returns {Promise<string>} - 预览URL
     */
    static createImagePreview(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    /**
     * 压缩图片
     * @param {File} file - 原始图片文件
     * @param {number} maxWidth - 最大宽度
     * @param {number} maxHeight - 最大高度
     * @param {number} quality - 压缩质量 (0-1)
     * @returns {Promise<Blob>} - 压缩后的图片
     */
    static compressImage(file, maxWidth = 800, maxHeight = 600, quality = 0.8) {
        return new Promise((resolve, reject) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.onload = () => {
                // 计算新尺寸
                let { width, height } = img;
                
                if (width > height) {
                    if (width > maxWidth) {
                        height = (height * maxWidth) / width;
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width = (width * maxHeight) / height;
                        height = maxHeight;
                    }
                }
                
                canvas.width = width;
                canvas.height = height;
                
                // 绘制压缩后的图片
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob(resolve, file.type, quality);
            };
            
            img.onerror = reject;
            img.src = URL.createObjectURL(file);
        });
    }
    
    /**
     * 等待指定时间
     * @param {number} ms - 等待时间 (毫秒)
     * @returns {Promise} - Promise对象
     */
    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * 重试函数
     * @param {Function} fn - 要重试的函数
     * @param {number} retries - 重试次数
     * @param {number} delay - 重试间隔 (毫秒)
     * @returns {Promise} - Promise对象
     */
    static async retry(fn, retries = 3, delay = 1000) {
        try {
            return await fn();
        } catch (error) {
            if (retries > 0) {
                await Utils.sleep(delay);
                return Utils.retry(fn, retries - 1, delay);
            }
            throw error;
        }
    }
}

// 导出工具类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
} else if (typeof window !== 'undefined') {
    window.Utils = Utils;
}