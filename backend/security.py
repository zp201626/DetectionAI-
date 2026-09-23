"""FastAPI 登录和角色权限依赖。"""  # 说明权限模块职责。

from __future__ import annotations  # 启用延迟类型注解。

from fastapi import Depends, HTTPException, status  # 引入 FastAPI 依赖和异常。
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # 引入 Bearer Token 读取器。

from .database import Database  # 导入数据库访问类。


bearer_scheme = HTTPBearer(auto_error=False)  # 创建可返回自定义错误的 Bearer 读取器。


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:  # 读取当前登录用户。
    if not credentials:  # 判断请求是否携带令牌。
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")  # 返回未登录错误。
    user = Database().user_from_token(credentials.credentials)  # 根据令牌查询用户。
    if not user:  # 判断令牌是否有效。
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")  # 返回无效令牌错误。
    return user  # 返回当前用户信息。


def admin_user(user: dict = Depends(current_user)) -> dict:  # 校验当前用户是否为管理员。
    if user["role"] != "admin":  # 判断用户角色。
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以执行此操作")  # 拒绝普通工程师访问管理功能。
    return user  # 返回管理员信息。
