"""公司 AI 网关适配器。

部署时只需要在这里对齐公司的鉴权头、路径和请求字段，业务 Agent 不直接依赖具体厂商 SDK。
"""  # 说明网关适配器边界。

from __future__ import annotations  # 启用延迟类型注解。

from typing import Any  # 引入通用 JSON 类型。

import httpx  # 使用异步 HTTP 客户端访问公司网关。

from .config import (  # 导入集中配置。
    CHAT_COMPLETIONS_PATH,  # 导入文本和视觉接口路径。
    CHAT_MODEL_NAME,  # 导入文本模型名称。
    EMBEDDINGS_PATH,  # 导入向量接口路径。
    EMBEDDING_MODEL_NAME,  # 导入向量模型名称。
    GATEWAY_API_KEY,  # 导入网关密钥。
    GATEWAY_BASE_URL,  # 导入网关基础地址。
    GATEWAY_TIMEOUT_SECONDS,  # 导入请求超时时间。
    VISION_MODEL_NAME,  # 导入视觉模型名称。
)


class CompanyGatewayClient:  # 定义统一公司网关客户端。
    """为文本模型和视觉模型提供统一调用入口。"""  # 说明客户端职责。

    def __init__(self) -> None:  # 初始化网关客户端。
        self.base_url = GATEWAY_BASE_URL.rstrip("/")  # 保存无尾斜杠的网关地址。
        self.api_key = GATEWAY_API_KEY  # 保存网关鉴权密钥。
        self.timeout = GATEWAY_TIMEOUT_SECONDS  # 保存请求超时时间。

    @property
    def configured(self) -> bool:  # 判断公司网关是否配置完整。
        return bool(self.base_url and self.api_key)  # 地址和密钥都有值时才认为已配置。

    def _headers(self) -> dict[str, str]:  # 构造公司网关请求头。
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}  # 默认使用 Bearer 鉴权。

    async def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:  # 调用公司文本模型。
        if not self.configured:  # 判断是否还没有配置公司网关。
            raise RuntimeError("公司 AI 网关尚未配置，请设置 DETECTION_GATEWAY_BASE_URL 和 DETECTION_GATEWAY_API_KEY")  # 返回明确配置错误。
        payload: dict[str, Any] = {"model": model or CHAT_MODEL_NAME, "messages": messages, "temperature": 0.1}  # 构造 OpenAI 兼容请求体。
        async with httpx.AsyncClient(timeout=self.timeout) as client:  # 创建异步 HTTP 客户端。
            response = await client.post(f"{self.base_url}{CHAT_COMPLETIONS_PATH}", headers=self._headers(), json=payload)  # 发送文本请求。
        response.raise_for_status()  # 将网关 HTTP 错误转换为异常。
        data = response.json()  # 解析网关 JSON 响应。
        return str(data["choices"][0]["message"]["content"])  # 提取 OpenAI 兼容格式中的回答文本。

    async def vision(self, prompt: str, image_data_url: str, model: str | None = None) -> str:  # 调用公司视觉模型。
        if not self.configured:  # 判断是否还没有配置公司网关。
            raise RuntimeError("公司 AI 网关尚未配置，暂时无法调用图片解析模型")  # 返回明确配置错误。
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_data_url}}]  # 构造多模态消息内容。
        payload: dict[str, Any] = {"model": model or VISION_MODEL_NAME, "messages": [{"role": "user", "content": content}], "temperature": 0.1}  # 构造视觉请求体。
        async with httpx.AsyncClient(timeout=self.timeout) as client:  # 创建异步 HTTP 客户端。
            response = await client.post(f"{self.base_url}{CHAT_COMPLETIONS_PATH}", headers=self._headers(), json=payload)  # 发送视觉请求。
        response.raise_for_status()  # 将网关 HTTP 错误转换为异常。
        data = response.json()  # 解析网关 JSON 响应。
        return str(data["choices"][0]["message"]["content"])  # 提取视觉模型回答文本。

    async def embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:  # 调用公司 Embedding 模型生成向量。
        if not self.configured:  # 判断是否还没有配置公司网关。
            raise RuntimeError("公司 AI 网关尚未配置，暂时无法生成知识库向量")  # 返回明确的配置错误。
        payload: dict[str, Any] = {"model": model or EMBEDDING_MODEL_NAME, "input": texts}  # 构造 OpenAI 兼容向量请求体。
        async with httpx.AsyncClient(timeout=self.timeout) as client:  # 创建异步 HTTP 客户端。
            response = await client.post(f"{self.base_url}{EMBEDDINGS_PATH}", headers=self._headers(), json=payload)  # 发送向量生成请求。
        response.raise_for_status()  # 将网关 HTTP 错误转换为异常。
        data = response.json()  # 解析向量接口 JSON 响应。
        return [list(item["embedding"]) for item in data["data"]]  # 提取每条输入对应的向量。
