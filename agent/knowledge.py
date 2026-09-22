"""轻量级本地知识检索。

先用标准库实现，避免首次运行必须下载 embedding 模型；后续可按参考项目
替换为 Chroma + DashScope Embeddings，接口保持不变。
"""

from __future__ import annotations

import re
from pathlib import Path


class KnowledgeBase:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def search(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        terms = {x.lower() for x in re.findall(r"[\w-]+|[\u4e00-\u9fff]", query) if len(x) > 1}
        results: list[tuple[int, dict[str, str]]] = []
        for path in sorted(self.root.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            score = sum(text.lower().count(term) for term in terms)
            if score:
                results.append((score, {"title": path.stem, "content": text[:1800], "source": path.name}))
        results.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in results[:limit]]
