"""本地 SQLite 数据库模块，保存用户、会话和知识文件审核状态。"""  # 说明数据库模块职责。

from __future__ import annotations  # 启用延迟类型注解。

import hashlib  # 用于密码派生和密码校验。
import secrets  # 用于生成随机盐值和会话令牌。
import sqlite3  # 使用 Python 标准库 SQLite 驱动。
from datetime import datetime, timedelta, timezone  # 用于会话过期时间。
from pathlib import Path  # 用于跨平台路径处理。
from typing import Any  # 用于通用字典类型。

from .config import DB_PATH, INITIAL_ADMIN_USERS, INITIAL_USER_PASSWORD  # 导入本地数据库配置。


def now_text() -> str:  # 获取当前 UTC 时间文本。
    return datetime.now(timezone.utc).isoformat()  # 返回带时区的 ISO 时间。


def hash_password(password: str, salt: str | None = None) -> str:  # 对密码进行 PBKDF2 哈希。
    actual_salt = salt or secrets.token_hex(16)  # 没有盐值时生成新的随机盐。
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), actual_salt.encode("utf-8"), 120000)  # 计算密码派生值。
    return f"pbkdf2_sha256$120000${actual_salt}${derived.hex()}"  # 保存算法、迭代次数、盐值和结果。


def verify_password(password: str, encoded: str) -> bool:  # 校验输入密码。
    try:  # 尝试拆分保存的密码结构。
        algorithm, iterations, salt, expected = encoded.split("$", 3)  # 读取哈希参数。
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)).hex()  # 使用相同参数派生输入密码。
        return algorithm == "pbkdf2_sha256" and secrets.compare_digest(derived, expected)  # 使用恒定时间比较结果。
    except (ValueError, TypeError):  # 处理格式异常的密码记录。
        return False  # 异常记录视为校验失败。


class Database:  # 定义 SQLite 数据库访问类。
    """封装用户、会话和文件审核相关的数据库操作。"""  # 说明类职责。

    def __init__(self, path: Path = DB_PATH) -> None:  # 初始化数据库访问对象。
        self.path = path  # 保存数据库文件路径。
        self.path.parent.mkdir(parents=True, exist_ok=True)  # 确保数据库父目录存在。
        self.initialize()  # 创建表并初始化默认账号。

    def connect(self) -> sqlite3.Connection:  # 创建数据库连接。
        connection = sqlite3.connect(self.path)  # 打开 SQLite 文件。
        connection.row_factory = sqlite3.Row  # 让查询结果支持字段名称访问。
        return connection  # 返回数据库连接。

    def initialize(self) -> None:  # 初始化数据库表和默认账号。
        with self.connect() as connection:  # 使用上下文自动提交或回滚。
            connection.executescript("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)); CREATE TABLE IF NOT EXISTS knowledge_files (id TEXT PRIMARY KEY, filename TEXT NOT NULL, stored_path TEXT NOT NULL, content_type TEXT NOT NULL, size INTEGER NOT NULL, uploader_id INTEGER NOT NULL, status TEXT NOT NULL, review_comment TEXT, created_at TEXT NOT NULL, reviewed_at TEXT, ingested_at TEXT, FOREIGN KEY(uploader_id) REFERENCES users(id));""")  # 创建用户、会话和知识文件表。
            for username in INITIAL_ADMIN_USERS:  # 遍历默认管理员账号。
                connection.execute("INSERT OR IGNORE INTO users(username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)", (username, hash_password(INITIAL_USER_PASSWORD), now_text()))  # 初始化管理员账号。

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:  # 验证账号密码。
        with self.connect() as connection:  # 打开数据库连接。
            row = connection.execute("SELECT id, username, password_hash, role, active FROM users WHERE username = ?", (username,)).fetchone()  # 查询用户记录。
        if not row or not row["active"] or not verify_password(password, row["password_hash"]):  # 检查用户状态和密码。
            return None  # 验证失败时不返回用户信息。
        return {"id": row["id"], "username": row["username"], "role": row["role"]}  # 返回最小用户信息。

    def create_session(self, user_id: int) -> str:  # 创建登录会话令牌。
        token = secrets.token_urlsafe(32)  # 生成不可预测的会话令牌。
        expires = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()  # 设置十二小时过期时间。
        with self.connect() as connection:  # 打开数据库连接。
            connection.execute("INSERT INTO sessions(token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires))  # 保存会话令牌。
        return token  # 返回会话令牌。

    def user_from_token(self, token: str) -> dict[str, Any] | None:  # 根据令牌读取用户。
        with self.connect() as connection:  # 打开数据库连接。
            row = connection.execute("SELECT users.id, users.username, users.role, sessions.expires_at FROM sessions JOIN users ON users.id = sessions.user_id WHERE sessions.token = ? AND users.active = 1", (token,)).fetchone()  # 查询有效会话。
        if not row or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):  # 检查会话是否过期。
            return None  # 过期或不存在时返回空。
        return {"id": row["id"], "username": row["username"], "role": row["role"]}  # 返回用户信息。

    def create_file(self, record: dict[str, Any]) -> dict[str, Any]:  # 保存待审核文件记录。
        with self.connect() as connection:  # 打开数据库连接。
            connection.execute("INSERT INTO knowledge_files(id, filename, stored_path, content_type, size, uploader_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)", (record["id"], record["filename"], record["stored_path"], record["content_type"], record["size"], record["uploader_id"], now_text()))  # 写入待审核状态。
        return self.get_file(record["id"])  # 返回完整文件记录。

    def get_file(self, file_id: str) -> dict[str, Any] | None:  # 查询单个文件记录。
        with self.connect() as connection:  # 打开数据库连接。
            row = connection.execute("SELECT knowledge_files.*, users.username AS uploader FROM knowledge_files JOIN users ON users.id = knowledge_files.uploader_id WHERE knowledge_files.id = ?", (file_id,)).fetchone()  # 查询文件和上传者。
        return dict(row) if row else None  # 将行转换为字典。

    def list_files(self, user: dict[str, Any]) -> list[dict[str, Any]]:  # 按角色查询文件记录。
        with self.connect() as connection:  # 打开数据库连接。
            if user["role"] == "admin":  # 判断是否为管理员。
                rows = connection.execute("SELECT knowledge_files.*, users.username AS uploader FROM knowledge_files JOIN users ON users.id = knowledge_files.uploader_id ORDER BY knowledge_files.created_at DESC").fetchall()  # 管理员查看全部文件。
            else:  # 处理普通工程师查询。
                rows = connection.execute("SELECT knowledge_files.*, users.username AS uploader FROM knowledge_files JOIN users ON users.id = knowledge_files.uploader_id WHERE uploader_id = ? ORDER BY knowledge_files.created_at DESC", (user["id"],)).fetchall()  # 工程师只查看自己的文件。
        return [dict(row) for row in rows]  # 返回文件字典列表。

    def review_file(self, file_id: str, status: str, comment: str | None) -> dict[str, Any] | None:  # 更新文件审核状态。
        with self.connect() as connection:  # 打开数据库连接。
            connection.execute("UPDATE knowledge_files SET status = ?, review_comment = ?, reviewed_at = ? WHERE id = ?", (status, comment, now_text(), file_id))  # 保存审核结果。
        return self.get_file(file_id)  # 返回更新后的文件记录。

    def ingest_file(self, file_id: str) -> dict[str, Any] | None:  # 将审核通过的文件标记为已入库。
        with self.connect() as connection:  # 打开数据库连接。
            row = connection.execute("SELECT status FROM knowledge_files WHERE id = ?", (file_id,)).fetchone()  # 查询当前审核状态。
            if not row or row["status"] != "approved":  # 只有审核通过才允许入库。
                return None  # 未通过审核时拒绝入库。
            connection.execute("UPDATE knowledge_files SET status = 'ingested', ingested_at = ? WHERE id = ?", (now_text(), file_id))  # 保存已入库状态。
        return self.get_file(file_id)  # 返回更新后的文件记录。
