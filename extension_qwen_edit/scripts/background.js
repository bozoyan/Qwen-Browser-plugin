// background.js - 后台服务脚本

// 创建右键菜单
chrome.runtime.onInstalled.addListener(() => {
  // 创建图片编辑菜单项
  chrome.contextMenus.create({
    id: "editImageWithQwen",
    title: "使用Qwen编辑图片",
    contexts: ["image"],
    documentUrlPatterns: ["<all_urls>"]
  });

  console.log("Qwen图片编辑工具已安装");
});

// 监听右键菜单点击事件
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "editImageWithQwen") {
    // 获取图片URL和尺寸信息
    const imageUrl = info.srcUrl;

    // 打开侧边栏并发送消息
    chrome.sidePanel.open({ windowId: tab.windowId }).then(() => {
      // 延迟发送消息,确保侧边栏已打开
      setTimeout(() => {
        chrome.runtime.sendMessage({
          action: "editImage",
          imageUrl: imageUrl,
          sourceTabId: tab.id
        });
      }, 500);
    });
  }
});

// 监听插件图标点击事件
chrome.action.onClicked.addListener((tab) => {
  // 打开侧边栏
  chrome.sidePanel.open({ windowId: tab.windowId });
});

// 监听来自content script和sidebar的消息
chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request.action === "getApiKey") {
    // 获取API Key从storage
    chrome.storage.local.get(["modelScopeToken"], (result) => {
      const token = result.modelScopeToken || "";
      sendResponse({ token: token });
    });
    return true; // 保持消息通道开放
  }

  if (request.action === "saveApiKey") {
    chrome.storage.local.set({ modelScopeToken: request.token }, () => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === "getSettings") {
    chrome.storage.local.get(
      [
        "modelScopeToken",
        "selectedModel",
        "imageWidth",
        "imageHeight",
        "customPrompt"
      ],
      (result) => {
        sendResponse({
          modelScopeToken: result.modelScopeToken || "",
          selectedModel: result.selectedModel || "Qwen/Qwen-Image-Edit-2511",
          imageWidth: result.imageWidth || 1280,
          imageHeight: result.imageHeight || 1920,
          customPrompt: result.customPrompt || ""
        });
      }
    );
    return true;
  }

  if (request.action === "saveSettings") {
    chrome.storage.local.set(request.settings, () => {
      sendResponse({ success: true });
    });
    return true;
  }
});
