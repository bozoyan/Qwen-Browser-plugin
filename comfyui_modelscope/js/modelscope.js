import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// 注册自定义节点类型
app.registerExtension({
    name: "comfyui_modelscope",
    
    async setup() {
        // 添加自定义菜单选项
        const menu = document.querySelector(".comfy-menu");
        const separator = document.createElement("hr");
        separator.className = "comfy-menu-separator";
        menu.appendChild(separator);
        
        const modelScopeButton = document.createElement("button");
        modelScopeButton.textContent = "ModelScope 配置";
        modelScopeButton.onclick = () => {
            showConfigDialog();
        };
        menu.appendChild(modelScopeButton);
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 为ModelScope节点添加自定义行为
        if (nodeData.name === "ModelScopeImageNode") {
            // 重写onNodeCreated方法
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const ret = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                // 在这里可以添加其他自定义行为，但不要添加输入端口
                // 因为输入端口已经在INPUT_TYPES中定义了
                
                return ret;
            };
        }
    }
});

// 显示配置对话框
function showConfigDialog() {
    const dialog = document.createElement("dialog");
    dialog.style.width = "500px";
    dialog.style.padding = "20px";
    
    const title = document.createElement("h3");
    title.textContent = "ModelScope 配置";
    dialog.appendChild(title);
    
    // API Key输入
    const apiKeyLabel = document.createElement("label");
    apiKeyLabel.textContent = "API Key:";
    apiKeyLabel.style.display = "block";
    apiKeyLabel.style.marginTop = "10px";
    dialog.appendChild(apiKeyLabel);
    
    const apiKeyInput = document.createElement("input");
    apiKeyInput.type = "password";
    apiKeyInput.style.width = "100%";
    apiKeyInput.style.marginBottom = "10px";
    dialog.appendChild(apiKeyInput);
    
    // Cookie输入
    const cookieLabel = document.createElement("label");
    cookieLabel.textContent = "ModelScope Cookie:";
    cookieLabel.style.display = "block";
    cookieLabel.style.marginTop = "10px";
    dialog.appendChild(cookieLabel);
    
    const cookieInput = document.createElement("textarea");
    cookieInput.style.width = "100%";
    cookieInput.style.height = "100px";
    cookieInput.style.marginBottom = "10px";
    dialog.appendChild(cookieInput);
    
    // 按钮区域
    const buttonContainer = document.createElement("div");
    buttonContainer.style.display = "flex";
    buttonContainer.style.justifyContent = "flex-end";
    buttonContainer.style.marginTop = "20px";
    
    const saveButton = document.createElement("button");
    saveButton.textContent = "保存";
    saveButton.style.marginRight = "10px";
    saveButton.onclick = async () => {
        try {
            await saveConfig(apiKeyInput.value, cookieInput.value);
            dialog.close();
            alert("配置已保存");
        } catch (error) {
            alert("保存配置失败: " + error.message);
        }
    };
    
    const cancelButton = document.createElement("button");
    cancelButton.textContent = "取消";
    cancelButton.onclick = () => {
        dialog.close();
    };
    
    buttonContainer.appendChild(saveButton);
    buttonContainer.appendChild(cancelButton);
    dialog.appendChild(buttonContainer);
    
    // 加载当前配置
    loadConfig().then(config => {
        apiKeyInput.value = config.api_key || "";
        cookieInput.value = config.model_scope_cookie || "";
    });
    
    document.body.appendChild(dialog);
    dialog.showModal();
}

// 保存配置
function saveConfig(apiKey, cookie) {
    try {
        localStorage.setItem("modelscope_api_key", apiKey);
        localStorage.setItem("modelscope_cookie", cookie);
        console.log("配置已保存到本地存储");
    } catch (error) {
        console.error("保存配置失败:", error);
        throw new Error(error.message || "保存配置失败");
    }
}

// 加载配置
function loadConfig() {
    try {
        return {
            api_key: localStorage.getItem("modelscope_api_key") || "",
            model_scope_cookie: localStorage.getItem("modelscope_cookie") || ""
        };
    } catch (error) {
        console.error("加载配置失败:", error);
        return {
            api_key: "",
            model_scope_cookie: ""
        };
    }
}