// 主入口文件
class PopupApp {
    constructor() {
        this.uiManager = null;
        this.apiManager = null;
        this.isProcessing = false;
        
        this.init();
    }
    
    /**
     * 初始化应用
     */
    async init() {
        try {
            // 等待DOM加载完成
            if (document.readyState === 'loading') {
                await new Promise(resolve => {
                    document.addEventListener('DOMContentLoaded', resolve);
                });
            }
            
            // 初始化管理器
            this.uiManager = new UIManager();
            this.apiManager = new APIManager();
            
            // 绑定事件
            this.bindEvents();
            
            // 检查服务器连接
            await this.checkServerConnection();
            
            // 应用启动完成

            
        } catch (error) {
            console.error('应用初始化失败:', error);
            if (this.uiManager) {

            }
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 重写UI管理器的处理方法，使用真实的API调用
        const originalHandleAnalyze = this.uiManager.handleAnalyze.bind(this.uiManager);
        this.uiManager.handleAnalyze = this.handleAnalyze.bind(this);
        
        // 监听窗口关闭事件
        window.addEventListener('beforeunload', () => {
            if (this.isProcessing) {
                this.apiManager.cancelCurrentTask();
            }
        });
    }
    
    /**
     * 检查服务器连接
     */
    async checkServerConnection() {
        try {
            const isConnected = await this.apiManager.checkConnection();
            
            if (isConnected) {

            } else {

                this.uiManager.showToast('无法连接到本地服务器', 'warning');
            }
            
        } catch (error) {

        }
    }
    
    /**
     * 处理分析按钮点击（真实API版本）
     */
    async handleAnalyze() {
        if (!this.uiManager.currentImageData) {
            this.uiManager.showToast('请先选择图片', 'warning');
            return;
        }
        
        if (this.isProcessing) {
            this.uiManager.showToast('正在处理中，请稍候', 'warning');
            return;
        }
        
        // 检查设置
        const settings = await this.uiManager.getSettings();
        if (!settings.openaiKey) {
            this.uiManager.showToast(CONFIG.ERRORS.MISSING_API_KEY, 'error');
            this.uiManager.showSettings();
            return;
        }
        
        if (!settings.modelScopeCookie) {
            this.uiManager.showToast(CONFIG.ERRORS.MISSING_COOKIE, 'error');
            this.uiManager.showSettings();
            return;
        }
        
        try {
            this.isProcessing = true;
            
            // 禁用按钮
            this.uiManager.elements.analyzeBtn.disabled = true;
            this.uiManager.elements.analyzeBtn.textContent = '处理中...';
            
            // 开始处理
            await this.processImageWithRealAPI(settings);
            
        } catch (error) {
            this.uiManager.showToast('处理失败: ' + error.message, 'error');

        } finally {
            this.isProcessing = false;
            
            // 恢复按钮
            this.uiManager.elements.analyzeBtn.disabled = false;
            this.uiManager.elements.analyzeBtn.textContent = '反推并生成';
        }
    }
    
    /**
     * 使用真实API处理图片
     */
    async processImageWithRealAPI(settings) {
        const callbacks = {
            // 上传进度
            onUploadProgress: (percent) => {
                this.uiManager.showUploadProgress(percent);

            },
            
            // 分析开始
            onAnalyzeStart: () => {
                this.uiManager.hideUploadProgress();

                this.uiManager.showQueueInfo('正在分析图片内容...', 0);
            },
            
            // 分析完成
            onAnalyzeComplete: (result) => {

            },
            
            // 生成开始
            onGenerateStart: () => {

                this.uiManager.updateQueueInfo('正在生成新图片...', 0);
            },
            
            // 生成进度
            onGenerateProgress: (status) => {
                const progress = status.progress || 0;
                this.uiManager.updateQueueProgress(progress);
                
                if (status.message) {
                    this.uiManager.updateQueueInfo(status.message, progress);
                }
                

            },
            
            // 生成完成
            onGenerateComplete: (result) => {
                this.uiManager.hideQueueInfo();

                
                if (result.images && result.images.length > 0) {
                    this.uiManager.showGeneratedImages(result.images);
                    this.uiManager.showToast(`成功生成 ${result.images.length} 张图片`, 'success');
                } else {
                    this.uiManager.showToast('未生成任何图片', 'warning');
                }
            },
            
            // 错误处理
            onError: (error) => {
                this.uiManager.hideQueueInfo();
                this.uiManager.hideUploadProgress();

            }
        };
        
        // 调用API处理图片
        await this.apiManager.processImage(
            this.uiManager.currentImageData,
            settings,
            callbacks
        );
    }
    
    /**
     * 获取应用状态
     */
    getStatus() {
        return {
            isProcessing: this.isProcessing,
            hasImage: !!this.uiManager?.currentImageData,
            generatedCount: this.uiManager?.generatedImages?.length || 0
        };
    }
}

// 全局应用实例
let popupApp = null;

// 当DOM加载完成时初始化应用
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        popupApp = new PopupApp();
    });
} else {
    popupApp = new PopupApp();
}

// 导出应用类（用于调试）
if (typeof window !== 'undefined') {
    window.PopupApp = PopupApp;
    window.getPopupApp = () => popupApp;
}