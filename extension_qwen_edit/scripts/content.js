// content.js - 内容脚本,用于在页面中捕获图片信息

// 监听来自background的请求
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getImageInfo") {
    // 获取页面中图片的详细信息
    const img = document.querySelector(`img[src="${request.imageUrl}"]`);
    if (img) {
      const imageInfo = {
        url: request.imageUrl,
        width: img.naturalWidth,
        height: img.naturalHeight
      };
      sendResponse({ imageInfo: imageInfo });
    } else {
      sendResponse({ imageInfo: null });
    }
  }
  return true;
});

// 监听图片右键点击事件,获取图片尺寸
document.addEventListener("contextmenu", (e) => {
  if (e.target.tagName === "IMG") {
    const img = e.target;
    const imageInfo = {
      url: img.src,
      width: img.naturalWidth,
      height: img.naturalHeight
    };

    // 临时存储图片信息
    sessionStorage.setItem("selectedImageInfo", JSON.stringify(imageInfo));
  }
}, true);
