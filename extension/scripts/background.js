// 创建右键菜单
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "reverse-image-search",
    title: "反推这张图片",
    contexts: ["image"],
  });
});

// 监听右键菜单点击事件
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "reverse-image-search") {
    const imageUrl = info.srcUrl;

    // 注入 CSS
    chrome.scripting.insertCSS({
      target: { tabId: tab.id },
      files: ["styles/content.css"],
    });

    // 注入并执行 content script
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["scripts/content.js"],
    }).then(() => {
        // 发送消息到 content script
        chrome.tabs.sendMessage(tab.id, {
            action: "showModal",
            imageUrl: imageUrl
        });
    });
  }
});