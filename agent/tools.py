"""Detection Agent 的工具层。"""

from __future__ import annotations

from .data import FabDataStore
from .knowledge import KnowledgeBase

try:
    from langchain_core.tools import tool as langchain_tool
except Exception:  # pragma: no cover - 允许离线轻量运行
    langchain_tool = None


store = FabDataStore()


def _decorate(fn):
    return langchain_tool(fn) if langchain_tool else fn


@_decorate
def get_lot_context(lot_id: str) -> dict:
    """获取 lot 的产品、层别、工艺、检测机台、recipe 和状态。"""
    return store.get_lot_context(lot_id)


@_decorate
def get_defect_summary(lot_id: str) -> dict:
    """获取 lot 缺陷总数、缺陷类型占比、空间分布和严重度。"""
    return store.get_defect_summary(lot_id)


@_decorate
def get_spc_trend(tool_id: str) -> dict:
    """获取检测机台最近 SPC 指标、控制界限和趋势判断。"""
    return store.get_spc_trend(tool_id)


@_decorate
def get_alarm_history(tool_id: str) -> dict:
    """获取设备最近报警历史。"""
    return store.get_alarm_history(tool_id)


@_decorate
def get_recipe_changes(tool_id: str) -> dict:
    """获取设备最近 recipe 参数变更记录。"""
    return store.get_recipe_changes(tool_id)


def search_knowledge(query: str, root: str) -> list[dict[str, str]]:
    """检索本地 SOP、排障手册和工艺知识。"""
    return KnowledgeBase(root).search(query)
