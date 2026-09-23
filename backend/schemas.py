"""FastAPI 请求和响应数据模型。"""  # 说明数据模型模块职责。

from __future__ import annotations  # 启用延迟类型注解。

from typing import Any  # 引入通用 JSON 数据类型。

from pydantic import BaseModel, Field  # 引入接口参数校验模型。


class ChatRequest(BaseModel):  # 定义聊天请求模型。
    query: str = Field(min_length=1, max_length=10000, description="工程师问题")  # 保存用户问题。
    session_id: str | None = Field(default=None, description="可选会话编号")  # 保存会话编号。


class Citation(BaseModel):  # 定义来源引用模型。
    source_type: str  # 保存来源类型，例如 knowledge、lot 或 tool。
    title: str  # 保存来源标题。
    location: str | None = None  # 保存页码、章节或记录位置。
    excerpt: str | None = None  # 保存可展示的原文摘要。


class ChatResponse(BaseModel):  # 定义聊天响应模型。
    answer: str  # 保存助手最终回答。
    session_id: str  # 保存本次会话编号。
    intent: str  # 保存识别出的业务意图。
    citations: list[Citation] = Field(default_factory=list)  # 保存可追溯来源列表。
    evidence: dict[str, Any] = Field(default_factory=dict)  # 保存供前端调试或展示的证据摘要。


class UploadResponse(BaseModel):  # 定义文件上传响应模型。
    file_id: str  # 保存文件唯一编号。
    filename: str  # 保存原始文件名。
    content_type: str  # 保存文件类型。
    size: int  # 保存文件大小。
    message: str  # 保存处理状态说明。
    status: str = "pending"  # 保存审核状态，默认进入待审核队列。


class HealthResponse(BaseModel):  # 定义健康检查响应模型。
    status: str  # 保存服务状态。
    gateway_configured: bool  # 标记公司网关是否已经配置。
    local_fallback_enabled: bool  # 标记本地离线兜底是否可用。


class LoginRequest(BaseModel):  # 定义登录请求模型。
    username: str = Field(min_length=1, max_length=100)  # 保存登录用户名。
    password: str = Field(min_length=1, max_length=200)  # 保存登录密码。


class LoginResponse(BaseModel):  # 定义登录响应模型。
    token: str  # 返回会话令牌。
    user: dict[str, Any]  # 返回登录用户信息。


class KnowledgeFileResponse(BaseModel):  # 定义知识文件审核响应模型。
    id: str  # 保存文件编号。
    filename: str  # 保存原始文件名。
    content_type: str  # 保存文件类型。
    size: int  # 保存文件大小。
    uploader: str  # 保存上传者账号。
    status: str  # 保存 pending、approved、rejected 或 ingested 状态。
    review_comment: str | None = None  # 保存管理员审核意见。
    created_at: str  # 保存上传时间。
    reviewed_at: str | None = None  # 保存审核时间。
    ingested_at: str | None = None  # 保存入库时间。


class ReviewRequest(BaseModel):  # 定义文件审核请求模型。
    status: str = Field(pattern="^(approved|rejected)$")  # 限制审核状态只能通过或驳回。
    comment: str | None = Field(default=None, max_length=2000)  # 保存审核意见。
