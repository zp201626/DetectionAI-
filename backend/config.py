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
DB_PATH = DATA_DIR / "detection_assistant.db"  # 指定本地 SQLite 数据库文件。
INITIAL_ADMIN_USERS = [item.strip() for item in os.getenv("DETECTION_ADMIN_USERS", "admin1,admin2").split(",") if item.strip()]  # 配置默认管理员账号名称。
INITIAL_USER_PASSWORD = os.getenv("DETECTION_INITIAL_PASSWORD", "change-me-before-team-use")  # 配置首次初始化账号密码，团队使用前必须修改。

GATEWAY_BASE_URL = os.getenv("DETECTION_GATEWAY_BASE_URL", "").strip()  # 公司 AI 网关地址，部署到公司环境时在本地 .env 中填写。
GATEWAY_API_KEY = os.getenv("DETECTION_GATEWAY_API_KEY", "").strip()  # 公司 AI 网关密钥，部署时填写。
CHAT_MODEL_NAME = os.getenv("DETECTION_CHAT_MODEL", "detection-chat")  # 默认文本模型名称，未配置网关时不会实际调用。
FAST_MODEL_NAME = os.getenv("DETECTION_FAST_MODEL", "detection-fast")  # 默认快速文本模型名称，接入网关时可替换。
LONG_CONTEXT_MODEL_NAME = os.getenv("DETECTION_LONG_CONTEXT_MODEL", "detection-long-context")  # 默认长上下文模型名称，接入网关时可替换。
VISION_MODEL_NAME = os.getenv("DETECTION_VISION_MODEL", "detection-vision")  # 默认视觉模型名称，接入网关时可替换。
EMBEDDING_MODEL_NAME = os.getenv("DETECTION_EMBEDDING_MODEL", "detection-embedding")  # 默认向量模型名称，接入网关时可替换。
CHAT_COMPLETIONS_PATH = os.getenv("DETECTION_CHAT_COMPLETIONS_PATH", "/chat/completions").strip()  # 配置文本和视觉接口相对路径。
EMBEDDINGS_PATH = os.getenv("DETECTION_EMBEDDINGS_PATH", "/embeddings").strip()  # 配置向量接口相对路径。
GATEWAY_TIMEOUT_SECONDS = float(os.getenv("DETECTION_GATEWAY_TIMEOUT", "60"))  # 设置网关请求超时时间。


def ensure_runtime_directories() -> None:  # 创建运行时所需目录。
    """确保上传目录和知识库目录存在。"""  # 说明函数用途。
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)  # 创建知识库目录。
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # 创建上传目录。
