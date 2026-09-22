"""FastAPI 应用入口。"""  # 说明 API 入口文件职责。

from __future__ import annotations  # 启用延迟类型注解。

from fastapi import FastAPI, File, UploadFile  # 引入 FastAPI 应用和文件上传类型。
from fastapi.middleware.cors import CORSMiddleware  # 引入跨域中间件。

from .config import GATEWAY_BASE_URL  # 导入网关地址配置，用于健康检查。
from .schemas import ChatRequest, ChatResponse, HealthResponse, UploadResponse  # 导入接口模型。
from .service import DetectionService  # 导入 Detection 业务服务。


app = FastAPI(title="DetectionAI Assistant API", version="0.1.0")  # 创建 FastAPI 应用实例。
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])  # 允许本地前端访问后端接口。
service = DetectionService()  # 创建全局业务服务实例。


@app.get("/api/health", response_model=HealthResponse)  # 注册健康检查接口。
async def health() -> HealthResponse:  # 返回后端运行状态。
    return HealthResponse(status="ok", gateway_configured=bool(GATEWAY_BASE_URL), local_fallback_enabled=True)  # 返回服务和网关状态。


@app.post("/api/chat", response_model=ChatResponse)  # 注册 Detection 对话接口。
async def chat(request: ChatRequest) -> ChatResponse:  # 接收自然语言问题并返回分析结果。
    result = await service.answer(request.query, request.session_id)  # 调用业务服务生成答案。
    return ChatResponse(**result)  # 将业务结果转换为接口响应模型。


@app.post("/api/files", response_model=UploadResponse)  # 注册通用文档上传接口。
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:  # 接收 PDF、Office、文本和图片文件。
    content = await file.read()  # 读取上传文件内容。
    result = await service.save_upload(file.filename or "unknown", file.content_type or "application/octet-stream", content)  # 保存上传文件。
    return UploadResponse(**result)  # 返回文件接收结果。


@app.post("/api/images/analyze")  # 注册结构图解析接口。
async def analyze_image(file: UploadFile = File(...)) -> dict:  # 接收并解析结构图图片。
    content = await file.read()  # 读取图片内容。
    return await service.analyze_image(file.filename or "unknown", file.content_type or "image/*", content)  # 调用视觉模型解析图片。
