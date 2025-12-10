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

            // URL输入相关
            imageUrlInput: document.getElementById('imageUrlInput'),
            loadUrlBtn: document.getElementById('loadUrlBtn'),

            // 进度相关
            uploadProgress: document.getElementById('uploadProgress'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),

            // 按钮
            analyzeBtn: document.getElementById('analyzeBtn'),
            settingsBtn: document.getElementById('settingsBtn'),
            stopBtn: document.getElementById('stopBtn'),
            removeImageBtn: document.getElementById('removeImageBtn'),
            
            // 结果显示
            queueInfo: document.getElementById('queueInfo'),
            queueDetail: document.getElementById('queueDetail'),
            queueProgress: document.getElementById('queueProgress'),
            mainPreview: document.getElementById('mainPreview'),
            thumbnailsContainer: document.getElementById('thumbnailsContainer'),

            // 反推文字预览
            promptContent: document.getElementById('promptContent'),
            promptText: document.getElementById('promptText'),
            copyPromptBtn: document.getElementById('copyPromptBtn'),
            

            
            // 设置面板
            settingsPanel: document.getElementById('settingsPanel'),
            closeSettings: document.getElementById('closeSettings'),
            openaiKey: document.getElementById('openaiKey'),
            modelScopeCookie: document.getElementById('modelScopeCookie'),
            imageWidth: document.getElementById('imageWidth'),
            imageHeight: document.getElementById('imageHeight'),
            numImages: document.getElementById('numImages'),
            enableHires: document.getElementById('enableHires'),
            checkpointSelect: document.getElementById('checkpointSelect'),
            lora1Select: document.getElementById('lora1Select'),
            lora2Select: document.getElementById('lora2Select'),
            lora3Select: document.getElementById('lora3Select'),
            lora4Select: document.getElementById('lora4Select'),
            loadModels: document.getElementById('loadModels'),
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

        // URL加载事件
        this.elements.loadUrlBtn.addEventListener('click', this.handleLoadImageUrl.bind(this));
        this.elements.imageUrlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleLoadImageUrl();
            }
        });

        // 按钮事件（注意：analyzeBtn的事件由popup.js处理，这里不绑定）
        // this.elements.analyzeBtn.addEventListener('click', this.handleAnalyze.bind(this));
        this.elements.settingsBtn.addEventListener('click', this.showSettings.bind(this));
        this.elements.closeSettings.addEventListener('click', this.hideSettings.bind(this));
        this.elements.saveSettings.addEventListener('click', this.saveSettings.bind(this));
        this.elements.resetSettings.addEventListener('click', this.resetSettings.bind(this));
        this.elements.loadModels.addEventListener('click', this.loadModels.bind(this));

        // 删除图片和复制按钮事件
        this.elements.removeImageBtn.addEventListener('click', this.handleRemoveImage.bind(this));
        this.elements.copyPromptBtn.addEventListener('click', this.handleCopyPrompt.bind(this));

        // 主预览区域点击事件
        this.elements.mainPreview.addEventListener('click', this.handleMainPreviewClick.bind(this));

        console.log('🔧 [UI] 基础事件绑定完成（analyzeBtn由popup.js处理）');
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
     * 注意：这个方法应该被popup.js中的handleAnalyze覆盖
     * 这里保留作为后备，但不应该被调用
     */
    async handleAnalyze() {
        if (!this.currentImageData) {
            this.showToast('请先选择图片', 'warning');
            return;
        }

        // 检查设置
        const settings = await this.getSettings();
        if (!settings.openaiKey) {
            this.showToast('请先配置 OpenAI API Key', 'error');
            this.showSettings();
            return;
        }

        if (!settings.modelScopeCookie) {
            this.showToast('请先配置 ModelScope Cookie', 'error');
            this.showSettings();
            return;
        }

        // 不应该调用这个方法，让popup.js的处理逻辑接管
        console.warn('[UI] UI.handleAnalyze被调用，应该使用popup.js的处理逻辑');
    }
    
    /**
     * 处理图片（已废弃，使用popup.js中的processImageWithRealAPI）
     * @deprecated
     */
    async processImage() {
        console.warn('[UI] processImage方法已废弃，请使用popup.js中的API处理逻辑');
        // 这个方法不再使用，所有图片处理逻辑都移动到popup.js中
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
    showGeneratedImages(images, prompt = '') {
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

        // 显示反推文字
        if (prompt) {
            this.showPromptText(prompt);
        }
    }

    /**
     * 显示反推文字
     */
    showPromptText(prompt) {
        // 在主预览区域下方创建提示文字区域
        let promptContainer = document.getElementById('promptContainer');
        if (!promptContainer) {
            promptContainer = document.createElement('div');
            promptContainer.id = 'promptContainer';
            promptContainer.className = 'prompt-container';
            this.elements.mainPreview.parentNode.insertBefore(
                promptContainer,
                this.elements.mainPreview.nextSibling
            );
        }

        promptContainer.innerHTML = `
            <div class="prompt-header">
                <h4>图片反推结果</h4>
                <button class="copy-prompt-btn" title="复制提示词">📋</button>
            </div>
            <div class="prompt-text">${prompt}</div>
        `;

        // 绑定复制按钮事件
        const copyBtn = promptContainer.querySelector('.copy-prompt-btn');
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(prompt).then(() => {
                this.showToast('提示词已复制到剪贴板', 'success');
            }).catch(() => {
                this.showToast('复制失败', 'error');
            });
        });
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
        if (this.selectedThumbnail !== null && this.generatedImages && this.generatedImages[this.selectedThumbnail]) {
            // 创建图片放大模态窗口
            this.showImageModal(this.generatedImages[this.selectedThumbnail]);
        }
    }

    /**
     * 显示图片放大模态窗口
     */
    showImageModal(imageUrl) {
        // 创建模态窗口
        const modal = document.createElement('div');
        modal.className = 'image-modal';
        modal.innerHTML = `
            <div class="image-modal-content">
                <button class="image-modal-close">×</button>
                <img src="${imageUrl}" alt="放大图片" />
                <div class="image-modal-info">
                    <p>点击图片或背景关闭</p>
                    <button class="image-modal-download">下载原图</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 添加样式
        if (!document.getElementById('image-modal-styles')) {
            const style = document.createElement('style');
            style.id = 'image-modal-styles';
            style.textContent = `
                .image-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.9);
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                }

                .image-modal-content {
                    position: relative;
                    max-width: 90%;
                    max-height: 90%;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }

                .image-modal-close {
                    position: absolute;
                    top: -30px;
                    right: -30px;
                    background: rgba(255, 255, 255, 0.8);
                    border: none;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    font-size: 18px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .image-modal img {
                    max-width: 100%;
                    max-height: 80vh;
                    object-fit: contain;
                    border-radius: 4px;
                }

                .image-modal-info {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    margin-top: 15px;
                    color: white;
                    font-size: 14px;
                }

                .image-modal-download {
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }

                .image-modal-download:hover {
                    background: #0056b3;
                }
            `;
            document.head.appendChild(style);
        }

        // 绑定关闭事件
        const closeModal = () => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        };

        modal.addEventListener('click', closeModal);
        modal.querySelector('.image-modal-content').addEventListener('click', (e) => {
            e.stopPropagation();
        });
        modal.querySelector('.image-modal-close').addEventListener('click', closeModal);

        // 绑定下载事件
        modal.querySelector('.image-modal-download').addEventListener('click', (e) => {
            e.stopPropagation();
            this.downloadImage(imageUrl);
        });

        // ESC键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    /**
     * 下载图片
     */
    downloadImage(imageUrl) {
        try {
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = `generated-image-${Date.now()}.png`;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.showToast('图片下载已开始', 'success');
        } catch (error) {
            // 如果直接下载失败，尝试在新标签页打开
            window.open(imageUrl, '_blank');
            this.showToast('已在新标签页打开图片，请手动保存', 'info');
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
     * 加载模型数据
     */
    async loadModels() {
        try {
            this.showToast('正在加载模型数据...', 'info');

            const apiManager = new APIManager();
            const modelData = await apiManager.loadModels();

            // 加载checkpoint模型
            this.populateCheckpoints(modelData.checkpoints);

            // 加载LoRA模型
            this.populateLoRAs(modelData.loras);

            this.showToast('模型数据加载成功', 'success');

        } catch (error) {
            console.error('加载模型失败:', error);
            this.showToast('模型数据加载失败: ' + error.message, 'error');
        }
    }

    /**
     * 填充checkpoint下拉框
     */
    populateCheckpoints(checkpoints) {
        const select = this.elements.checkpointSelect;
        select.innerHTML = '<option value="">请选择Checkpoint模型</option>';

        checkpoints.forEach(checkpoint => {
            const option = document.createElement('option');
            option.value = JSON.stringify(checkpoint);
            option.textContent = checkpoint.CheckpointName;
            option.dataset.modelVersionId = checkpoint.checkpointModelVersionId;
            select.appendChild(option);
        });
    }

    /**
     * 填充LoRA下拉框
     */
    populateLoRAs(loras) {
        const loraSelects = [
            this.elements.lora1Select,
            this.elements.lora2Select,
            this.elements.lora3Select,
            this.elements.lora4Select
        ];

        loraSelects.forEach(select => {
            select.innerHTML = '<option value="">请选择LoRA模型</option>';

            loras.forEach(lora => {
                const option = document.createElement('option');
                option.value = JSON.stringify(lora);
                option.textContent = lora.LoraName;
                option.dataset.modelVersionId = lora.modelVersionId;
                select.appendChild(option);
            });
        });
    }

    /**
     * 保存设置
     */
    async saveSettings() {
        const selectedCheckpoint = this.elements.checkpointSelect.value;
        const checkpoint = selectedCheckpoint ? JSON.parse(selectedCheckpoint) : null;

        const loras = [];
        for (let i = 1; i <= 4; i++) {
            const loraSelect = this.elements[`lora${i}Select`];
            if (loraSelect.value) {
                loras.push(JSON.parse(loraSelect.value));
            } else {
                loras.push(null);
            }
        }

        const settings = {
            openaiKey: this.elements.openaiKey.value.trim(),
            modelScopeCookie: this.elements.modelScopeCookie.value.trim(),
            imageWidth: parseInt(this.elements.imageWidth.value) || CONFIG.DEFAULTS.IMAGE_WIDTH,
            imageHeight: parseInt(this.elements.imageHeight.value) || CONFIG.DEFAULTS.IMAGE_HEIGHT,
            numImages: parseInt(this.elements.numImages.value) || 4,
            enableHires: this.elements.enableHires.checked,
            checkpoint: checkpoint,
            lora1: loras[0],
            lora2: loras[1],
            lora3: loras[2],
            lora4: loras[3]
        };

        try {
            // 保存到Chrome存储
            await chrome.storage.local.set({
                [CONFIG.STORAGE_KEYS.OPENAI_API_KEY]: settings.openaiKey,
                [CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE]: settings.modelScopeCookie,
                [CONFIG.STORAGE_KEYS.IMAGE_WIDTH]: settings.imageWidth,
                [CONFIG.STORAGE_KEYS.IMAGE_HEIGHT]: settings.imageHeight,
                [CONFIG.STORAGE_KEYS.SETTINGS]: settings,
                'numImages': settings.numImages,
                'enableHires': settings.enableHires,
                'checkpoint': settings.checkpoint,
                'lora1': settings.lora1,
                'lora2': settings.lora2,
                'lora3': settings.lora3,
                'lora4': settings.lora4
            });

            this.showToast(CONFIG.SUCCESS.SETTINGS_SAVED, 'success');
            this.hideSettings();

        } catch (error) {
            this.showToast('设置保存失败', 'error');
            console.error('设置保存失败:', error);
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
        this.elements.numImages.value = 4;
        this.elements.enableHires.checked = true;

        // 重置模型选择
        this.elements.checkpointSelect.selectedIndex = 0;
        this.elements.lora1Select.selectedIndex = 0;
        this.elements.lora2Select.selectedIndex = 0;
        this.elements.lora3Select.selectedIndex = 0;
        this.elements.lora4Select.selectedIndex = 0;

        try {
            // 清除Chrome存储
            await chrome.storage.local.remove([
                CONFIG.STORAGE_KEYS.OPENAI_API_KEY,
                CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE,
                CONFIG.STORAGE_KEYS.IMAGE_WIDTH,
                CONFIG.STORAGE_KEYS.IMAGE_HEIGHT,
                CONFIG.STORAGE_KEYS.SETTINGS,
                'numImages',
                'enableHires',
                'checkpoint',
                'lora1',
                'lora2',
                'lora3',
                'lora4'
            ]);

            this.showToast(CONFIG.SUCCESS.SETTINGS_RESET, 'success');

        } catch (error) {
            this.showToast('设置重置失败', 'error');
            console.error('设置重置失败:', error);
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
                CONFIG.STORAGE_KEYS.IMAGE_HEIGHT,
                'numImages',
                'enableHires',
                'checkpoint',
                'lora1',
                'lora2',
                'lora3',
                'lora4'
            ]);

            this.elements.openaiKey.value = result[CONFIG.STORAGE_KEYS.OPENAI_API_KEY] || '';
            this.elements.modelScopeCookie.value = result[CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE] || '';
            this.elements.imageWidth.value = result[CONFIG.STORAGE_KEYS.IMAGE_WIDTH] || CONFIG.DEFAULTS.IMAGE_WIDTH;
            this.elements.imageHeight.value = result[CONFIG.STORAGE_KEYS.IMAGE_HEIGHT] || CONFIG.DEFAULTS.IMAGE_HEIGHT;
            this.elements.numImages.value = result.numImages || 4;
            this.elements.enableHires.checked = result.enableHires !== false;

            // 延迟加载模型选择
            setTimeout(() => {
                this.loadModelSelections(result);
            }, 100);

        } catch (error) {
            console.error('加载设置失败:', error);
        }
    }

    /**
     * 加载模型选择
     */
    loadModelSelections(savedData) {
        try {
            // 加载checkpoint选择
            if (savedData.checkpoint) {
                const checkpointOption = Array.from(this.elements.checkpointSelect.options)
                    .find(option => {
                        try {
                            const data = JSON.parse(option.value);
                            return data.checkpointModelVersionId === savedData.checkpoint.checkpointModelVersionId;
                        } catch {
                            return false;
                        }
                    });
                if (checkpointOption) {
                    this.elements.checkpointSelect.value = checkpointOption.value;
                }
            }

            // 加载LoRA选择
            for (let i = 1; i <= 4; i++) {
                const loraKey = `lora${i}`;
                const savedLora = savedData[loraKey];
                if (savedLora) {
                    const loraSelect = this.elements[`${loraKey}Select`];
                    const loraOption = Array.from(loraSelect.options)
                        .find(option => {
                            try {
                                const data = JSON.parse(option.value);
                                return data.modelVersionId === savedLora.modelVersionId;
                            } catch {
                                return false;
                            }
                        });
                    if (loraOption) {
                        loraSelect.value = loraOption.value;
                    }
                }
            }

        } catch (error) {
            console.error('加载模型选择失败:', error);
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
                CONFIG.STORAGE_KEYS.IMAGE_HEIGHT,
                'numImages',
                'enableHires',
                'checkpoint',
                'lora1',
                'lora2',
                'lora3',
                'lora4'
            ]);

            return {
                openaiKey: result[CONFIG.STORAGE_KEYS.OPENAI_API_KEY] || '',
                modelScopeCookie: result[CONFIG.STORAGE_KEYS.MODEL_SCOPE_COOKIE] || '',
                imageWidth: result[CONFIG.STORAGE_KEYS.IMAGE_WIDTH] || CONFIG.DEFAULTS.IMAGE_WIDTH,
                imageHeight: result[CONFIG.STORAGE_KEYS.IMAGE_HEIGHT] || CONFIG.DEFAULTS.IMAGE_HEIGHT,
                numImages: result.numImages || 4,
                enableHires: result.enableHires !== false,
                checkpoint: result.checkpoint,
                lora1: result.lora1,
                lora2: result.lora2,
                lora3: result.lora3,
                lora4: result.lora4
            };

        } catch (error) {
            console.error('获取设置失败:', error);
            return {
                openaiKey: '',
                modelScopeCookie: '',
                imageWidth: CONFIG.DEFAULTS.IMAGE_WIDTH,
                imageHeight: CONFIG.DEFAULTS.IMAGE_HEIGHT,
                numImages: 4,
                enableHires: true,
                checkpoint: null,
                lora1: null,
                lora2: null,
                lora3: null,
                lora4: null
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

    /**
     * 处理URL图片加载
     */
    async handleLoadImageUrl() {
        const url = this.elements.imageUrlInput.value.trim();
        if (!url) {
            this.showToast('请输入图片URL', 'warning');
            return;
        }

        // 验证URL格式
        try {
            new URL(url);
        } catch (error) {
            this.showToast('无效的URL格式', 'error');
            return;
        }

        try {
            this.showToast('正在加载图片...', 'info');

            // 清除当前图片
            this.clearCurrentImage();

            // 加载图片
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const blob = await response.blob();
            if (!blob.type.startsWith('image/')) {
                throw new Error('URL不是有效的图片格式');
            }

            // 转换为base64
            const base64 = await this.blobToBase64(blob);
            this.currentImageData = base64;

            // 显示预览
            this.elements.previewImg.src = base64;
            this.elements.dropPlaceholder.style.display = 'none';
            this.elements.imagePreview.style.display = 'block';
            this.elements.analyzeBtn.disabled = false;

            this.showToast('图片加载成功', 'success');

        } catch (error) {
            console.error('URL图片加载失败:', error);
            this.showToast('图片加载失败: ' + error.message, 'error');
        }
    }

    /**
     * 处理删除图片
     */
    handleRemoveImage() {
        this.clearCurrentImage();
        this.showToast('图片已删除', 'info');
    }

    /**
     * 清除当前图片
     */
    clearCurrentImage() {
        this.currentImageData = null;
        this.elements.previewImg.src = '';
        this.elements.imagePreview.style.display = 'none';
        this.elements.dropPlaceholder.style.display = 'block';
        this.elements.analyzeBtn.disabled = true;
        this.elements.imageUrlInput.value = '';

        // 清除反推文字
        this.clearPromptPreview();
    }

    /**
     * 处理复制提示词
     */
    handleCopyPrompt() {
        const promptText = this.elements.promptText.textContent;
        if (!promptText) {
            this.showToast('没有可复制的提示词', 'warning');
            return;
        }

        navigator.clipboard.writeText(promptText).then(() => {
            this.showToast('提示词已复制到剪贴板', 'success');
        }).catch(error => {
            console.error('复制失败:', error);
            this.showToast('复制失败', 'error');
        });
    }

    /**
     * 显示反推文字
     */
    showPromptPreview(promptText) {
        this.elements.promptText.textContent = promptText;
        this.elements.promptContent.style.display = 'flex';
        this.elements.copyPromptBtn.style.display = 'inline-block';
        this.elements.promptContent.parentElement.querySelector('.prompt-placeholder').style.display = 'none';
    }

    /**
     * 清除反推文字预览
     */
    clearPromptPreview() {
        this.elements.promptText.textContent = '';
        this.elements.promptContent.style.display = 'none';
        this.elements.copyPromptBtn.style.display = 'none';
        this.elements.promptContent.parentElement.querySelector('.prompt-placeholder').style.display = 'block';
    }

    /**
     * 显示/隐藏停止按钮
     */
    showStopButton() {
        if (this.elements.stopBtn) {
            this.elements.stopBtn.style.display = 'inline-block';
        }
    }

    hideStopButton() {
        if (this.elements.stopBtn) {
            this.elements.stopBtn.style.display = 'none';
        }
    }

    /**
     * 将Blob转换为Base64
     */
    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

}

// 导出UI管理类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIManager;
} else if (typeof window !== 'undefined') {
    window.UIManager = UIManager;
}