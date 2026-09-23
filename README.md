# DetectionAI 助手

这是参考 LangGraph AIOps Agent 改造的晶圆厂 Detection 工程师 AI 助手。当前工程采用 FastAPI 后端和纯 HTML/CSS/JavaScript 前端，FastAPI 同时提供接口和网页，因此运行环境不需要 Node.js 或 npm。

## 工程结构

```text
backend/             FastAPI 接口、网关适配器和业务服务
agent/               Detection 工作流、演示数据和知识检索
backend/static/      HTML、CSS 和 JavaScript 页面
data/knowledge/      本地 SOP、缺陷机理和其他知识文档
```

## 启动后端

```powershell
cd "C:\Users\Maya\Documents\Codex\DetectionAI助手\AI助手"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

浏览器访问 `http://127.0.0.1:8000`，后端健康检查地址为 `http://127.0.0.1:8000/api/health`。不再需要启动第二个前端窗口。

## 公司网关配置

公司环境接入时，先复制 `backend/.env.example` 为项目根目录的 `.env`，再在 VS Code 中填写公司网关地址、API Key 和模型名称。公司网关适配集中在 `backend/gateway.py`，业务调用集中在 `backend/service.py`。API Key 只能放在本地 `.env`，不可提交到 GitHub。网关协议当前按 OpenAI 兼容的 `/chat/completions` 和 `/embeddings` 设计；如果公司网关路径或鉴权字段不同，只需要修改适配器。

不配置网关时，系统仍可以用本地 Detection 工作流和本地知识库运行演示。示例编号：`LOT-240921-A01`、`LOT-240921-B03`、`INS-07`、`ETCH-03`。

## 本期范围

已预留全文 RAG、GraphRAG、图片解析和来源溯源接口；本期不实现机台参数自动推荐，也不自动对接 MN 系统或下发机台控制指令。
