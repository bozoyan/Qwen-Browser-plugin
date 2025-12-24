// sidebar.js - 侧边栏逻辑

// 全局状态
let currentImageUrl = null;
let currentImageSize = { width: 1280, height: 1920 };
let currentTaskId = null;
let uploadedImageCount = 0; // 已上传图片数量
let countdownInterval = null; // 读秒计时器

// DOM元素
const quickEditSection = document.getElementById("quickEditSection");
const customEditSection = document.getElementById("customEditSection");
const settingsPanel = document.getElementById("settingsPanel");

// 初始化
document.addEventListener("DOMContentLoaded", () => {
  initializeEventListeners();
  loadSettings();

  // 监听来自background的消息
  chrome.runtime.onMessage.addListener((request) => {
    if (request.action === "editImage") {
      handleEditImage(request.imageUrl);
    }
  });
});

// 初始化事件监听器
function initializeEventListeners() {
  // 设置按钮
  document.getElementById("settingsBtn").addEventListener("click", openSettings);
  document.getElementById("closeSettings").addEventListener("click", closeSettings);

  // 快速编辑
  document.getElementById("submitEditBtn").addEventListener("click", submitQuickEdit);
  document.getElementById("downloadAllBtn").addEventListener("click", downloadAllImages);

  // 自定义编辑
  document.getElementById("addImageBtn").addEventListener("click", addImageInput);
  document.getElementById("submitCustomBtn").addEventListener("click", submitCustomEdit);
  document.getElementById("presetResolution").addEventListener("change", handleResolutionChange);

  // 图片上传相关
  initializeImageUpload();

  // Tab切换
  initializeTabs();

  // 设置
  document.getElementById("saveSettings").addEventListener("click", saveSettings);
  document.getElementById("resetSettings").addEventListener("click", resetSettings);
  document.getElementById("modelSelect").addEventListener("change", handleModelChange);
  document.getElementById("toggleTokenVisibility").addEventListener("click", toggleTokenVisibility);
  document.getElementById("apiToken").addEventListener("input", validateToken);
}

// 处理编辑图片(从右键菜单触发)
async function handleEditImage(imageUrl) {
  currentImageUrl = imageUrl;

  // 显示原图
  document.getElementById("originalImage").src = imageUrl;

  // 尝试获取图片尺寸
  try {
    const response = await fetch(imageUrl, { method: "HEAD" });
    const contentType = response.headers.get("Content-Type");

    // 加载图片获取实际尺寸
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      currentImageSize = { width: img.width, height: img.height };
      document.getElementById("imageInfo").textContent =
        `尺寸: ${img.width} x ${img.height} | 类型: ${contentType}`;
    };
    img.onerror = () => {
      document.getElementById("imageInfo").textContent = "无法获取图片尺寸";
    };
    img.src = imageUrl;

  } catch (error) {
    document.getElementById("imageInfo").textContent = "图片URL无效";
  }

  // 显示快速编辑区域
  quickEditSection.style.display = "block";
  customEditSection.style.display = "none";
}

// 提交快速编辑
async function submitQuickEdit() {
  const prompt = document.getElementById("editPrompt").value.trim();

  if (!prompt) {
    showToast("请输入编辑提示词", "error");
    return;
  }

  if (!currentImageUrl) {
    showToast("没有可编辑的图片", "error");
    return;
  }

  // 禁用按钮
  const submitBtn = document.getElementById("submitEditBtn");
  submitBtn.disabled = true;

  // 显示进度并启动读秒
  showProgress("正在提交任务...");
  startCountdown();

  try {
    // 获取设置
    const settings = await modelScopeAPI.getSettings();

    // 使用图片原始尺寸
    const size = `${currentImageSize.width}x${currentImageSize.height}`;

    // 调用API(快速编辑模式,只使用基础参数)
    const result = await modelScopeAPI.editImage({
      model: settings.selectedModel,
      prompt: prompt,
      size: size,
      image_url: [currentImageUrl]
    }, (progress) => {
      updateProgress(progress);
    }, true); // isQuickEdit = true

    handleResult(result);

  } catch (error) {
    showToast(`错误: ${error.message}`, "error");
    hideProgress();
    stopCountdown();
  } finally {
    submitBtn.disabled = false;
  }
}

// 提交自定义编辑
async function submitCustomEdit() {
  const imageInputs = document.querySelectorAll(".image-url-input");
  const imageUrls = Array.from(imageInputs)
    .map(input => input.value.trim())
    .filter(url => url !== "");

  const prompt = document.getElementById("customPrompt").value.trim();

  if (imageUrls.length === 0) {
    showToast("请输入至少一个图片URL", "error");
    return;
  }

  if (!prompt) {
    showToast("请输入正向提示词", "error");
    return;
  }

  // 获取分辨率
  let size;
  const presetValue = document.getElementById("presetResolution").value;
  if (presetValue === "custom") {
    const width = document.getElementById("customWidth").value;
    const height = document.getElementById("customHeight").value;
    if (!width || !height) {
      showToast("请输入自定义分辨率", "error");
      return;
    }
    size = `${width}x${height}`;
  } else if (presetValue) {
    size = presetValue;
  } else {
    showToast("请选择分辨率", "error");
    return;
  }

  // 禁用按钮
  const submitBtn = document.getElementById("submitCustomBtn");
  submitBtn.disabled = true;

  // 显示进度并启动读秒
  showProgress("正在生成图片...");
  startCountdown();

  try {
    // 获取设置
    const settings = await modelScopeAPI.getSettings();

    // 构建参数
    const params = {
      model: settings.selectedModel,
      prompt: prompt,
      size: size,
      image_url: imageUrls
    };

    // 添加可选参数
    const negativePrompt = document.getElementById("negativePrompt").value.trim();
    if (negativePrompt) {
      params.negative_prompt = negativePrompt;
    }

    const steps = document.getElementById("steps").value;
    if (steps) {
      params.steps = parseInt(steps);
    }

    const guidance = document.getElementById("guidance").value;
    if (guidance) {
      params.guidance = parseFloat(guidance);
    }

    const seed = document.getElementById("seed").value;
    if (seed) {
      params.seed = parseInt(seed);
    }

    // 调用API(自定义编辑模式,使用所有参数)
    const result = await modelScopeAPI.editImage(params, (progress) => {
      updateProgress(progress);
    }, false); // isQuickEdit = false

    handleCustomResult(result);

  } catch (error) {
    showToast(`错误: ${error.message}`, "error");
    hideProgress();
    stopCountdown();
  } finally {
    submitBtn.disabled = false;
  }
}

// 处理结果
function handleResult(result) {
  hideProgress();
  stopCountdown();

  if (result.status === "success") {
    const resultImages = document.getElementById("resultImages");
    resultImages.innerHTML = "";

    result.images.forEach((imageUrl, index) => {
      const img = document.createElement("img");
      img.src = imageUrl;
      img.alt = `生成结果 ${index + 1}`;
      img.addEventListener("click", () => {
        window.open(imageUrl, "_blank");
      });
      resultImages.appendChild(img);
    });

    document.getElementById("editResult").style.display = "block";
    showToast("图片生成成功!", "success");
  } else {
    showToast(`生成失败: ${result.error}`, "error");
  }
}

// 处理自定义结果
function handleCustomResult(result) {
  hideProgress();
  stopCountdown();

  if (result.status === "success") {
    const resultImages = document.getElementById("customResultImages");
    resultImages.innerHTML = "";

    result.images.forEach((imageUrl, index) => {
      const img = document.createElement("img");
      img.src = imageUrl;
      img.alt = `生成结果 ${index + 1}`;
      img.addEventListener("click", () => {
        window.open(imageUrl, "_blank");
      });
      resultImages.appendChild(img);
    });

    document.getElementById("customResult").style.display = "block";
    showToast("图片生成成功!", "success");
  } else {
    showToast(`生成失败: ${result.error}`, "error");
  }
}

// 添加图片输入
function addImageInput() {
  const imageInputs = document.getElementById("imageInputs");
  const input = document.createElement("input");
  input.type = "text";
  input.className = "image-url-input";
  input.placeholder = "输入图片URL";
  imageInputs.appendChild(input);
}

// 处理分辨率变化
function handleResolutionChange(e) {
  const customResolution = document.getElementById("customResolution");
  if (e.target.value === "custom") {
    customResolution.style.display = "flex";
  } else {
    customResolution.style.display = "none";
  }
}

// 处理模型选择变化
function handleModelChange(e) {
  const customModel = document.getElementById("customModel");
  if (e.target.value === "custom") {
    customModel.style.display = "block";
  } else {
    customModel.style.display = "none";
  }
}

// 显示进度
function showProgress(message) {
  const progressSection = document.getElementById("editProgress");
  const progressInfo = document.getElementById("progressInfo");
  progressInfo.textContent = message;
  progressSection.style.display = "block";
}

// 更新进度
function updateProgress(progress) {
  const progressInfo = document.getElementById("progressInfo");
  const taskInfo = document.getElementById("taskInfo");

  if (progress.message) {
    progressInfo.textContent = progress.message;
  }

  if (progress.taskId) {
    currentTaskId = progress.taskId;
    taskInfo.textContent = `任务ID: ${progress.taskId}`;
  }
}

// 启动读秒计时器
function startCountdown() {
  let seconds = 0;
  const progressInfo = document.getElementById("progressInfo");

  // 清除之前的计时器
  if (countdownInterval) {
    clearInterval(countdownInterval);
  }

  // 每秒更新一次
  countdownInterval = setInterval(() => {
    seconds++;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    const timeString = minutes > 0 ? `${minutes}分${secs}秒` : `${secs}秒`;

    // 保留原始消息,添加时间
    const originalMessage = progressInfo.textContent.split(" (")[0];
    progressInfo.textContent = `${originalMessage} (已等待: ${timeString})`;
  }, 1000);
}

// 停止读秒计时器
function stopCountdown() {
  if (countdownInterval) {
    clearInterval(countdownInterval);
    countdownInterval = null;
  }
}

// 隐藏进度
function hideProgress() {
  document.getElementById("editProgress").style.display = "none";
  stopCountdown();
}

// 下载所有图片
function downloadAllImages() {
  const images = document.querySelectorAll("#resultImages img");
  images.forEach((img, index) => {
    setTimeout(() => {
      const link = document.createElement("a");
      link.href = img.src;
      link.download = `qwen-edit-${index + 1}.jpg`;
      link.click();
    }, index * 500);
  });
}

// 打开设置
function openSettings() {
  settingsPanel.style.display = "block";
}

// 关闭设置
function closeSettings() {
  settingsPanel.style.display = "none";
}

// 加载设置
async function loadSettings() {
  const settings = await modelScopeAPI.getSettings();

  if (settings.modelScopeToken) {
    document.getElementById("apiToken").value = settings.modelScopeToken;
  }

  if (settings.selectedModel) {
    document.getElementById("modelSelect").value = settings.selectedModel;
    if (settings.selectedModel === "custom") {
      document.getElementById("customModel").style.display = "block";
    }
  }

  if (settings.imageWidth) {
    document.getElementById("defaultWidth").value = settings.imageWidth;
  }

  if (settings.imageHeight) {
    document.getElementById("defaultHeight").value = settings.imageHeight;
  }

  if (settings.customPrompt) {
    document.getElementById("customPrompt").value = settings.customPrompt;
  }
}

// 保存设置
function saveSettings() {
  const modelSelect = document.getElementById("modelSelect").value;
  let selectedModel = modelSelect;

  if (modelSelect === "custom") {
    const customModel = document.getElementById("customModel").value.trim();
    if (!customModel) {
      showToast("请输入自定义模型ID", "error");
      return;
    }
    selectedModel = customModel;
  }

  const settings = {
    modelScopeToken: document.getElementById("apiToken").value.trim(),
    selectedModel: selectedModel,
    imageWidth: parseInt(document.getElementById("defaultWidth").value),
    imageHeight: parseInt(document.getElementById("defaultHeight").value),
    customPrompt: document.getElementById("customPrompt").value.trim()
  };

  chrome.runtime.sendMessage({
    action: "saveSettings",
    settings: settings
  }, (response) => {
    if (response.success) {
      showToast("设置已保存", "success");
      closeSettings();
    }
  });
}

// 重置设置
function resetSettings() {
  document.getElementById("apiToken").value = "";
  document.getElementById("modelSelect").value = "Qwen/Qwen-Image-Edit-2511";
  document.getElementById("customModel").style.display = "none";
  document.getElementById("defaultWidth").value = 1280;
  document.getElementById("defaultHeight").value = 1920;
  document.getElementById("customPrompt").value = "";

  showToast("设置已重置", "info");
}

// 显示Toast通知
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  // 3秒后自动移除
  setTimeout(() => {
    toast.style.animation = "slide-in 0.3s ease-out reverse";
    setTimeout(() => {
      container.removeChild(toast);
    }, 300);
  }, 3000);
}

// ============ 图片上传和缩略图功能 ============

// 存储已上传的图片
let uploadedImages = [];

// 初始化图片上传功能
function initializeImageUpload() {
  const uploadArea = document.getElementById("uploadArea");
  const fileInput = document.getElementById("fileInput");

  // 点击上传区域
  uploadArea.addEventListener("click", () => {
    fileInput.click();
  });

  // 文件选择
  fileInput.addEventListener("change", (e) => {
    handleFiles(e.target.files);
  });

  // 拖拽上传
  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("dragover");
  });

  uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("dragover");
  });

  uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("dragover");
    handleFiles(e.dataTransfer.files);
  });

  // URL添加按钮
  const addUrlBtns = document.querySelectorAll(".btn-add-url");
  addUrlBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const input = btn.parentElement.querySelector(".image-url-input");
      const url = input.value.trim();
      if (url) {
        addImageUrl(url);
        input.value = "";
      }
    });
  });
}

// 处理文件上传
function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (!file.type.startsWith("image/")) {
      showToast("请选择图片文件", "error");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      addImageThumbnail(e.target.result, "local");
    };
    reader.readAsDataURL(file);
  });
}

// 添加图片URL
function addImageUrl(url) {
  // 验证URL
  try {
    new URL(url);
    addImageThumbnail(url, "url");
  } catch {
    showToast("请输入有效的URL", "error");
  }
}

// 添加图片缩略图
function addImageThumbnail(src, type) {
  uploadedImages.push({ src, type, id: Date.now() });
  renderThumbnails();
}

// 渲染缩略图列表
function renderThumbnails() {
  const container = document.getElementById("imageThumbnails");
  container.innerHTML = "";

  uploadedImages.forEach((img, index) => {
    const item = document.createElement("div");
    item.className = "thumbnail-item";

    const image = document.createElement("img");
    image.src = img.src;
    image.alt = `图片${index + 1}`;

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-btn";
    deleteBtn.innerHTML = "×";
    deleteBtn.title = "删除图片";
    deleteBtn.onclick = () => removeImage(img.id);

    const badge = document.createElement("span");
    badge.className = "image-type-badge";
    badge.textContent = img.type === "local" ? "本地" : "URL";

    item.appendChild(image);
    item.appendChild(deleteBtn);
    item.appendChild(badge);
    container.appendChild(item);
  });
}

// 删除图片
function removeImage(id) {
  uploadedImages = uploadedImages.filter(img => img.id !== id);
  renderThumbnails();
}

// 初始化Tab切换
function initializeTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      // 移除所有active状态
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      // 添加active状态
      btn.classList.add("active");
      const tabName = btn.dataset.tab;
      document.getElementById(`${tabName}Tab`).classList.add("active");
    });
  });
}

// 修改submitCustomEdit函数以使用上传的图片
// 需要先删除旧的函数定义
const originalSubmitCustomEdit = submitCustomEdit;

submitCustomEdit = async function() {
  // 如果有上传的图片,使用上传的图片
  if (uploadedImages.length > 0) {
    const imageUrls = uploadedImages.map(img => img.src);

    const prompt = document.getElementById("customPrompt").value.trim();

    if (imageUrls.length === 0) {
      showToast("请添加至少一张图片", "error");
      return;
    }

    if (!prompt) {
      showToast("请输入正向提示词", "error");
      return;
    }

    // 获取分辨率
    let size;
    const presetValue = document.getElementById("presetResolution").value;
    if (presetValue === "custom") {
      const width = document.getElementById("customWidth").value;
      const height = document.getElementById("customHeight").value;
      if (!width || !height) {
        showToast("请输入自定义分辨率", "error");
        return;
      }
      size = `${width}x${height}`;
    } else if (presetValue) {
      size = presetValue;
    } else {
      showToast("请选择分辨率", "error");
      return;
    }

    // 禁用按钮
    const submitBtn = document.getElementById("submitCustomBtn");
    submitBtn.disabled = true;

    // 显示进度并启动读秒
    showProgress("正在生成图片...");
    startCountdown();

    try {
      // 获取设置
      const settings = await modelScopeAPI.getSettings();

      // 构建参数
      const params = {
        model: settings.selectedModel,
        prompt: prompt,
        size: size,
        image_url: imageUrls
      };

      // 添加可选参数
      const negativePrompt = document.getElementById("negativePrompt").value.trim();
      if (negativePrompt) {
        params.negative_prompt = negativePrompt;
      }

      const steps = document.getElementById("steps").value;
      if (steps) {
        params.steps = parseInt(steps);
      }

      const guidance = document.getElementById("guidance").value;
      if (guidance) {
        params.guidance = parseFloat(guidance);
      }

      const seed = document.getElementById("seed").value;
      if (seed) {
        params.seed = parseInt(seed);
      }

      // 调用API
      const result = await modelScopeAPI.editImage(params, (progress) => {
        updateProgress(progress);
      }, false);

      handleCustomResult(result);

    } catch (error) {
      showToast(`错误: ${error.message}`, "error");
      hideProgress();
      stopCountdown();
    } finally {
      submitBtn.disabled = false;
    }
  } else {
    // 使用原来的URL输入方式
    const imageInputs = document.querySelectorAll(".image-url-input");
    const imageUrls = Array.from(imageInputs)
      .map(input => input.value.trim())
      .filter(url => url !== "");

    if (imageUrls.length === 0) {
      showToast("请输入至少一个图片URL或上传图片", "error");
      return;
    }

    // 调用原始函数的剩余部分
    await originalSubmitCustomEdit();
  }
};

// ============ Token显示功能 ============

// 切换Token可见性
function toggleTokenVisibility() {
  const input = document.getElementById("apiToken");
  const icon = document.querySelector(".eye-icon");

  if (input.type === "password") {
    input.type = "text";
    icon.textContent = "🙈";
  } else {
    input.type = "password";
    icon.textContent = "👁️";
  }
}

// 验证Token并更新状态
function validateToken() {
  const input = document.getElementById("apiToken");
  const status = document.getElementById("tokenStatus");
  const statusIcon = status.querySelector(".status-icon");
  const statusText = status.querySelector(".status-text");

  const token = input.value.trim();

  if (token.length === 0) {
    status.className = "token-status";
    statusIcon.textContent = "⚠️";
    statusText.textContent = "未设置Token";
  } else if (token.length < 20) {
    status.className = "token-status invalid";
    statusIcon.textContent = "❌";
    statusText.textContent = "Token格式不正确(太短)";
  } else {
    status.className = "token-status valid";
    statusIcon.textContent = "✅";
    statusText.textContent = "Token已设置";
  }
}

// 修改loadSettings函数以加载Token
const originalLoadSettings = loadSettings;

loadSettings = async function() {
  const settings = await modelScopeAPI.getSettings();

  // 加载Token
  if (settings.modelScopeToken) {
    const tokenInput = document.getElementById("apiToken");
    tokenInput.value = settings.modelScopeToken;
    validateToken();
  }

  // 加载其他设置
  if (settings.selectedModel) {
    document.getElementById("modelSelect").value = settings.selectedModel;
    if (settings.selectedModel === "custom") {
      document.getElementById("customModel").style.display = "block";
    }
  }

  if (settings.imageWidth) {
    document.getElementById("defaultWidth").value = settings.imageWidth;
  }

  if (settings.imageHeight) {
    document.getElementById("defaultHeight").value = settings.imageHeight;
  }

  if (settings.customPrompt) {
    document.getElementById("customPrompt").value = settings.customPrompt;
  }
};

// 修改saveSettings函数
const originalSaveSettings = saveSettings;

saveSettings = function() {
  const modelSelect = document.getElementById("modelSelect").value;
  let selectedModel = modelSelect;

  if (modelSelect === "custom") {
    const customModel = document.getElementById("customModel").value.trim();
    if (!customModel) {
      showToast("请输入自定义模型ID", "error");
      return;
    }
    selectedModel = customModel;
  }

  const token = document.getElementById("apiToken").value.trim();

  // 验证Token
  if (!token) {
    showToast("请输入ModelScope Token", "error");
    return;
  }

  if (token.length < 20) {
    showToast("Token格式不正确,请检查", "error");
    return;
  }

  const settings = {
    modelScopeToken: token,
    selectedModel: selectedModel,
    imageWidth: parseInt(document.getElementById("defaultWidth").value),
    imageHeight: parseInt(document.getElementById("defaultHeight").value),
    customPrompt: document.getElementById("customPrompt").value.trim()
  };

  chrome.runtime.sendMessage({
    action: "saveSettings",
    settings: settings
  }, (response) => {
    if (response.success) {
      showToast("设置已保存", "success");
      closeSettings();
    }
  });
};

// 修改resetSettings函数
const originalResetSettings = resetSettings;

resetSettings = function() {
  document.getElementById("apiToken").value = "";
  document.getElementById("modelSelect").value = "Qwen/Qwen-Image-Edit-2511";
  document.getElementById("customModel").style.display = "none";
  document.getElementById("defaultWidth").value = 1280;
  document.getElementById("defaultHeight").value = 1920;
  document.getElementById("customPrompt").value = "";

  // 重置Token状态
  validateToken();

  showToast("设置已重置", "info");
};
