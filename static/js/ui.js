// 全局变量
let currentImageUrl = null;



// 显示Toast通知
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast_container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.role = 'alert';
    toast.ariaLive = 'assertive';
    toast.ariaAtomic = 'true';

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    const toastBootstrap = new bootstrap.Toast(toast);
    toastBootstrap.show();

    toast.addEventListener('hidden.bs.toast', function () {
        toastContainer.removeChild(toast);
    });
}


// 显示图片预览
function showImagePreview(imageUrl) {
    currentImageUrl = imageUrl;
    
    // 获取预览元素
    const dropPlaceholder = document.getElementById('drop_placeholder');
    const imagePreview = document.getElementById('image_preview');
    const previewImg = document.getElementById('preview_img');
    const uploadedFileInfo = document.getElementById('uploaded_file_info');
    
    // 设置图片源
    previewImg.src = ''; // 先清空避免缓存问题
    previewImg.src = imageUrl;
    
    // 图片加载成功后显示
    previewImg.onload = function() {
        // 重新获取DOM元素引用并更新UI
        const dropPlaceholder = document.getElementById('drop_placeholder');
        const imagePreview = document.getElementById('image_preview');
        const uploadedFileInfo = document.getElementById('uploaded_file_info');
        
        // 显示预览图片，隐藏拖放提示和所有文字图标
        dropPlaceholder.style.display = 'none';
        imagePreview.style.display = 'block';
        // 确保完全隐藏上传文件信息
        uploadedFileInfo.style.display = 'none';
        uploadedFileInfo.innerHTML = '';
        

    };
    
    // 图片加载失败处理
    previewImg.onerror = function() {
        // 重新获取DOM元素引用
        const dropPlaceholder = document.getElementById('drop_placeholder');
        const imagePreview = document.getElementById('image_preview');
        const uploadedFileInfo = document.getElementById('uploaded_file_info');
        
        // 显示错误信息
        dropPlaceholder.innerHTML = '<div class="feature-icon">❌</div><p>无法加载预览图片</p><p>请重新选择图片文件</p>';
        dropPlaceholder.style.display = 'flex';
        imagePreview.style.display = 'none';
        uploadedFileInfo.style.display = 'none';

    };
}

// 显示图片全屏预览 - 支持ESC退出和左右键切换
function showImageFullscreen(imageUrl) {
    // 设置全局状态，表示当前正在查看大图
    window.isFullscreenImageOpen = true;
    
    // 获取当前图片在生成列表中的索引
    let currentImageIndex = 0;
    if (window.generatedImages && window.generatedImages.length > 0) {
        currentImageIndex = window.generatedImages.indexOf(imageUrl);
        if (currentImageIndex === -1) {
            currentImageIndex = 0;
        }
    }
    
    // 创建全屏遮罩
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
    overlay.style.zIndex = '9999';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.cursor = 'pointer';
    
    // 创建大图元素
    const fullscreenImg = document.createElement('img');
    fullscreenImg.src = imageUrl;
    fullscreenImg.style.maxWidth = '90%';
    fullscreenImg.style.maxHeight = '90%';
    fullscreenImg.style.objectFit = 'contain';
    fullscreenImg.style.cursor = 'default';
    
    // 点击空白处关闭全屏预览
    overlay.addEventListener('click', closeFullscreen);
    
    // 点击图片本身不关闭
    fullscreenImg.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // 添加键盘事件监听
    function handleKeyDown(e) {
        // ESC键退出全屏
        if (e.key === 'Escape') {
            closeFullscreen();
        }
        // 左右方向键切换图片
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            if (window.generatedImages && window.generatedImages.length > 0) {
                if (e.key === 'ArrowLeft') {
                    currentImageIndex = (currentImageIndex - 1 + window.generatedImages.length) % window.generatedImages.length;
                } else {
                    currentImageIndex = (currentImageIndex + 1) % window.generatedImages.length;
                }
                fullscreenImg.src = window.generatedImages[currentImageIndex];
                e.preventDefault();
            }
        }
    }
    
    // 关闭全屏预览函数
    function closeFullscreen() {
        document.body.removeChild(overlay);
        document.removeEventListener('keydown', handleKeyDown);
        // 重置全局状态
        window.isFullscreenImageOpen = false;
    }
    
    // 添加键盘事件监听
    document.addEventListener('keydown', handleKeyDown);
    
    overlay.appendChild(fullscreenImg);
    document.body.appendChild(overlay);
}

// 显示生成的图片 - 支持键盘左右键切换
function displayGeneratedImages(images) {
    const mainPreviewArea = document.getElementById('main_preview_area');
    const thumbnailsContainer = document.getElementById('thumbnails_container');
    
    if (!mainPreviewArea || !thumbnailsContainer) return;

    // 清空容器
    mainPreviewArea.innerHTML = '';
    thumbnailsContainer.innerHTML = '';

    // 存储所有图片URL
    window.generatedImages = images;

    // 如果有图片，默认显示第一张
    if (images.length > 0) {
        showSelectedImage(images[0]);
    } else {
        mainPreviewArea.innerHTML = `
            <div class="d-flex justify-content-center align-items-center text-muted">
                没有生成图片
            </div>
        `;
    }

    // 创建底部缩略图
    images.forEach((imageUrl, index) => {
        const thumbnailWrapper = document.createElement('div');
        thumbnailWrapper.className = index === 0 ? 'selected' : '';
        thumbnailWrapper.style.cursor = 'pointer';
        thumbnailWrapper.style.border = index === 0 ? '2px solid #007bff' : '2px solid transparent';
        thumbnailWrapper.style.borderRadius = '4px';
        thumbnailWrapper.style.padding = '2px';
        
        const thumbnail = document.createElement('img');
        thumbnail.src = imageUrl;
        thumbnail.style.width = '42px';
        thumbnail.style.height = '42px';
        thumbnail.style.objectFit = 'cover';
        thumbnail.style.borderRadius = '2px';
        
        // 点击缩略图选择图片
        thumbnailWrapper.addEventListener('click', function() {
            // 移除其他选中状态
            const allThumbnails = thumbnailsContainer.querySelectorAll('div');
            allThumbnails.forEach(thumb => {
                thumb.style.border = '2px solid transparent';
            });
            // 添加选中状态
            this.style.border = '2px solid #007bff';
            // 显示选中的图片
            showSelectedImage(imageUrl);
        });
        
        thumbnailWrapper.appendChild(thumbnail);
        thumbnailsContainer.appendChild(thumbnailWrapper);
    });
    
    // 添加键盘事件监听，支持左右键切换缩略图
    if (images.length > 0) {
        // 确保缩略图容器获得焦点
        thumbnailsContainer.setAttribute('tabindex', '0');
        
        function handleThumbnailKeyDown(e) {
            const thumbnails = thumbnailsContainer.querySelectorAll('div');
            if (!thumbnails.length) return;
            
            // 找到当前选中的缩略图
            let currentIndex = -1;
            for (let i = 0; i < thumbnails.length; i++) {
                if (thumbnails[i].style.border === '2px solid #007bff') {
                    currentIndex = i;
                    break;
                }
            }
            
            // 默认选择第一张
            if (currentIndex === -1) currentIndex = 0;
            
            // 左右方向键切换
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                
                // 移除当前选中状态
                thumbnails[currentIndex].style.border = '2px solid transparent';
                
                // 计算新索引
                if (e.key === 'ArrowLeft') {
                    currentIndex = (currentIndex - 1 + thumbnails.length) % thumbnails.length;
                } else {
                    currentIndex = (currentIndex + 1) % thumbnails.length;
                }
                
                // 设置新选中状态
                thumbnails[currentIndex].style.border = '2px solid #007bff';
                
                // 显示选中的图片
                showSelectedImage(images[currentIndex]);
                
                // 滚动到选中的缩略图
                thumbnails[currentIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        }
        
        // 添加键盘事件监听
        thumbnailsContainer.addEventListener('keydown', handleThumbnailKeyDown);
    }
}

// 显示选中的图片（中等大小）
function showSelectedImage(imageUrl) {
    const mainPreviewArea = document.getElementById('main_preview_area');
    if (!mainPreviewArea) return;
    
    mainPreviewArea.innerHTML = '';
    
    const imgWrapper = document.createElement('div');
    imgWrapper.style.cursor = 'pointer';
    imgWrapper.style.display = 'flex';
    imgWrapper.style.justifyContent = 'center';
    imgWrapper.style.alignItems = 'center';
    imgWrapper.style.width = '223.07px';
    imgWrapper.style.height = '400px';
    
    const img = document.createElement('img');
    img.src = imageUrl;
    img.style.maxWidth = '100%';
    img.style.maxHeight = '100%';
    img.style.objectFit = 'contain';
    
    // 点击中等大小图片查看原图
    imgWrapper.addEventListener('click', function() {
        showImageFullscreen(imageUrl);
    });
    
    imgWrapper.appendChild(img);
    mainPreviewArea.appendChild(imgWrapper);
}