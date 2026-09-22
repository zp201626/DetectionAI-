"""面向演示的 fab 数据适配层。

真实部署时只需要替换本文件中的查询函数，将数据接到 MES、EDA、SPC、
设备报警平台或数据湖，Agent 工作流无需改动。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LotRecord:
    lot_id: str
    product: str
    layer: str
    route: str
    process: str
    tool: str
    recipe: str
    start_time: str
    status: str


LOTS = {
    "LOT-240921-A01": LotRecord(
        lot_id="LOT-240921-A01", product="N7 logic", layer="M2", route="R2",
        process="光刻后检测", tool="INS-07", recipe="INS_M2_STD_04",
        start_time="2026-09-21 08:20", status="hold（待判定）",
    ),
    "LOT-240921-B03": LotRecord(
        lot_id="LOT-240921-B03", product="N7 logic", layer="M2", route="R2",
        process="光刻后检测", tool="INS-07", recipe="INS_M2_STD_04",
        start_time="2026-09-21 10:45", status="processing",
    ),
}

DEFECTS = {
    "LOT-240921-A01": {
        "total": 37, "density": 0.82, "baseline_density": 0.31,
        "top_modes": [
            {"mode": "Bridge", "count": 18, "share": "48.6%"},
            {"mode": "Open", "count": 9, "share": "24.3%"},
            {"mode": "Particle", "count": 6, "share": "16.2%"},
        ],
        "spatial_pattern": "wafer edge ring，3–5 点钟方向更集中",
        "severity": "high",
    },
    "LOT-240921-B03": {
        "total": 14, "density": 0.29, "baseline_density": 0.31,
        "top_modes": [
            {"mode": "Particle", "count": 7, "share": "50.0%"},
            {"mode": "Bridge", "count": 4, "share": "28.6%"},
        ],
        "spatial_pattern": "随机分布，无明显 edge ring",
        "severity": "normal",
    },
}

SPC = {
    "INS-07": {
        "metric": "defect density",
        "unit": "defects/cm²",
        "values": [0.28, 0.31, 0.33, 0.36, 0.42, 0.55, 0.82],
        "dates": ["09-15", "09-16", "09-17", "09-18", "09-19", "09-20", "09-21"],
        "ucl": 0.60,
        "lsl": 0.00,
        "trend": "连续 4 点上升，最近 2 点超过 UCL",
    },
    "ETCH-03": {
        "metric": "CD bias",
        "unit": "nm",
        "values": [1.2, 1.0, 1.4, 1.6, 1.8, 2.1, 2.4],
        "dates": ["09-15", "09-16", "09-17", "09-18", "09-19", "09-20", "09-21"],
        "ucl": 2.0,
        "lsl": -2.0,
        "trend": "缓慢正向漂移，最近 2 点超过 UCL",
    },
}

ALARMS = {
    "INS-07": [
        {"time": "2026-09-21 07:52", "code": "ILLUM-231", "level": "warning", "message": "illumination intensity low"},
        {"time": "2026-09-21 08:06", "code": "ALIGN-104", "level": "critical", "message": "alignment mark recognition retry"},
        {"time": "2026-09-21 08:11", "code": "FOCUS-019", "level": "warning", "message": "focus offset near limit"},
    ],
    "ETCH-03": [
        {"time": "2026-09-20 23:18", "code": "RF-088", "level": "warning", "message": "RF match network drift"},
    ],
}

RECIPE_CHANGES = {
    "INS-07": [
        {"time": "2026-09-20 22:40", "recipe": "INS_M2_STD_04", "field": "focus_offset", "before": "-0.02", "after": "+0.05", "operator": "ENG-021"},
    ],
    "ETCH-03": [],
}


class FabDataStore:
    """统一封装 fab 数据查询，便于替换为真实连接器。"""

    def get_lot_context(self, lot_id: str) -> dict[str, Any]:
        record = LOTS.get(lot_id.upper())
        if not record:
            return {"found": False, "lot_id": lot_id, "message": "未找到该 lot 的演示数据"}
        return {"found": True, **record.__dict__}

    def get_defect_summary(self, lot_id: str) -> dict[str, Any]:
        data = DEFECTS.get(lot_id.upper())
        if not data:
            return {"found": False, "lot_id": lot_id, "message": "未找到缺陷汇总"}
        return {"found": True, "lot_id": lot_id.upper(), **data}

    def get_spc_trend(self, tool_id: str) -> dict[str, Any]:
        data = SPC.get(tool_id.upper())
        if not data:
            return {"found": False, "tool_id": tool_id, "message": "未找到 SPC 趋势"}
        return {"found": True, "tool_id": tool_id.upper(), **data}

    def get_alarm_history(self, tool_id: str) -> dict[str, Any]:
        return {"found": True, "tool_id": tool_id.upper(), "alarms": ALARMS.get(tool_id.upper(), [])}

    def get_recipe_changes(self, tool_id: str) -> dict[str, Any]:
        return {"found": True, "tool_id": tool_id.upper(), "changes": RECIPE_CHANGES.get(tool_id.upper(), [])}

    def get_report(self, lot_id: str) -> dict[str, Any]:
        lot = self.get_lot_context(lot_id)
        defects = self.get_defect_summary(lot_id)
        tool_id = lot.get("tool", "") if lot.get("found") else ""
        return {
            "lot": lot,
            "defects": defects,
            "spc": self.get_spc_trend(tool_id) if tool_id else {"found": False},
            "alarms": self.get_alarm_history(tool_id) if tool_id else {"found": False},
            "recipe_changes": self.get_recipe_changes(tool_id) if tool_id else {"found": False},
        }
