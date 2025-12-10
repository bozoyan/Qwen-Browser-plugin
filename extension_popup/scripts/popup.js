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
        console.log('🚀 [Popup] 开始初始化Chrome扩展...');

        try {
            // 等待DOM加载完成
            if (document.readyState === 'loading') {
                console.log('⏳ [Popup] 等待DOM加载完成...');
                await new Promise(resolve => {
                    document.addEventListener('DOMContentLoaded', resolve);
                });
            }

            console.log('✅ [Popup] DOM加载完成');

            // 初始化管理器
            this.uiManager = new UIManager();
            this.apiManager = new APIManager();
            console.log('✅ [Popup] 管理器初始化完成');

            // 绑定事件
            this.bindEvents();
            console.log('✅ [Popup] 事件绑定完成');

            // 检查服务器连接
            await this.checkServerConnection();
            console.log('✅ [Popup] 服务器连接检查完成');

            // 应用启动完成
            console.log('🎉 [Popup] 应用初始化完成！');

        } catch (error) {
            console.error('❌ [Popup] 应用初始化失败:', error);
            if (this.uiManager) {
                this.uiManager.showToast('应用初始化失败: ' + error.message, 'error');
            }
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        console.log('🔧 [Popup] 绑定事件处理方法...');

        // 重写UI管理器的处理方法，使用真实的API调用
        const originalHandleAnalyze = this.uiManager.handleAnalyze.bind(this.uiManager);
        this.uiManager.handleAnalyze = this.handleAnalyze.bind(this);

        console.log('✅ [Popup] UI管理器的handleAnalyze方法已重写为popup.js中的方法');

        // 验证重写是否成功
        if (this.uiManager.handleAnalyze === this.handleAnalyze) {
            console.log('✅ [Popup] handleAnalyze方法重写成功');
        } else {
            console.error('❌ [Popup] handleAnalyze方法重写失败');
        }

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
        console.log('🚀 [Popup] 开始处理图片分析请求');

        if (!this.uiManager.currentImageData) {
            console.log('❌ [Popup] 没有选择图片');
            this.uiManager.showToast('请先选择图片', 'warning');
            return;
        }

        if (this.isProcessing) {
            console.log('⏳ [Popup] 正在处理中，跳过重复请求');
            this.uiManager.showToast('正在处理中，请稍候', 'warning');
            return;
        }

        // 检查设置
        console.log('🔧 [Popup] 获取设置信息...');
        const settings = await this.uiManager.getSettings();
        console.log('📋 [Popup] 获取到的设置:', {
            hasOpenAIKey: !!settings.openaiKey,
            hasCookie: !!settings.modelScopeCookie,
            imageSize: `${settings.imageWidth}x${settings.imageHeight}`,
            numImages: settings.numImages,
            enableHires: settings.enableHires,
            hasCheckpoint: !!settings.checkpoint
        });

        if (!settings.openaiKey) {
            console.log('❌ [Popup] 缺少 OpenAI API Key');
            this.uiManager.showToast('请先配置 OpenAI API Key', 'error');
            this.uiManager.showSettings();
            return;
        }

        if (!settings.modelScopeCookie) {
            console.log('❌ [Popup] 缺少 ModelScope Cookie');
            this.uiManager.showToast('请先配置 ModelScope Cookie', 'error');
            this.uiManager.showSettings();
            return;
        }

        try {
            console.log('✅ [Popup] 开始处理图片...');
            this.isProcessing = true;

            // 禁用按钮
            this.uiManager.elements.analyzeBtn.disabled = true;
            this.uiManager.elements.analyzeBtn.textContent = '处理中...';

            console.log('🔄 [Popup] 调用图片处理API...');
            // 开始处理
            await this.processImageWithRealAPI(settings);
            console.log('✅ [Popup] 图片处理完成');

        } catch (error) {
            console.error('❌ [Popup] 处理失败:', error);
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
                console.log(`📊 [Popup] 上传进度: ${percent}%`);
            },

            // 分析开始
            onAnalyzeStart: () => {
                this.uiManager.hideUploadProgress();
                this.uiManager.showQueueInfo('正在分析图片内容...', 20);
                console.log('🔍 [Popup] 开始分析图片');
            },

            // 分析完成
            onAnalyzeComplete: (result) => {
                this.uiManager.updateQueueInfo('图片分析完成，开始生成...', 40);
                console.log('✅ [Popup] 图片分析完成');
            },

            // 生成开始
            onGenerateStart: () => {
                this.uiManager.updateQueueInfo('正在生成新图片...', 60);
                console.log('🎨 [Popup] 开始生成图片');
            },

            // 生成进度
            onGenerateProgress: (status) => {
                const progress = status.progress || 80;
                this.uiManager.updateQueueProgress(progress);
                console.log(`⏳ [Popup] 生成进度: ${progress}%`);

                if (status.message) {
                    this.uiManager.updateQueueInfo(status.message, progress);
                } else {
                    this.uiManager.updateQueueInfo('正在生成图片，请稍候...', progress);
                }
            },

            // 生成完成
            onGenerateComplete: (result) => {
                this.uiManager.hideQueueInfo();
                console.log('🎉 [Popup] 生成完成，处理结果:', result);

                if (result.success && result.images && result.images.length > 0) {
                    const prompt = result.prompt || '图片反推完成';
                    this.uiManager.showGeneratedImages(result.images, prompt);
                    this.uiManager.showToast(`成功生成 ${result.images.length} 张图片`, 'success');
                    console.log(`✅ [Popup] 显示 ${result.images.length} 张生成图片`);
                } else {
                    this.uiManager.showToast('未生成任何图片', 'warning');
                    console.log('⚠️ [Popup] 未生成任何图片');
                }
            },

            // 错误处理
            onError: (error) => {
                this.uiManager.hideQueueInfo();
                this.uiManager.hideUploadProgress();
                this.uiManager.showToast('处理失败: ' + error.message, 'error');
                console.error('❌ [Popup] 处理失败:', error);
            }
        };

        try {
            // 调用API处理图片
            await this.apiManager.processImage(
                this.uiManager.currentImageData,
                settings,
                callbacks
            );
        } catch (error) {
            this.uiManager.showToast('处理失败: ' + error.message, 'error');
            console.error('图片处理失败:', error);
        }
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