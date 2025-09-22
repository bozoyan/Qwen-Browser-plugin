if (typeof popup === 'undefined') {
    var popup = null;
}

function createPopup(imageUrl) {
    if (popup) {
        popup.remove();
    }

    popup = document.createElement('div');
    popup.id = 'reverse-image-popup';
    popup.innerHTML = `
        <div class="popup-header">
            <h3>反推生图</h3>
            <button class="close-btn">&times;</button>
        </div>
        <div class="popup-content">
            <div class="error-message" style="display: none;"></div>
            <div class="prompt-section">
                <label>反推提示词:</label>
                <div class="prompt-display"></div>
            </div>
            <div class="image-container">
                <div class="image-box">
                    <p>原始图片</p>
                    <img src="${imageUrl}" alt="Original Image" style="max-width: 100%; height: auto;">
                </div>
                <div class="image-box">
                    <p>生成图片</p>
                    <div class="generated-image-wrapper">
                        <div class="spinner" style="display: none;"></div>
                        <img id="main-generated-image" src="" alt="Generated Image" style="display:none; max-width: 100%; height: auto; margin-bottom: 10px; border-radius: 4px;">
                        <div id="thumbnail-container" style="display: flex; flex-wrap: nowrap; gap: 5px; justify-content: center; align-items: center; width: 100%;"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(popup);

    const closeBtn = popup.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => {
        popup.remove();
        popup = null;
    });

    return popup;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "showModal") {
        const newPopup = createPopup(request.imageUrl);
        const promptDisplay = newPopup.querySelector('.prompt-display');
        const errorMessage = newPopup.querySelector('.error-message');
        const spinner = newPopup.querySelector('.spinner');

        spinner.style.display = 'block';

        fetch('http://127.0.0.1:8005/reverse_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_url: request.imageUrl }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.prompt) {
                promptDisplay.textContent = data.prompt;
                
                fetch('http://127.0.0.1:8005/api/generate_image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: data.prompt }),
                })
                .then(response => response.json())
                .then(generateData => {
                    spinner.style.display = 'none';
                    if (generateData.success && generateData.images && generateData.images.length > 0) {
                        const mainImage = newPopup.querySelector('#main-generated-image');
                        const thumbnailContainer = newPopup.querySelector('#thumbnail-container');
                        
                        thumbnailContainer.innerHTML = '';
                        mainImage.src = generateData.images[0];
                        mainImage.style.display = 'block';

                        const imageCount = generateData.images.length;
                        const gap = 5;
                        const border = 2; // px
                        const borderWidth = border * 2;
                        
                        const imageBox = thumbnailContainer.closest('.image-box');
                        const containerWidth = imageBox ? imageBox.clientWidth : 0;
                        const totalGapWidth = (imageCount - 1) * gap;
                        const totalBorderWidth = imageCount * borderWidth;
                        
                        const thumbSize = Math.max(0, Math.floor((containerWidth - totalGapWidth - totalBorderWidth) / imageCount));

                        generateData.images.forEach((imageUrl, index) => {
                            const thumb = document.createElement('img');
                            thumb.src = imageUrl;
                            thumb.style.width = `${thumbSize}px`;
                            thumb.style.height = `${thumbSize}px`;
                            thumb.style.objectFit = 'cover';
                            thumb.style.cursor = 'pointer';
                            thumb.style.borderRadius = '4px';
                            thumb.style.border = index === 0 ? `${border}px solid #007bff` : `${border}px solid transparent`;
                            
                            thumb.addEventListener('click', () => {
                                mainImage.src = imageUrl;
                                thumbnailContainer.querySelectorAll('img').forEach(t => t.style.border = `${border}px solid transparent`);
                                thumb.style.border = `${border}px solid #007bff`;
                            });
                            thumbnailContainer.appendChild(thumb);
                        });
                    } else {
                        errorMessage.textContent = `错误: ${generateData.error || '未能生成图片'}`;
                        errorMessage.style.display = 'block';
                    }
                })
                .catch(error => {
                    spinner.style.display = 'none';
                    errorMessage.textContent = `生图请求失败: ${error.message}`;
                    errorMessage.style.display = 'block';
                });
            } else {
                spinner.style.display = 'none';
                errorMessage.textContent = `错误: ${data.error || '未能启动反推任务'}`;
                errorMessage.style.display = 'block';
            }
        })
        .catch(error => {
            spinner.style.display = 'none';
            errorMessage.textContent = `请求失败: ${error.message}`;
            errorMessage.style.display = 'block';
        });
    }
});
