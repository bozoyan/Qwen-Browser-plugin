// 从cookie中提取csrf token，支持多种格式
function extractCsrfToken(cookie) {
    // 尝试从csrf_token格式提取
    let match = cookie.match(/csrf_token=([^;]+)/);
    if (match && match[1]) {
        return match[1];
    }
    
    // 尝试从csrftoken格式提取（标准Django格式）
    match = cookie.match(/csrftoken=([^;]+)/);
    if (match && match[1]) {
        return match[1];
    }
    
    // 尝试从csrf_session格式提取
    match = cookie.match(/csrf_session=([^;]+)/);
    if (match && match[1]) {
        return match[1];
    }
    
    return '';
}

// 生成trace id
function generateTraceId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}