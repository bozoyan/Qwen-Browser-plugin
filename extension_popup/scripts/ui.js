// UI 管理类
class UIManager {
    constructor() {
        this.elements = {};
        this.currentImageData = null;
        this.generatedImages = [];
        this.selectedThumbnail = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
    }
    
    /**
     * 初始化DOM元素引用
     */
    initializeElements() {
        this.elements = {
            // 文件上传相关
            fileDropArea: document.getElementById('fileDropArea'),
            fileInput: document.getElementById('fileInput'),
            dropPlaceholder: document.getElementById('dropPlaceholder'),
            imagePreview: document.getElementById('imagePreview'),
            previewImg: document.getElementById('previewImg'),
            
            // 进度相关
            uploadProgress: document.getElementById('uploadProgress'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            
            // 按钮
            analyzeBtn: document.getElementById('analyzeBtn'),
            settingsBtn: document.getElementById('settingsBtn'),
            
            // 结果显示
            queueInfo: document.getElementById('queueInfo'),
            queueDetail: document.getElementById('queueDetail'),
            queueProgress: document.getElementById('queueProgress'),
            mainPreview: document.getElementById('mainPreview'),
            thumbnailsContainer: document.getElementById('thumbnailsContainer'),
            

            
            // 设置面板
            settingsPanel: document.getElementById('settingsPanel'),
            closeSettings: document.getElementById('closeSettings'),
            openaiKey: document.getElementById('openaiKey'),
            modelScopeCookie: document.getElementById('modelScopeCookie'),
            imageWidth: document.getElementById('imageWidth'),
            imageHeight: document.getElementById('imageHeight'),
            saveSettings: document.getElementById('saveSettings'),
            resetSettings: document.getElementById('resetSettings'),
            
            // Toast容器
            toastContainer: document.getElementById('toastContainer')
        };
    }
    
    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 文件拖放事件
        this.elements.fileDropArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.elements.fileDropArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.elements.fileDropArea.addEventListener('drop', this.handleDrop.bind(this));
        this.elements.fileDropArea.addEventListener('click', () => this.elements.fileInput.click());
        
        // 文件选择事件
        this.elements.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // 按钮事件
        this.elements.analyzeBtn.addEventListener('click', this.handleAnalyze.bind(this));
        this.elements.settingsBtn.addEventListener('click', this.showSettings.bind(this));
        this.elements.closeSettings.addEventListener('click', this.hideSettings.bind(this));
        this.elements.saveSettings.addEventListener('click', this.saveSettings.bind(this));
        this.elements.resetSettings.addEventListener('click', this.resetSettings.bind(this));
        
        // 主预览区域点击事件
        this.elements.mainPreview.addEventListener('click', this.handleMainPreviewClick.bind(this));
    }
    
    /**
     * 处理拖拽悬停
     */
    handleDragOver(e) {
        e.preventDefault();
        this.elements.fileDropArea.classList.add('active');
    }
    
    /**
     * 处理拖拽离开
     */
    handleDragLeave(e) {
        e.preventDefault();
        this.elements.fileDropArea.classList.remove('active');
    }
    
    /**
     * 处理文件拖放
     */
    handleDrop(e) {
        e.preventDefault();
        this.elements.fileDropArea.classList.remove('active');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }
    
    /**
     * 处理文件选择
     */
    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }
    
    /**
     * 处理文件
     */
    async handleFile(file) {
        // 验证文件
        const validation = Utils.validateFile(file);
        if (!validation.valid) {
            this.showToast(validation.error, 'error');
            return;
        }
        
        try {
            // 显示图片预览
            const previewUrl = await Utils.createImagePreview(file);
            this.showImagePreview(previewUrl);
            
            // 保存文件数据
            this.currentImageData = file;
            
            // 启用分析按钮
            this.elements.analyzeBtn.disabled = false;
            
            // 记录日志

            
        } catch (error) {
            this.showToast('图片预览失败', 'error');

        }
    }
    
    /**
     * 显示图片预览
     */
    showImagePreview(url) {
        this.elements.previewImg.src = url;
        this.elements.dropPlaceholder.style.display = 'none';
        this.elements.imagePreview.style.display = 'flex';
    }
    
    /**
     * 隐藏图片预览
     */
    hideImagePreview() {
        this.elements.previewImg.src = '';
        this.elements.dropPlaceholder.style.display = 'block';
        this.elements.imagePreview.style.display = 'none';
    }
    
    /**
     * 处理分析按钮点击
     */
    async handleAnalyze() {
        if (!this.currentImageData) {
            this.showToast('请先选择图片', 'warning');
            return;
        }
        
        // 检查设置
        const settings = await this.getSettings();
        if (!settings.openaiKey) {
            this.showToast(CONFIG.ERRORS.MISSING_API_KEY, 'error');
            this.showSettings();
            return;
        }
        
        if (!settings.modelScopeCookie) {
            this.showToast(CONFIG.ERRORS.MISSING_COOKIE, 'error');
            this.showSettings();
            return;
        }
        
        try {
            // 禁用按钮
            this.elements.analyzeBtn.disabled = true;
            this.elements.analyzeBtn.textContent = '处理中...';
            
            // 开始处理
            await this.processImage();
            
        } catch (error) {
            this.showToast('处理失败: ' + error.message, 'error');

        } finally {
            // 恢复按钮
            this.elements.analyzeBtn.disabled = false;
            this.elements.analyzeBtn.textContent = '反推并生成';
        }
    }
    
    /**
     * 处理图片
     */
    async processImage() {
        // 这里应该调用API类的方法
        // 由于API类还没有实现，先模拟处理过程
        

        this.showUploadProgress(0);
        
        // 模拟上传进度
        for (let i = 0; i <= 100; i += 10) {
            await Utils.sleep(100);
            this.showUploadProgress(i);
        }
        
        this.hideUploadProgress();

        
        // 显示队列信息
        this.showQueueInfo('正在分析图片内容...', 0);
        
        // 模拟分析过程
        for (let i = 0; i <= 100; i += 5) {
            await Utils.sleep(200);
            this.updateQueueProgress(i);
            
            if (i === 50) {
                this.updateQueueInfo('正在生成新图片...', i);
            }
        }
        
        // 模拟生成结果
        this.hideQueueInfo();

        
        // 显示生成的图片（这里使用示例图片）
        const mockImages = [
            'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7nlJ/miJDlm77niYcxPC90ZXh0Pjwvc3ZnPg==',
            'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjYWFhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7nlJ/miJDlm77niYcyPC90ZXh0Pjwvc3ZnPg==',
            'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjNzc3Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7nlJ/miJDlm77niYczPC90ZXh0Pjwvc3ZnPg=='
        ];
        
        this.showGeneratedImages(mockImages);
    }
    
    /**
     * 显示上传进度
     */
    showUploadProgress(percent) {
        this.elements.uploadProgress.style.display = 'block';
        this.elements.progressFill.style.width = percent + '%';
        this.elements.progressText.textContent = `上传中... ${percent}%`;
    }
    
    /**
     * 隐藏上传进度
     */
    hideUploadProgress() {
        this.elements.uploadProgress.style.display = 'none';
    }
    
    /**
     * 显示队列信息
     */
    showQueueInfo(message, progress) {
        this.elements.queueInfo.style.display = 'block';
        this.elements.queueDetail.textContent = message;
        this.elements.queueProgress.style.width = progress + '%';
    }
    
    /**
     * 更新队列信息
     */
    updateQueueInfo(message, progress) {
        this.elements.queueDetail.textContent = message;
        this.elements.queueProgress.style.width = progress + '%';
    }
    
    /**
     * 更新队列进度
     */
    updateQueueProgress(progress) {
        this.elements.queueProgress.style.width = progress + '%';
    }
    
    /**
     * 隐藏队列信息
     */
    hideQueueInfo() {
        this.elements.queueInfo.style.display = 'none';
    }
    
    /**
     * 显示生成的图片
     */
    showGeneratedImages(images) {
        this.generatedImages = images;
        
        // 清空缩略图容器
        this.elements.thumbnailsContainer.innerHTML = '';
        
        // 创建缩略图
        images.forEach((imageUrl, index) => {
            const wrapper = document.createElement('div');
            wrapper.className = 'thumbnail-wrapper';
            wrapper.dataset.index = index;
            
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = `生成图片 ${index + 1}`;
            
            wrapper.appendChild(img);
            this.elements.thumbnailsContainer.appendChild(wrapper);
            
            // 绑定点击事件
            wrapper.addEventListener('click', () => this.selectThumbnail(index));
        });
        
        // 默认选择第一张图片
        if (images.length > 0) {
            this.selectThumbnail(0);
        }
    }
    
    /**
     * 选择缩略图
     */
    selectThumbnail(index) {
        // 移除之前的选中状态
        if (this.selectedThumbnail !== null) {
            const prevWrapper = this.elements.thumbnailsContainer.children[this.selectedThumbnail];
            if (prevWrapper) {
                prevWrapper.classList.remove('selected');
            }
        }
        
        // 设置新的选中状态
        this.selectedThumbnail = index;
        const wrapper = this.elements.thumbnailsContainer.children[index];
        if (wrapper) {
            wrapper.classList.add('selected');
        }
        
        // 在主预览区域显示选中的图片
        this.showMainPreview(this.generatedImages[index]);
    }
    
    /**
     * 在主预览区域显示图片
     */
    showMainPreview(imageUrl) {
        this.elements.mainPreview.innerHTML = `<img src="${imageUrl}" alt="预览图片">`;
    }
    
    /**
     * 处理主预览区域点击
     */
    handleMainPreviewClick() {
        if (this.selectedThumbnail !== null && this.generatedImages[this.selectedThumbnail]) {
            // 在新标签页中打开图片
            window.open(this.generatedImages[this.selectedThumbnail], '_blank');
        }
    }
    
    /**
     * 显示设置面板
     */
    showSettings() {
        this.elements.settingsPanel.style.display = 'block';
    }
    
    /**
     * 隐藏设置面板
     */
    hideSettings() {
        this.elements.settingsPanel.style.display = 'none';
    }
    
    /**
     * 保存设置
     */
    async saveSettings() {
        const settings = {
            openaiKey: this.elements.openaiKey.value.trim(),
            modelScopeCookie: this.elements.modelScopeCookie.value.trim(),
            imageWidth: parseInt(this.elements.imageWidth.value) || CONFIG.DEFAULTS.IMAGE_WIDTH,
            imageHeight: parseInt(this.elements.imageHeight.value) || CONFIG.DEFAULTS.IMAGE_HEIGHT
        };
        
        try {
            // 保存到Chrome存储
            await chrome.storage.local.set({
                [CONFIG.STORAGE_KEYS.OPENAI_API_KEY]: settings.openaiKey,
                [CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE]: settings.modelScopeCookie,
                [CONFIG.STORAGE_KEYS.IMAGE_WIDTH]: settings.imageWidth,
                [CONFIG.STORAGE_KEYS.IMAGE_HEIGHT]: settings.imageHeight,
                [CONFIG.STORAGE_KEYS.SETTINGS]: settings
            });
            
            this.showToast(CONFIG.SUCCESS.SETTINGS_SAVED, 'success');

            this.hideSettings();
            
        } catch (error) {
            this.showToast('设置保存失败', 'error');

        }
    }
    
    /**
     * 重置设置
     */
    async resetSettings() {
        this.elements.openaiKey.value = '';
        this.elements.modelScopeCookie.value = '';
        this.elements.imageWidth.value = CONFIG.DEFAULTS.IMAGE_WIDTH;
        this.elements.imageHeight.value = CONFIG.DEFAULTS.IMAGE_HEIGHT;
        
        try {
            // 清除Chrome存储
            await chrome.storage.local.remove([
                CONFIG.STORAGE_KEYS.OPENAI_API_KEY,
                CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE,
                CONFIG.STORAGE_KEYS.IMAGE_WIDTH,
                CONFIG.STORAGE_KEYS.IMAGE_HEIGHT,
                CONFIG.STORAGE_KEYS.SETTINGS
            ]);
            
            this.showToast(CONFIG.SUCCESS.SETTINGS_RESET, 'success');

            
        } catch (error) {
            this.showToast('设置重置失败', 'error');

        }
    }
    
    /**
     * 加载设置
     */
    async loadSettings() {
        try {
            const result = await chrome.storage.local.get([
                CONFIG.STORAGE_KEYS.OPENAI_API_KEY,
                CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE,
                CONFIG.STORAGE_KEYS.IMAGE_WIDTH,
                CONFIG.STORAGE_KEYS.IMAGE_HEIGHT
            ]);
            
            this.elements.openaiKey.value = result[CONFIG.STORAGE_KEYS.OPENAI_API_KEY] || '';
            this.elements.modelScopeCookie.value = result[CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE] || '';
            this.elements.imageWidth.value = result[CONFIG.STORAGE_KEYS.IMAGE_WIDTH] || CONFIG.DEFAULTS.IMAGE_WIDTH;
            this.elements.imageHeight.value = result[CONFIG.STORAGE_KEYS.IMAGE_HEIGHT] || CONFIG.DEFAULTS.IMAGE_HEIGHT;
            
        } catch (error) {

        }
    }
    
    /**
     * 获取当前设置
     */
    async getSettings() {
        try {
            const result = await chrome.storage.local.get([
                CONFIG.STORAGE_KEYS.OPENAI_API_KEY,
                CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE,
                CONFIG.STORAGE_KEYS.IMAGE_WIDTH,
                CONFIG.STORAGE_KEYS.IMAGE_HEIGHT
            ]);
            
            return {
                openaiKey: result[CONFIG.STORAGE_KEYS.OPENAI_API_KEY] || '',
                modelScopeCookie: result[CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE] || '',
                imageWidth: result[CONFIG.STORAGE_KEYS.IMAGE_WIDTH] || CONFIG.DEFAULTS.IMAGE_WIDTH,
                imageHeight: result[CONFIG.STORAGE_KEYS.IMAGE_HEIGHT] || CONFIG.DEFAULTS.IMAGE_HEIGHT
            };
            
        } catch (error) {

            return {
                openaiKey: '',
                modelScopeCookie: '',
                imageWidth: CONFIG.DEFAULTS.IMAGE_WIDTH,
                imageHeight: CONFIG.DEFAULTS.IMAGE_HEIGHT
            };
        }
    }
    
    /**
     * 显示Toast通知
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        this.elements.toastContainer.appendChild(toast);
        
        // 自动移除Toast
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, CONFIG.UI.TOAST_DURATION);
    }
    

}

// 导出UI管理类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIManager;
} else if (typeof window !== 'undefined') {
    window.UIManager = UIManager;
}