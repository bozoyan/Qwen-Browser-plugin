// static/js/api.js

async function uploadFile(file, onUploadProgress) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await axios.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: onUploadProgress
        });
        return response.data;
    } catch (error) {
        console.error('Upload error:', error);
        throw error.response ? new Error(error.response.data.error || '服务器错误') : error;
    }
}

async function analyzeImage(showSuccessToast = false) {
    try {
        const response = await axios.post('/analyze');
        if (response.data.success) {
            if (showSuccessToast) {
                showToast('图片分析成功！', 'success');
            }
            return { success: true, prompt: response.data.prompt };
        } else {
            throw new Error(response.data.error || '分析失败');
        }
    } catch (error) {
        console.error('分析图片时出错:', error);
        showToast('分析图片时出错: ' + error.message, 'danger');
        return { success: false, error: error.message };
    }
}

async function analyzeImageFromUrl(imageUrl) {
    try {
        showToast('正在分析网络图片...', 'info');
        const response = await axios.post('/analyze_from_url', { url: imageUrl });
        if (response.data.success) {
            showToast('网络图片分析成功！', 'success');
            return { success: true, prompt: response.data.prompt };
        } else {
            throw new Error(response.data.error || '网络图片分析失败');
        }
    } catch (error) {
        console.error('分析网络图片时出错:', error);
        showToast('分析网络图片时出错: ' + error.message, 'danger');
        return { success: false, error: error.message };
    }
}

async function generateQwenImage(prompt) {
    const requestData = {
        prompt: prompt,
    };

    try {
        showToast('正在提交生成任务...', 'info');
        const response = await axios.post('/api/generate_image', requestData);
        const data = response.data;

        if (!data.success) {
            throw new Error(data.error || '生成图片失败');
        }

        // 新的API直接返回图片，不需要轮询
        if (data.images && data.images.length > 0) {
            console.log(`图片生成成功，获取到${data.images.length}张图片`);
            return data.images;
        } else {
            throw new Error('生成成功但未获取到图片');
        }
    } catch (error) {
        console.error(`生成图片时出错: ${error.message}`);
        throw error;
    }
}