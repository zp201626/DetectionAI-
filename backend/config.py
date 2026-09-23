"""后端配置模块，集中管理公司 AI 网关和本地数据路径。"""  # 说明配置模块用途。

from __future__ import annotations  # 启用延迟类型注解，方便兼容不同 Python 版本。

import os  # 读取环境变量和系统路径配置。
from pathlib import Path  # 使用跨平台路径对象。

from dotenv import load_dotenv  # 读取本地 .env 文件中的敏感配置。


BASE_DIR = Path(__file__).resolve().parent.parent  # 计算项目根目录。
load_dotenv(BASE_DIR / ".env")  # 从项目根目录加载本地网关配置，且不会提交到 Git。
DATA_DIR = BASE_DIR / "data"  # 指定本地数据目录。
KNOWLEDGE_DIR = DATA_DIR / "knowledge"  # 指定知识库文件目录。
UPLOAD_DIR = DATA_DIR / "uploads"  # 指定用户上传文件目录。

GATEWAY_BASE_URL = os.getenv("DETECTION_GATEWAY_BASE_URL", "http://agi-gateway.cxmt.com/token/v1").strip()  # 公司 AI 网关地址，默认使用已提供的公司开发网关。
GATEWAY_API_KEY = os.getenv("DETECTION_GATEWAY_API_KEY", "").strip()  # 公司 AI 网关密钥，部署时填写。
CHAT_MODEL_NAME = os.getenv("DETECTION_CHAT_MODEL", "glm-5.2")  # 默认使用主推理文本模型。
FAST_MODEL_NAME = os.getenv("DETECTION_FAST_MODEL", "glm-5.3-flash")  # 配置低延迟文本模型供简单问答使用。
LONG_CONTEXT_MODEL_NAME = os.getenv("DETECTION_LONG_CONTEXT_MODEL", "kimi-k2.6-cloud")  # 配置长上下文模型供大文档和长 Case 使用。
VISION_MODEL_NAME = os.getenv("DETECTION_VISION_MODEL", "doubao-seed-2.0-pro-cloud")  # 配置视觉模型供结构图解析使用。
EMBEDDING_MODEL_NAME = os.getenv("DETECTION_EMBEDDING_MODEL", "qwen3-Embedding")  # 配置向量模型供知识库搭建和检索使用。
CHAT_COMPLETIONS_PATH = os.getenv("DETECTION_CHAT_COMPLETIONS_PATH", "/chat/completions").strip()  # 配置文本和视觉接口相对路径。
EMBEDDINGS_PATH = os.getenv("DETECTION_EMBEDDINGS_PATH", "/embeddings").strip()  # 配置向量接口相对路径。
GATEWAY_TIMEOUT_SECONDS = float(os.getenv("DETECTION_GATEWAY_TIMEOUT", "60"))  # 设置网关请求超时时间。


def ensure_runtime_directories() -> None:  # 创建运行时所需目录。
    """确保上传目录和知识库目录存在。"""  # 说明函数用途。
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)  # 创建知识库目录。
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # 创建上传目录。
