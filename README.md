# DetectionAI 助手

这是参考 LangGraph AIOps Agent 改造的晶圆厂 Detection 工程师 AI 助手。当前工程采用 FastAPI 后端和纯 HTML/CSS/JavaScript 前端，FastAPI 同时提供接口和网页，因此运行环境不需要 Node.js 或 npm。

## 工程结构

```text
backend/             FastAPI 接口、网关适配器和业务服务
agent/               Detection 工作流、演示数据和知识检索
backend/static/      HTML、CSS 和 JavaScript 页面
data/knowledge/      本地 SOP、缺陷机理和其他知识文档
```

## 知识库文件放在哪里

当前版本的本地知识库目录是：

```text
C:\Users\Maya\Documents\Codex\DetectionAI助手\AI助手\data\knowledge\
```

也可以用相对于项目根目录的路径表示：

```text
data/knowledge/
```

建议在该目录下按资料类型分文件夹保存：

```text
data/knowledge/
├── historical_cases/       历史缺陷 Case 和异常复盘
├── machine_sop/            机台 SOP、操作规范和排查流程
├── optical_papers/        光学 Paper、膜层结构和缺陷机理
└── other/                  其他规范、临时作业文件和辅助资料
```

当前演示版的关键词检索会扫描 `data/knowledge/` 下的 Markdown 文件。将来接入正式向量库后，PDF、Word、PPT、Excel、TXT、Markdown 和图片应先经过管理员审核，再由入库任务解析并写入向量库；不建议直接把原始生产文件放到 GitHub。

## 如何让回答更准确

DetectionAI 助手不是通过简单“训练几次对话”就会自动变准。准确率主要取决于知识资料、检索质量、图谱关系、模型能力和评测反馈。建议按照以下顺序优化：

### 1. 先提高知识文件质量

- 优先整理已确认结论的历史 Case，而不是只上传聊天记录。
- 每个 Case 保留产品、层别、工艺、机台、缺陷类型、现象、排查过程、根因、措施和最终结论。
- SOP 和 Paper 保留版本号、生效日期、章节标题和页码。
- 扫描 PDF 先做 OCR，确保文本和页码能够被检索。
- 删除重复、过期、互相矛盾或未经确认的文件。
- 文件名统一包含类别、主题和版本，例如 `M2_Bridge_INS07_Case_2026_v1.pdf`。

### 2. 使用标准元数据

每个文件建议附带：

```text
文档类型：历史 Case / 机台 SOP / 光学 Paper / 其他
产品：
层别：
工艺：
机台：
缺陷类型：
版本：
生效日期：
审核人：
```

这些字段可以帮助系统过滤无关文档，避免把不同产品、层别和机台的经验混在一起。

### 3. 建立问题评测集

建议由 Detection 工程师整理 30～100 个真实问题，每个问题记录：

- 标准答案
- 必须引用的 Case、SOP 或 Paper
- 不允许出现的结论
- 关键判断依据
- 是否需要图片解析

以后每次更换模型、Prompt、Embedding 模型或检索参数，都用这组问题回归测试。不要只凭“看起来回答不错”判断效果。

### 4. 分开事实、推测和建议

系统回答应固定区分：

```text
已确认事实
基于资料的推测
建议验证动作
当前无法确认的信息
```

这样可以降低模型把推测说成确定结论的风险。

### 5. 优化检索和向量库

正式版需要使用 Embedding 模型把文档和问题转换为向量，再由向量库检索相关片段。提升准确率时重点检查：

- 文档切分长度是否合适。
- 是否保留章节、页码和文件版本元数据。
- 是否同时使用关键词检索和向量检索。
- 是否对产品、层别、机台和缺陷类型做过滤。
- Top-K 是否太少或太多。
- 检索结果是否包含互相冲突的旧版本。

### 6. 用 GraphRAG 连接专业关系

向量检索擅长找相似文字，GraphRAG 更适合表达：

```text
缺陷类型 → 光学机理 → 膜层结构 → 检测机台 → 相似 Case → SOP
```

图谱关系必须经过工程师审核，不能完全依赖模型自动生成，否则错误关系会被重复传播。

### 7. 选择合适模型

- 复杂理论解释和多来源综合：使用能力更强的主模型。
- 简单分类、意图识别和摘要：使用低延迟模型。
- 长 Paper、长 SOP 和多 Case 合并：使用长上下文模型。
- 结构图和缺陷图片：使用视觉模型。
- 文档入库和问题检索：使用 Embedding 模型。

模型名称不是准确率的唯一决定因素。真实 Detection 评测集和知识库质量通常比盲目更换模型更重要。

### 8. 建立人工反馈闭环

每次回答允许工程师标记：

- 有帮助
- 部分正确
- 引用错误
- 结论错误
- 缺少关键资料

管理员每周汇总错误回答，判断问题属于知识缺失、检索错误、图谱错误、Prompt 问题还是模型问题，再针对性修复。

## 当前版本的准确率边界

当前仓库中的 `data/knowledge/` 只有演示文档，`agent/knowledge.py` 还是轻量关键词检索，不能代表生产级 RAG 或 GraphRAG 的最终准确率。正式部署前需要完成文档解析、Embedding 入库、向量检索、图谱构建、引用定位和评测集回归测试。

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
