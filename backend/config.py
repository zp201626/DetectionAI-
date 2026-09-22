"""后端配置模块，集中管理公司 AI 网关和本地数据路径。"""  # 说明配置模块用途。

from __future__ import annotations  # 启用延迟类型注解，方便兼容不同 Python 版本。

import os  # 读取环境变量和系统路径配置。
from pathlib import Path  # 使用跨平台路径对象。


BASE_DIR = Path(__file__).resolve().parent.parent  # 计算项目根目录。
DATA_DIR = BASE_DIR / "data"  # 指定本地数据目录。
KNOWLEDGE_DIR = DATA_DIR / "knowledge"  # 指定知识库文件目录。
UPLOAD_DIR = DATA_DIR / "uploads"  # 指定用户上传文件目录。

GATEWAY_BASE_URL = os.getenv("DETECTION_GATEWAY_BASE_URL", "").strip()  # 公司 AI 网关地址，部署时填写。
GATEWAY_API_KEY = os.getenv("DETECTION_GATEWAY_API_KEY", "").strip()  # 公司 AI 网关密钥，部署时填写。
CHAT_MODEL_NAME = os.getenv("DETECTION_CHAT_MODEL", "detection-chat")  # 公司网关中的文本模型名称。
VISION_MODEL_NAME = os.getenv("DETECTION_VISION_MODEL", "detection-vision")  # 公司网关中的视觉模型名称。
EMBEDDING_MODEL_NAME = os.getenv("DETECTION_EMBEDDING_MODEL", "detection-embedding")  # 公司网关中的向量模型名称。
GATEWAY_TIMEOUT_SECONDS = float(os.getenv("DETECTION_GATEWAY_TIMEOUT", "60"))  # 设置网关请求超时时间。


def ensure_runtime_directories() -> None:  # 创建运行时所需目录。
    """确保上传目录和知识库目录存在。"""  # 说明函数用途。
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)  # 创建知识库目录。
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # 创建上传目录。
