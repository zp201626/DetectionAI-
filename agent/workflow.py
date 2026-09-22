"""基于 LangGraph 的 Detection 工程师分析工作流。"""

from __future__ import annotations

import re
from typing import Any, TypedDict

from .data import FabDataStore
from .tools import search_knowledge

try:
    from langgraph.graph import END, START, StateGraph
except Exception:  # pragma: no cover
    StateGraph = None
    START = END = None


class DetectionState(TypedDict, total=False):
    query: str
    intent: str
    lot_id: str
    tool_id: str
    evidence: dict[str, Any]
    answer: str


class DetectionAssistant:
    def __init__(self, knowledge_root: str):
        self.store = FabDataStore()
        self.knowledge_root = knowledge_root
        self.graph = self._build_graph() if StateGraph else None

    def _build_graph(self):
        graph = StateGraph(DetectionState)
        graph.add_node("route", self._route)
        graph.add_node("collect", self._collect)
        graph.add_node("respond", self._respond)
        graph.add_edge(START, "route")
        graph.add_edge("route", "collect")
        graph.add_edge("collect", "respond")
        graph.add_edge("respond", END)
        return graph.compile()

    @staticmethod
    def _extract(query: str) -> tuple[str, str]:
        lot = re.search(r"\bLOT[-_][A-Z0-9-]+", query.upper())
        tool = re.search(r"\b(?:INS|ETCH|CVD|CMP|LITHO)[-_][A-Z0-9-]+", query.upper())
        return (lot.group(0).replace("_", "-") if lot else "", tool.group(0).replace("_", "-") if tool else "")

    def _route(self, state: DetectionState) -> DetectionState:
        q = state["query"].lower()
        lot_id, tool_id = self._extract(state["query"])
        if any(k in q for k in ("报告", "report", "总结", "日报", "周报")):
            intent = "report"
        elif any(k in q for k in ("spc", "趋势", "漂移", "control chart", "控制图")):
            intent = "spc"
        elif any(k in q for k in ("报警", "alarm", "宕机")):
            intent = "alarm"
        elif any(k in q for k in ("recipe", "配方", "参数变更")):
            intent = "recipe"
        elif any(k in q for k in ("sop", "规范", "怎么排查", "知识", "标准")):
            intent = "knowledge"
        else:
            intent = "defect"
        return {"intent": intent, "lot_id": lot_id, "tool_id": tool_id}

    def _collect(self, state: DetectionState) -> DetectionState:
        intent, lot_id, tool_id = state["intent"], state.get("lot_id", ""), state.get("tool_id", "")
        evidence: dict[str, Any] = {}
        if intent in {"defect", "report"} and lot_id:
            lot = self.store.get_lot_context(lot_id)
            evidence["lot"] = lot
            evidence["defects"] = self.store.get_defect_summary(lot_id)
            tool_id = tool_id or lot.get("tool", "")
        if intent in {"spc", "report"} and tool_id:
            evidence["spc"] = self.store.get_spc_trend(tool_id)
        if intent in {"alarm", "report"} and tool_id:
            evidence["alarms"] = self.store.get_alarm_history(tool_id)
        if intent in {"recipe", "report"} and tool_id:
            evidence["recipe_changes"] = self.store.get_recipe_changes(tool_id)
        if intent == "knowledge":
            evidence["knowledge"] = search_knowledge(state["query"], self.knowledge_root)
        # 对缺少 lot/tool 的问题，仍然检索知识并明确数据不足，而不是编造结果。
        if not evidence and intent != "knowledge":
            evidence["knowledge"] = search_knowledge(state["query"], self.knowledge_root)
        return {"evidence": evidence, "tool_id": tool_id}

    @staticmethod
    def _fmt_list(items: list[dict[str, Any]]) -> str:
        return "、".join(f"{x.get('mode')} {x.get('count')}件（{x.get('share')}）" for x in items)

    def _respond(self, state: DetectionState) -> DetectionState:
        intent, q, ev = state["intent"], state["query"], state.get("evidence", {})
        if intent == "knowledge":
            docs = ev.get("knowledge", [])
            if not docs:
                return {"answer": "当前本地知识库没有匹配内容。请提供 SOP、设备手册或排障案例后再检索。"}
            body = "\n\n".join(f"**{d['title']}**\n{d['content']}\n> 来源：{d['source']}" for d in docs)
            return {"answer": f"根据本地知识库检索结果：\n\n{body}"}

        if intent == "defect":
            lot, defects = ev.get("lot", {}), ev.get("defects", {})
            if not lot.get("found") or not defects.get("found"):
                return {"answer": "缺少有效 LOT_ID。请提供例如 `LOT-240921-A01`，我才能查询缺陷分布和 lot 上下文。"}
            answer = (
                f"## 缺陷分析：{lot['lot_id']}\n\n"
                f"- 产品/层别：{lot['product']} / {lot['layer']}\n"
                f"- 工艺与设备：{lot['process']} / `{lot['tool']}`\n"
                f"- 缺陷数/密度：**{defects['total']} 件 / {defects['density']} defects/cm²**（基线 {defects['baseline_density']}）\n"
                f"- Top 缺陷：{self._fmt_list(defects['top_modes'])}\n"
                f"- 空间特征：{defects['spatial_pattern']}\n\n"
                "### 初步判断\n"
                "缺陷密度较基线明显升高，且呈现非随机空间聚集；优先排查检测机光学/对焦/对准状态，并与相邻 lot 及同机台历史趋势交叉确认。\n\n"
                "### 建议动作\n"
                "1. 对该 lot 执行 hold，复核 defect map 与复测结果。\n"
                "2. 检查检测机最近报警、focus/illumination 及 recipe 变更。\n"
                "3. 与同层别最近 3 个 lot 做 defect mode 和 edge ring 对比。"
            )
            return {"answer": answer}

        if intent == "spc":
            spc = ev.get("spc", {})
            if not spc.get("found"):
                return {"answer": "请提供有效设备编号，例如 `INS-07` 或 `ETCH-03`。"}
            return {"answer": (
                f"## SPC 趋势：{spc['tool_id']}\n\n"
                f"- 指标：{spc['metric']}（{spc['unit']}）\n"
                f"- 最近值：{spc['values'][-1]}，UCL={spc['ucl']}，LSL={spc['lsl']}\n"
                f"- 趋势：**{spc['trend']}**\n\n"
                "### 判定\n当前更符合持续漂移/特殊原因信号，不建议只用扩大控制界限来处理。建议先锁定设备、recipe 与腔体状态，再做分层验证。"
            )}

        if intent in {"alarm", "recipe"}:
            key = "alarms" if intent == "alarm" else "recipe_changes"
            rows = ev.get(key, {})
            items = rows.get(key, []) if rows else []
            if not items:
                return {"answer": f"没有找到 `{state.get('tool_id', '')}` 的相关记录，或当前问题缺少设备编号。"}
            lines = [f"- {x}" for x in items]
            return {"answer": f"## {'报警历史' if intent == 'alarm' else 'Recipe 变更'}：{state.get('tool_id', '')}\n\n" + "\n".join(lines)}

        # report
        lot, defects, spc = ev.get("lot", {}), ev.get("defects", {}), ev.get("spc", {})
        if not lot.get("found"):
            return {"answer": "生成 fab 分析报告需要 LOT_ID，例如 `LOT-240921-A01`。"}
        return {"answer": (
            f"# Detection 分析报告：{lot['lot_id']}\n\n"
            f"## 1. 报告概览\n- 产品/层别：{lot['product']} / {lot['layer']}\n- 工艺：{lot['process']}\n- 设备：{lot['tool']}\n- 状态：{lot['status']}\n\n"
            f"## 2. 缺陷表现\n- 缺陷总数：{defects.get('total', 'N/A')}\n- 缺陷密度：{defects.get('density', 'N/A')}（基线 {defects.get('baseline_density', 'N/A')}）\n- 空间分布：{defects.get('spatial_pattern', 'N/A')}\n\n"
            f"## 3. 设备与 SPC\n- {spc.get('trend', '未获取到设备 SPC 数据')}\n"
            "\n## 4. 综合判断\n当前需要优先排除检测设备光学/对焦/对准相关特殊原因，同时确认该缺陷是否在真实工艺层面复现。\n\n"
            "## 5. 建议\n1. 保持 lot hold 并完成复测。\n2. 核对设备报警与 recipe 变更时间线。\n3. 通过 golden wafer 或 monitor wafer 做设备健康确认。"
        )}

    def ask(self, query: str) -> dict[str, Any]:
        initial: DetectionState = {"query": query}
        if self.graph:
            result = self.graph.invoke(initial)
        else:
            result = initial
            for node in (self._route, self._collect, self._respond):
                result.update(node(result))
        return result
