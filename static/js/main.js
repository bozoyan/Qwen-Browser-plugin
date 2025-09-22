// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // 元素引用
    const fileInput = document.getElementById('file_input');
    const fileDropArea = document.getElementById('file_drop_area');
    const imagePreview = document.getElementById('image_preview');
    const previewImg = document.getElementById('preview_img');
    const urlImagePreview = document.getElementById('url_image_preview');
    const urlPreviewImg = document.getElementById('url_preview_img');
    const dropPlaceholder = document.getElementById('drop_placeholder');
    const uploadedFileInfo = document.getElementById('uploaded_file_info');
    const analyzeAndGenerateButton = document.getElementById('analyze_and_generate');

    // =========================================================================
    // 初始化逻辑
    // =========================================================================

    // 检查URL中是否包含imageUrl参数
    const urlParams = new URLSearchParams(window.location.search);
    const imageUrlFromParam = urlParams.get('imageUrl');

    if (imageUrlFromParam) {
        // 如果有imageUrl参数，则显示URL图片预览区域，隐藏文件上传区域
        if (dropPlaceholder) dropPlaceholder.style.display = 'none';
        if (uploadedFileInfo) uploadedFileInfo.style.display = 'none';
        if (imagePreview) imagePreview.style.display = 'none';
        if (fileInput) fileInput.style.display = 'none';
        if (fileDropArea) fileDropArea.style.pointerEvents = 'none'; // 禁用拖放区域

        if (urlImagePreview) urlImagePreview.style.display = 'block';
        if (urlPreviewImg) urlPreviewImg.src = imageUrlFromParam;
        if (analyzeAndGenerateButton) analyzeAndGenerateButton.disabled = false;

        // 自动触发分析和生成
        analyzeAndGenerate(imageUrlFromParam);
    } else {
        // 否则，确保文件上传区域是可见的
        if (dropPlaceholder) dropPlaceholder.style.display = 'flex';
        if (urlImagePreview) urlImagePreview.style.display = 'none';
        if (fileInput) fileInput.style.display = 'block';
        if (fileDropArea) fileDropArea.style.pointerEvents = 'auto';
    }

    // =========================================================================
    // 事件监听
    // =========================================================================

    // 1. 点击上传区域触发文件选择
    if (fileDropArea) {
        fileDropArea.addEventListener('click', (e) => {
            // 如果点击的是图片预览区域，不触发文件选择
            if (e.target.closest('#image_preview')) {
                return;
            }
            fileInput.value = ''; // 允许重复选择相同文件
            fileInput.click();
        });
    }

    // 2. 点击预览图片时也能重新选择文件
    if (imagePreview) {
        imagePreview.addEventListener('click', (e) => {
            e.stopPropagation(); // 阻止事件冒泡
            fileInput.value = '';
            fileInput.click();
        });
    }

    // 3. 处理文件选择
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }

    // 4. 处理文件拖放
    if (fileDropArea) {
        // 防止浏览器默认行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, preventDefaults, false);
        });

        // 高亮/取消高亮拖放区域
        ['dragenter', 'dragover'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, () => fileDropArea.classList.add('active'), false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, () => fileDropArea.classList.remove('active'), false);
        });

        // 处理拖放的文件
        fileDropArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files[0]) {
                handleFileUpload(files[0]);
            }
        }, false);
    }

    // 5. 点击 "反推并生成" 按钮
    if (analyzeAndGenerateButton) {
        analyzeAndGenerateButton.addEventListener('click', () => analyzeAndGenerate());
    }

    // =========================================================================
    // 核心功能函数
    // =========================================================================

    /**
     * 处理文件上传的整个流程
     * @param {File} file - 用户选择的文件
     */
    async function handleFileUpload(file) {
        const uploadProgressContainer = document.getElementById('upload_progress_container');
        const uploadProgressBar = document.getElementById('upload_progress_bar');

        // 验证文件
        const validExtensions = ['image/png', 'image/jpeg', 'image/gif', 'image/bmp'];
        if (!validExtensions.includes(file.type)) {
            showToast('不支持的文件类型，请上传图片文件', 'danger');

            return;
        }
        if (file.size > 16 * 1024 * 1024) { // 16MB
            showToast('文件太大，请上传小于16MB的图片', 'danger');

            return;
        }

        // 显示进度条
        if(uploadProgressContainer) uploadProgressContainer.style.display = 'block';
        if(uploadProgressBar) uploadProgressBar.style.width = '0%';
        if(analyzeAndGenerateButton) analyzeAndGenerateButton.disabled = true;


        try {
            // 定义上传进度回调
            const onUploadProgress = (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                if(uploadProgressBar) uploadProgressBar.style.width = percentCompleted + '%';
            };

            // 调用API上传文件
            const data = await uploadFile(file, onUploadProgress);

            if (data.success) {
                const imageUrl = '/uploads/' + data.filename;
                showImagePreview(imageUrl); // from ui.js
                if (analyzeAndGenerateButton) analyzeAndGenerateButton.disabled = false;

                showToast('文件上传成功！', 'success');
            } else {
                throw new Error(data.error || '上传失败');
            }
        } catch (error) {

            showToast('上传文件时出错，请重试', 'danger');
            if (analyzeAndGenerateButton) analyzeAndGenerateButton.disabled = true;
        } finally {
            if(uploadProgressContainer) uploadProgressContainer.style.display = 'none';
        }
    }

    /**
     * 执行分析并生成图片的流程
     * @param {string} [imageUrl] - 可选的图片URL，如果提供则从URL分析，否则从已上传图片分析
     */
    async function analyzeAndGenerate(imageUrl = null) {
        let analysisResponse;
        if (imageUrl) {
            // 从URL分析图片
            analysisResponse = await analyzeImageFromUrl(imageUrl); // from api.js
        } else {
            // 从已上传图片分析
            analysisResponse = await analyzeImage(true); // from api.js
        }

        // 2. 如果分析成功，则生成图片
        if (analysisResponse && analysisResponse.success) {
            const prompt = analysisResponse.prompt; // 注意这里是analysisResponse.prompt

            try {
                // 调用API生成图片 - 只传递prompt，让后端使用config中的默认配置
                const images = await generateQwenImage(prompt); // from api.js
                displayGeneratedImages(images); // from ui.js

                showToast('图片生成成功！', 'success');
            } catch (error) {

                showToast('生成图片时出错：' + error.message, 'danger');
            }
        }
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }


});