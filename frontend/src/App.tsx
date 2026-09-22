import { FormEvent, useState } from "react"; // 导入表单事件类型和 React 状态钩子。

type Citation = { // 定义来源引用类型。
  source_type: string; // 保存来源类型。
  title: string; // 保存来源标题。
  location?: string; // 保存来源位置。
  excerpt?: string; // 保存来源摘要。
}; // 结束来源类型定义。

type Message = { // 定义聊天消息类型。
  role: "user" | "assistant"; // 标记消息角色。
  content: string; // 保存消息正文。
  citations?: Citation[]; // 保存助手消息引用。
}; // 结束聊天消息类型定义。

const quickPrompts = [ // 定义页面快捷问题。
  "分析 LOT-240921-A01 的缺陷情况", // 添加缺陷分析示例。
  "查看 INS-07 的 SPC 趋势", // 添加 SPC 趋势示例。
  "查询 INS-07 最近报警", // 添加报警查询示例。
  "Bridge 和 edge ring 应该怎么排查？", // 添加知识库检索示例。
]; // 结束快捷问题列表。

function App() { // 定义前端应用组件。
  const [messages, setMessages] = useState<Message[]>([]); // 保存当前会话消息。
  const [query, setQuery] = useState(""); // 保存输入框内容。
  const [loading, setLoading] = useState(false); // 保存请求加载状态。
  const [error, setError] = useState(""); // 保存前端错误信息。

  async function sendMessage(event?: FormEvent) { // 定义发送聊天消息函数。
    event?.preventDefault(); // 阻止浏览器默认提交行为。
    const text = query.trim(); // 清理用户输入两端空白。
    if (!text || loading) return; // 输入为空或请求中时不重复发送。
    setMessages((current) => [...current, { role: "user", content: text }]); // 将用户问题追加到页面。
    setQuery(""); // 清空输入框。
    setLoading(true); // 开启加载状态。
    setError(""); // 清空上一次错误。
    try { // 开始调用后端接口。
      const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: text }) }); // 请求 FastAPI 聊天接口。
      if (!response.ok) throw new Error(`后端请求失败：${response.status}`); // 检查 HTTP 状态码。
      const data = await response.json(); // 解析后端 JSON 响应。
      setMessages((current) => [...current, { role: "assistant", content: data.answer, citations: data.citations }]); // 将助手回答和来源追加到页面。
    } catch (requestError) { // 捕获接口调用异常。
      setError(requestError instanceof Error ? requestError.message : "请求失败，请检查后端服务"); // 显示可理解的错误提示。
    } finally { // 无论请求成功与否都执行收尾逻辑。
      setLoading(false); // 关闭加载状态。
    } // 结束请求处理。
  } // 结束发送消息函数。

  function useQuickPrompt(prompt: string) { // 定义快捷问题填充函数。
    setQuery(prompt); // 将快捷问题写入输入框。
  } // 结束快捷问题填充函数。

  return ( // 返回页面结构。
    <div className="app-shell"> {/* 创建应用外层容器。 */}
      <aside className="sidebar"> {/* 创建左侧导航栏。 */}
        <div className="brand">🔬 DetectionAI</div> {/* 显示产品名称。 */}
        <button className="new-chat" onClick={() => setMessages([])}>＋ 新建对话</button> {/* 提供新建对话按钮。 */}
        <div className="sidebar-section">知识能力</div> {/* 显示能力分组标题。 */}
        <div className="capability">全文 RAG 检索</div> {/* 显示全文检索能力。 */}
        <div className="capability">GraphRAG 关系推理</div> {/* 显示知识图谱能力。 */}
        <div className="capability">结构图多模态解析</div> {/* 显示图片解析能力。 */}
        <div className="capability">来源文件和章节溯源</div> {/* 显示引用溯源能力。 */}
        <div className="sidebar-note">公司网关地址和模型名称在后端配置，不写入前端代码。</div> {/* 提示网关配置位置。 */}
      </aside> {/* 结束左侧导航栏。 */}
      <main className="main-panel"> {/* 创建主聊天区域。 */}
        <header className="hero"> {/* 创建产品介绍区域。 */}
          <div><span className="eyebrow">FAB ENGINEERING COPILOT</span><h1>Detection 智能助手</h1><p>理论原理、历史 Case、SOP 和结构图一起分析。</p></div> {/* 显示产品标题和说明。 */}
          <div className="status-pill">本地服务可用</div> {/* 显示当前服务状态。 */}
        </header> {/* 结束产品介绍区域。 */}
        {messages.length === 0 && <section className="welcome"> {/* 在无消息时显示欢迎区。 */}
          <h2>从一个 Detection 问题开始</h2> {/* 显示欢迎标题。 */}
          <p>输入 defect、机台、SPC、光学原理或 SOP 问题。</p> {/* 显示输入引导。 */}
          <div className="quick-grid">{quickPrompts.map((prompt) => <button key={prompt} onClick={() => useQuickPrompt(prompt)}>{prompt}</button>)}</div> {/* 显示快捷问题按钮。 */}
        </section>} {/* 结束欢迎区。 */}
        <section className="messages"> {/* 创建消息列表区域。 */}
          {messages.map((message, index) => <article className={`message ${message.role}`} key={`${message.role}-${index}`}> {/* 渲染每条对话消息。 */}
            <div className="message-role">{message.role === "user" ? "你" : "DetectionAI"}</div> {/* 显示消息角色。 */}
            <div className="message-content">{message.content}</div> {/* 显示消息正文。 */}
            {message.citations && message.citations.length > 0 && <div className="citations"><strong>来源溯源</strong>{message.citations.map((citation, citationIndex) => <div className="citation" key={`${citation.title}-${citationIndex}`}><span>{citation.title}</span><small>{citation.location || citation.source_type}</small>{citation.excerpt && <p>{citation.excerpt}</p>}</div>)}</div>} {/* 显示助手回答引用。 */}
          </article>)} {/* 结束消息列表。 */}
          {loading && <div className="loading">正在汇总知识库和 Detection 证据…</div>} {/* 显示请求加载提示。 */}
          {error && <div className="error">{error}</div>} {/* 显示错误提示。 */}
        </section> {/* 结束消息列表区域。 */}
        <form className="composer" onSubmit={sendMessage}> {/* 创建聊天输入表单。 */}
          <textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder="例如：分析 LOT-240921-A01 的 edge ring 缺陷" rows={3} /> {/* 创建问题输入框。 */}
          <div className="composer-actions"><span>后端接口：/api/chat</span><button type="submit" disabled={loading || !query.trim()}>发送</button></div> {/* 显示接口提示和发送按钮。 */}
        </form> {/* 结束聊天输入表单。 */}
      </main> {/* 结束主聊天区域。 */}
    </div> {/* 结束应用外层容器。 */}
  ); // 结束页面结构返回。
} // 结束应用组件。

export default App; // 导出应用主组件。
