"""Detection 业务服务层，连接既有分析工作流、知识库和公司网关。"""  # 说明服务层职责。

from __future__ import annotations  # 启用延迟类型注解。

import base64  # 将上传图片转换为网关可接受的 Data URL。
import uuid  # 生成会话和文件唯一编号。
from pathlib import Path  # 使用跨平台路径对象。
from typing import Any  # 引入通用 JSON 类型。

from agent.knowledge import KnowledgeBase  # 复用已有轻量知识检索能力。
from agent.workflow import DetectionAssistant  # 复用已有 Detection 分析工作流。

from .config import FAST_MODEL_NAME, KNOWLEDGE_DIR, LONG_CONTEXT_MODEL_NAME, UPLOAD_DIR, ensure_runtime_directories  # 导入项目路径配置。
from .database import Database  # 导入本地数据库访问类。
from .gateway import CompanyGatewayClient  # 导入公司网关适配器。
from .schemas import Citation  # 导入引用响应模型。


class DetectionService:  # 定义 Detection 业务服务。
    """封装问答、引用整理和图片解析能力。"""  # 说明服务职责。

    ALLOWED_UPLOAD_SUFFIXES = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".md", ".png", ".jpg", ".jpeg"}  # 定义允许进入审核队列的文件格式。
    MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 设置单个上传文件最大为 50 MB。

    def __init__(self) -> None:  # 初始化 Detection 服务。
        ensure_runtime_directories()  # 确保运行目录已经创建。
        self.assistant = DetectionAssistant(str(KNOWLEDGE_DIR))  # 创建本地 Detection 分析助手。
        self.knowledge = KnowledgeBase(KNOWLEDGE_DIR)  # 创建本地知识库检索器。
        self.gateway = CompanyGatewayClient()  # 创建公司网关客户端。
        self.database = Database()  # 创建用户和文件审核数据库。

    @staticmethod
    def _citation_from_evidence(evidence: dict[str, Any]) -> list[Citation]:  # 将工作流证据转换为引用列表。
        citations: list[Citation] = []  # 初始化引用列表。
        knowledge_docs = evidence.get("knowledge", [])  # 读取知识库结果。
        for document in knowledge_docs:  # 遍历知识库文档结果。
            citations.append(Citation(source_type="knowledge", title=document.get("title", "本地知识文档"), location=document.get("source"), excerpt=document.get("content", "")[:240]))  # 添加知识文档引用。
        lot = evidence.get("lot", {})  # 读取 lot 证据。
        if lot.get("found"):  # 判断 lot 是否有效。
            citations.append(Citation(source_type="lot", title=f"Lot {lot.get('lot_id', '')}", location="演示数据记录", excerpt=f"设备 {lot.get('tool', '')}，工艺 {lot.get('process', '')}"))  # 添加 lot 记录引用。
        defects = evidence.get("defects", {})  # 读取缺陷证据。
        if defects.get("found"):  # 判断缺陷数据是否有效。
            citations.append(Citation(source_type="defect", title="缺陷汇总", location="演示数据记录", excerpt=f"缺陷数 {defects.get('total')}，密度 {defects.get('density')}"))  # 添加缺陷汇总引用。
        spc = evidence.get("spc", {})  # 读取 SPC 证据。
        if spc.get("found"):  # 判断 SPC 数据是否有效。
            citations.append(Citation(source_type="spc", title=f"SPC {spc.get('tool_id', '')}", location="最近七个采样点", excerpt=spc.get("trend")))  # 添加 SPC 引用。
        return citations  # 返回整理后的引用列表。

    async def answer(self, query: str, session_id: str | None = None) -> dict[str, Any]:  # 处理用户问答请求。
        result = self.assistant.ask(query)  # 先调用本地可解释工作流得到结构化结果。
        evidence = result.get("evidence", {})  # 读取结构化证据。
        answer = result.get("answer", "当前无法生成回答")  # 读取本地回答作为默认结果。
        if self.gateway.configured:  # 判断公司网关是否已配置。
            prompt = "请基于以下 Detection 证据优化回答，保留专业中文、明确不确定性并禁止编造数据。\n" + str({"query": query, "evidence": evidence, "draft": answer})  # 组合网关提示词和本地证据。
            try:  # 尝试调用公司网关。
                selected_model = LONG_CONTEXT_MODEL_NAME if len(prompt) > 12000 else FAST_MODEL_NAME if result.get("intent") in {"spc", "alarm", "recipe"} else None  # 按问题复杂度选择长上下文、快速或主推理模型。
                answer = await self.gateway.chat([{ "role": "user", "content": prompt }], model=selected_model)  # 通过公司网关生成最终回答。
            except Exception:  # 捕获网关异常并保留本地兜底结果。
                answer = f"{answer}\n\n> 公司网关调用失败，以上为本地规则引擎结果。"  # 在回答中声明网关失败状态。
        return {"answer": answer, "session_id": session_id or str(uuid.uuid4()), "intent": result.get("intent", "unknown"), "citations": self._citation_from_evidence(evidence), "evidence": evidence}  # 返回统一接口结果。

    async def save_upload(self, filename: str, content_type: str, content: bytes, uploader_id: int) -> dict[str, Any]:  # 保存用户上传文件并创建待审核记录。
        file_id = str(uuid.uuid4())  # 生成上传文件编号。
        safe_name = Path(filename).name  # 去掉用户文件名中的路径部分。
        if Path(safe_name).suffix.lower() not in self.ALLOWED_UPLOAD_SUFFIXES:  # 检查文件后缀是否在允许列表中。
            raise ValueError("不支持的文件格式，请上传 PDF、Word、PPT、Excel、TXT、Markdown 或 PNG/JPG 文件")  # 拒绝不支持的文件格式。
        if len(content) > self.MAX_UPLOAD_BYTES:  # 检查文件大小是否超限。
            raise ValueError("文件大小不能超过 50 MB")  # 拒绝过大的文件。
        target = UPLOAD_DIR / f"{file_id}_{safe_name}"  # 生成安全的保存路径。
        target.write_bytes(content)  # 将文件内容写入本地上传目录。
        record = self.database.create_file({"id": file_id, "filename": safe_name, "stored_path": str(target), "content_type": content_type, "size": len(content), "uploader_id": uploader_id})  # 保存待审核文件记录。
        return {"file_id": file_id, "filename": safe_name, "content_type": content_type, "size": len(content), "message": "文件已上传，等待管理员审核", "status": record["status"]}  # 返回审核状态。

    async def analyze_image(self, filename: str, content_type: str, content: bytes) -> dict[str, Any]:  # 解析用户上传结构图。
        if not self.gateway.configured:  # 判断是否配置了视觉网关。
            return {"answer": "图片已接收，但尚未配置公司视觉模型网关。请设置 DETECTION_GATEWAY_BASE_URL、DETECTION_GATEWAY_API_KEY 和 DETECTION_VISION_MODEL。", "citations": []}  # 返回明确的配置提示。
        encoded = base64.b64encode(content).decode("ascii")  # 将图片编码为 ASCII Base64。
        data_url = f"data:{content_type};base64,{encoded}"  # 组成视觉模型可识别的 Data URL。
        prompt = "请解析这张晶圆厂 Detection 结构图，提取膜层顺序、厚度、标注文字和结构关系；不确定信息请明确标注。"  # 定义结构图解析提示词。
        answer = await self.gateway.vision(prompt, data_url)  # 调用公司视觉模型解析结构图。
        return {"answer": answer, "citations": [Citation(source_type="image", title=filename, location="用户上传图片", excerpt="视觉模型解析结果")]}  # 返回图片解析结果和引用。
