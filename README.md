# DetectionAI 助手

这是参考 LangGraph AIOps Agent 改造的晶圆厂 Detection 工程师 AI 助手。当前工程采用 FastAPI 后端和 React + Vite 独立前端，支持本地规则工作流、知识检索、来源引用、文件上传接口和结构图视觉模型网关接口。

## 工程结构

```text
backend/             FastAPI 接口、网关适配器和业务服务
agent/               Detection 工作流、演示数据和知识检索
frontend/            React + Vite 独立前端
data/knowledge/      本地 SOP、缺陷机理和其他知识文档
```

## 启动后端

```powershell
cd "C:\Users\Maya\Documents\Codex\DetectionAI助手\AI助手"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.main:app --reload --port 8000
```

## 启动前端

```powershell
cd "C:\Users\Maya\Documents\Codex\DetectionAI助手\AI助手\frontend"
npm install
npm run dev
```

浏览器访问 `http://localhost:5173`，后端健康检查地址为 `http://127.0.0.1:8000/api/health`。

## 公司网关配置

复制 `backend/.env.example` 中的变量到部署环境。公司网关适配集中在 `backend/gateway.py`，业务调用集中在 `backend/service.py`。当前默认网关地址为 `http://agi-gateway.cxmt.com/token/v1`，主模型为 `glm-5.2`，视觉模型为 `doubao-seed-2.0-pro-cloud`，Embedding 模型为 `qwen3-Embedding`。API Key 只能放在本地 `.env`，不可提交到 GitHub。网关协议当前按 OpenAI 兼容的 `/chat/completions` 和 `/embeddings` 设计；如果公司网关路径或鉴权字段不同，只需要修改适配器。

不配置网关时，系统仍可以用本地 Detection 工作流和本地知识库运行演示。示例编号：`LOT-240921-A01`、`LOT-240921-B03`、`INS-07`、`ETCH-03`。

## 本期范围

已预留全文 RAG、GraphRAG、图片解析和来源溯源接口；本期不实现机台参数自动推荐，也不自动对接 MN 系统或下发机台控制指令。
