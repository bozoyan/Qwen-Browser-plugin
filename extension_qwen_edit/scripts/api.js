// api.js - API调用模块

class ModelScopeAPI {
  constructor() {
    this.baseUrl = "https://api-inference.modelscope.cn/";
  }

  async getApiKey() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ action: "getApiKey" }, (response) => {
        resolve(response.token);
      });
    });
  }

  async getSettings() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ action: "getSettings" }, (response) => {
        resolve(response);
      });
    });
  }

  // 提交图片生成任务
  async submitEditTask(params, isQuickEdit = false) {
    const apiKey = await this.getApiKey();

    if (!apiKey) {
      throw new Error("请先设置ModelScope Token");
    }

    // 构建请求数据
    const requestData = {
      model: params.model || "Qwen/Qwen-Image-Edit-2511",
      prompt: params.prompt,
      size: params.size,
      image_url: params.image_url
    };

    // 如果不是快速编辑模式,添加可选参数
    if (!isQuickEdit) {
      if (params.negative_prompt) requestData.negative_prompt = params.negative_prompt;
      if (params.seed) requestData.seed = params.seed;
      if (params.steps) requestData.steps = params.steps;
      if (params.guidance) requestData.guidance = params.guidance;
      if (params.loras) requestData.loras = params.loras;
    }

    const response = await fetch(`${this.baseUrl}v1/images/generations`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "X-ModelScope-Async-Mode": "true"
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API请求失败: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.task_id;
  }

  // 轮询任务状态
  async pollTaskStatus(taskId, onProgress) {
    const apiKey = await this.getApiKey();
    const headers = {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "X-ModelScope-Task-Type": "image_generation"
    };

    let attempts = 0;
    const maxAttempts = 120; // 最多轮询10分钟

    while (attempts < maxAttempts) {
      try {
        const response = await fetch(`${this.baseUrl}v1/tasks/${taskId}`, {
          method: "GET",
          headers: headers
        });

        if (!response.ok) {
          throw new Error(`获取任务状态失败: ${response.status}`);
        }

        const data = await response.json();

        if (data.task_status === "SUCCEED") {
          return {
            status: "success",
            images: data.output_images || []
          };
        } else if (data.task_status === "FAILED") {
          return {
            status: "failed",
            error: "图片生成失败"
          };
        } else if (data.task_status === "PENDING" || data.task_status === "RUNNING") {
          // 任务进行中
          if (onProgress) {
            onProgress({
              status: data.task_status,
              taskId: taskId
            });
          }
        }

        attempts++;
        // 等待5秒后重试
        await new Promise(resolve => setTimeout(resolve, 5000));

      } catch (error) {
        console.error("轮询任务状态出错:", error);
        attempts++;
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }

    return {
      status: "timeout",
      error: "任务超时,请稍后到魔搭社区查看结果"
    };
  }

  // 完整的图片编辑流程
  async editImage(params, onProgress, isQuickEdit = false) {
    try {
      // 提交任务
      if (onProgress) {
        onProgress({ stage: "submitting", message: "正在提交任务..." });
      }

      const taskId = await this.submitEditTask(params, isQuickEdit);

      if (onProgress) {
        onProgress({ stage: "polling", message: "任务已提交,正在生成图片...", taskId: taskId });
      }

      // 轮询任务状态
      const result = await this.pollTaskStatus(taskId, (progress) => {
        if (onProgress) {
          onProgress({ stage: "generating", message: "正在生成图片...", ...progress });
        }
      });

      return result;

    } catch (error) {
      return {
        status: "error",
        error: error.message
      };
    }
  }
}

// 导出API实例
const modelScopeAPI = new ModelScopeAPI();
