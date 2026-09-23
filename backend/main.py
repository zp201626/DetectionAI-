"""FastAPI 应用入口。"""  # 说明 API 入口文件职责。

from __future__ import annotations  # 启用延迟类型注解。

from pathlib import Path  # 引入跨平台路径对象。

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile  # 引入 FastAPI 应用、依赖、异常和文件上传类型。
from fastapi.middleware.cors import CORSMiddleware  # 引入跨域中间件。
from fastapi.staticfiles import StaticFiles  # 引入 FastAPI 静态文件托管能力。

from .database import Database  # 导入本地数据库访问类。
from .schemas import ChatRequest, ChatResponse, HealthResponse, KnowledgeFileResponse, LoginRequest, LoginResponse, ReviewRequest, UploadResponse  # 导入接口模型。
from .security import admin_user, current_user  # 导入登录和管理员权限依赖。
from .service import DetectionService  # 导入 Detection 业务服务。


app = FastAPI(title="DetectionAI Assistant API", version="0.1.0")  # 创建 FastAPI 应用实例。
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])  # 允许本地前端访问后端接口。
service = DetectionService()  # 创建全局业务服务实例。
database = Database()  # 创建全局数据库访问实例。
STATIC_DIR = Path(__file__).resolve().parent / "static"  # 定位纯 Python 前端静态文件目录。


@app.get("/api/health", response_model=HealthResponse)  # 注册健康检查接口。
async def health() -> HealthResponse:  # 返回后端运行状态。
    return HealthResponse(status="ok", gateway_configured=service.gateway.configured, local_fallback_enabled=True)  # 返回服务和网关状态。


@app.post("/api/chat", response_model=ChatResponse)  # 注册 Detection 对话接口。
async def chat(request: ChatRequest, user: dict = Depends(current_user)) -> ChatResponse:  # 接收登录工程师的问题并返回分析结果。
    result = await service.answer(request.query, request.session_id)  # 调用业务服务生成答案。
    return ChatResponse(**result)  # 将业务结果转换为接口响应模型。


@app.post("/api/files", response_model=UploadResponse)  # 注册通用文档上传接口。
async def upload_file(file: UploadFile = File(...), user: dict = Depends(current_user)) -> UploadResponse:  # 接收登录工程师上传的 PDF、Office、文本和图片文件。
    content = await file.read()  # 读取上传文件内容。
    try:  # 捕获文件格式和大小校验异常。
        result = await service.save_upload(file.filename or "unknown", file.content_type or "application/octet-stream", content, user["id"])  # 保存上传文件并进入待审核状态。
    except ValueError as error:  # 处理不合规文件。
        raise HTTPException(status_code=400, detail=str(error)) from error  # 返回文件校验错误。
    return UploadResponse(**result)  # 返回文件接收结果。


@app.post("/api/images/analyze")  # 注册结构图解析接口。
async def analyze_image(file: UploadFile = File(...), user: dict = Depends(current_user)) -> dict:  # 接收登录工程师上传并解析结构图图片。
    content = await file.read()  # 读取图片内容。
    return await service.analyze_image(file.filename or "unknown", file.content_type or "image/*", content)  # 调用视觉模型解析图片。


@app.post("/api/auth/login", response_model=LoginResponse)  # 注册账号密码登录接口。
async def login(request: LoginRequest) -> LoginResponse:  # 校验账号密码并创建会话。
    user = database.authenticate(request.username, request.password)  # 查询并验证用户。
    if not user:  # 判断账号密码是否正确。
        from fastapi import HTTPException  # 延迟导入 HTTP 异常类型。
        raise HTTPException(status_code=401, detail="用户名或密码错误")  # 返回登录失败信息。
    return LoginResponse(token=database.create_session(user["id"]), user=user)  # 返回会话令牌和用户角色。


@app.get("/api/auth/me")  # 注册当前用户信息接口。
async def me(user: dict = Depends(current_user)) -> dict:  # 返回当前登录用户。
    return user  # 返回用户信息。


@app.get("/api/knowledge/files", response_model=list[KnowledgeFileResponse])  # 注册知识文件列表接口。
async def list_knowledge_files(user: dict = Depends(current_user)) -> list[dict]:  # 按角色返回知识文件。
    return database.list_files(user)  # 返回工程师自己的文件或管理员的全部文件。


@app.post("/api/knowledge/files/{file_id}/review", response_model=KnowledgeFileResponse)  # 注册管理员审核接口。
async def review_knowledge_file(file_id: str, request: ReviewRequest, user: dict = Depends(admin_user)) -> dict:  # 审核文件并记录意见。
    record = database.review_file(file_id, request.status, request.comment)  # 更新文件审核状态。
    if not record:  # 判断文件是否存在。
        from fastapi import HTTPException  # 延迟导入 HTTP 异常类型。
        raise HTTPException(status_code=404, detail="文件不存在")  # 返回文件不存在错误。
    return record  # 返回审核后的文件记录。


@app.post("/api/knowledge/files/{file_id}/ingest", response_model=KnowledgeFileResponse)  # 注册管理员入库接口。
async def ingest_knowledge_file(file_id: str, user: dict = Depends(admin_user)) -> dict:  # 将已通过审核的文件标记为入库。
    record = database.ingest_file(file_id)  # 执行审核通过后的入库操作。
    if not record:  # 判断文件是否审核通过或存在。
        from fastapi import HTTPException  # 延迟导入 HTTP 异常类型。
        raise HTTPException(status_code=400, detail="文件不存在或尚未审核通过")  # 返回入库条件不满足错误。
    return record  # 返回入库后的文件记录。


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")  # 让 FastAPI 在同一端口提供 HTML、CSS 和 JavaScript 页面。
