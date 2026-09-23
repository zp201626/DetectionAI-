// 保存当前会话消息，页面刷新后会重置。
const messages = document.getElementById("messages");
// 保存欢迎区域节点，首次发送消息后隐藏。
const welcome = document.getElementById("welcome");
// 保存问题输入框节点。
const queryInput = document.getElementById("query");
// 保存发送按钮节点。
const sendButton = document.getElementById("send");
// 保存文件选择节点。
const imageFile = document.getElementById("image-file");
// 保存文件名展示节点。
const fileName = document.getElementById("file-name");
// 保存知识文件选择节点。
const documentFile = document.getElementById("document-file");
// 保存知识文件名展示节点。
const documentName = document.getElementById("document-name");
// 保存图片解析结果节点。
const imageResult = document.getElementById("image-result");
// 保存服务状态节点。
const status = document.getElementById("status");
// 保存当前登录令牌。
let authToken = sessionStorage.getItem("detection_auth_token") || "";
// 保存当前用户信息。
let currentUser = JSON.parse(sessionStorage.getItem("detection_user") || "null");
// 统一生成带登录令牌的请求头。
function authHeaders(json = false) { return { ...(json ? { "Content-Type": "application/json" } : {}), ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}) }; }
// 切换登录面板和主界面显示状态。
function setLoggedIn(user) { document.getElementById("login-panel").classList.toggle("hidden", !user); document.querySelector(".app-shell").classList.toggle("hidden", !user); document.getElementById("knowledge-button").classList.toggle("hidden", !user || user.role !== "admin"); }
// 初始化登录状态。
setLoggedIn(currentUser);

// 处理账号密码登录。
document.getElementById("login-form").addEventListener("submit", async (event) => {
  // 阻止浏览器刷新页面。
  event.preventDefault();
  // 读取登录账号。
  const username = document.getElementById("username").value.trim();
  // 读取登录密码。
  const password = document.getElementById("password").value;
  // 清空旧错误。
  document.getElementById("login-error").textContent = "";
  try {
    // 调用登录接口。
    const response = await fetch("/api/auth/login", { method: "POST", headers: authHeaders(true), body: JSON.stringify({ username, password }) });
    // 检查登录状态。
    if (!response.ok) throw new Error("用户名或密码错误");
    // 读取登录结果。
    const data = await response.json();
    // 保存令牌。
    authToken = data.token;
    // 保存用户信息。
    currentUser = data.user;
    // 写入浏览器会话存储。
    sessionStorage.setItem("detection_auth_token", authToken);
    sessionStorage.setItem("detection_user", JSON.stringify(currentUser));
    // 显示主界面。
    setLoggedIn(currentUser);
  } catch (error) {
    // 显示登录失败原因。
    document.getElementById("login-error").textContent = error instanceof Error ? error.message : "登录失败";
  }
});

// 将纯文本安全地添加到消息区域。
function addMessage(role, content, citations = []) {
  // 创建消息外层元素。
  const article = document.createElement("article");
  // 设置消息样式类别。
  article.className = `message ${role}`;
  // 创建消息角色元素。
  const roleElement = document.createElement("div");
  // 设置消息角色文本。
  roleElement.className = "message-role";
  // 显示用户或助手名称。
  roleElement.textContent = role === "user" ? "你" : "DetectionAI";
  // 创建消息正文元素。
  const contentElement = document.createElement("div");
  // 保留换行并避免执行返回内容中的 HTML。
  contentElement.textContent = content;
  // 将角色和正文加入消息元素。
  article.append(roleElement, contentElement);
  // 只为助手消息创建来源区域。
  if (role === "assistant" && citations.length > 0) {
    // 创建引用容器。
    const citationBox = document.createElement("div");
    // 设置引用容器样式。
    citationBox.className = "citations";
    // 创建引用标题。
    const citationTitle = document.createElement("strong");
    // 设置引用标题文字。
    citationTitle.textContent = "来源溯源";
    // 将引用标题加入引用容器。
    citationBox.appendChild(citationTitle);
    // 遍历后端返回的引用。
    citations.forEach((citation) => {
      // 创建单条引用卡片。
      const item = document.createElement("div");
      // 设置引用卡片样式。
      item.className = "citation";
      // 创建引用标题元素。
      const title = document.createElement("span");
      // 设置引用标题样式。
      title.className = "citation-title";
      // 写入来源名称。
      title.textContent = citation.title || "未命名来源";
      // 创建引用位置元素。
      const location = document.createElement("small");
      // 设置引用位置样式。
      location.className = "citation-location";
      // 写入文件、章节或记录位置。
      location.textContent = citation.location || citation.source_type || "未知位置";
      // 将引用标题和位置加入卡片。
      item.append(title, location);
      // 如果有摘要则追加摘要元素。
      if (citation.excerpt) {
        // 创建摘要元素。
        const excerpt = document.createElement("p");
        // 设置摘要样式。
        excerpt.className = "citation-excerpt";
        // 写入摘要文本。
        excerpt.textContent = citation.excerpt;
        // 将摘要加入引用卡片。
        item.appendChild(excerpt);
      }
      // 将引用卡片加入引用区域。
      citationBox.appendChild(item);
    });
    // 将完整引用区域加入消息元素。
    article.appendChild(citationBox);
  }
  // 将消息元素加入页面消息列表。
  messages.appendChild(article);
  // 滚动到最新消息。
  article.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// 向 FastAPI 发送用户问题。
async function sendMessage(query) {
  // 清除输入首尾空白。
  const text = query.trim();
  // 输入为空时不发送请求。
  if (!text || sendButton.disabled) return;
  // 隐藏欢迎区域。
  welcome.classList.add("hidden");
  // 显示用户消息。
  addMessage("user", text);
  // 清空输入框。
  queryInput.value = "";
  // 禁用发送按钮防止重复请求。
  sendButton.disabled = true;
  // 更新状态提示。
  status.textContent = "正在分析";
  try {
    // 调用 FastAPI 聊天接口。
    const response = await fetch("/api/chat", { method: "POST", headers: authHeaders(true), body: JSON.stringify({ query: text }) });
    // 检查 HTTP 请求状态。
    if (!response.ok) throw new Error(`后端请求失败：${response.status}`);
    // 解析 JSON 响应。
    const data = await response.json();
    // 显示助手回答和引用。
    addMessage("assistant", data.answer || "后端没有返回回答。", data.citations || []);
    // 恢复服务状态。
    status.textContent = "本地服务可用";
  } catch (error) {
    // 将请求异常显示给用户。
    addMessage("assistant", error instanceof Error ? error.message : "请求失败，请检查后端服务。", []);
    // 标记服务可能异常。
    status.textContent = "请求失败";
  } finally {
    // 恢复发送按钮。
    sendButton.disabled = false;
  }
}

// 向 FastAPI 发送结构图并请求视觉解析。
async function analyzeImage(file) {
  // 没有文件时直接返回。
  if (!file) return;
  // 显示图片解析中状态。
  imageResult.className = "image-result";
  imageResult.textContent = "正在解析结构图…";
  try {
    // 创建文件上传表单。
    const formData = new FormData();
    // 将图片加入表单。
    formData.append("file", file);
    // 调用 FastAPI 图片接口。
    const response = await fetch("/api/images/analyze", { method: "POST", headers: authHeaders(), body: formData });
    // 检查图片接口状态。
    if (!response.ok) throw new Error(`图片解析失败：${response.status}`);
    // 解析图片接口结果。
    const data = await response.json();
    // 显示视觉模型返回结果。
    imageResult.textContent = data.answer || "图片解析接口没有返回内容。";
  } catch (error) {
    // 显示图片解析错误。
    imageResult.textContent = error instanceof Error ? error.message : "图片解析失败。";
  }
}

// 上传知识库文件并进入管理员审核队列。
async function uploadKnowledgeFile(file) {
  // 没有文件时直接返回。
  if (!file) return;
  // 创建文件上传表单。
  const formData = new FormData();
  // 将知识文件加入表单。
  formData.append("file", file);
  // 调用知识文件上传接口。
  const response = await fetch("/api/files", { method: "POST", headers: authHeaders(), body: formData });
  // 检查上传状态。
  if (!response.ok) throw new Error("知识文件上传失败");
  // 读取上传结果。
  const data = await response.json();
  // 在消息区域显示审核提示。
  addMessage("assistant", `${data.filename} 已上传，当前状态：${data.status || "pending"}，等待管理员审核。`, []);
}

// 监听聊天表单提交事件。
document.getElementById("composer").addEventListener("submit", (event) => {
  // 阻止浏览器刷新页面。
  event.preventDefault();
  // 发送输入框问题。
  sendMessage(queryInput.value);
});
// 加载知识库文件审核列表。
async function loadKnowledgeFiles() {
  // 获取知识库文件列表。
  const response = await fetch("/api/knowledge/files", { headers: authHeaders() });
  // 检查列表接口状态。
  if (!response.ok) throw new Error("无法加载知识库文件");
  // 解析文件列表。
  const files = await response.json();
  // 获取列表容器。
  const list = document.getElementById("file-list");
  // 清空旧列表。
  list.innerHTML = "";
  // 没有文件时显示提示。
  if (files.length === 0) { list.textContent = "暂无上传文件"; return; }
  // 创建文件审核卡片。
  files.forEach((file) => {
    // 创建文件卡片。
    const card = document.createElement("div");
    // 设置文件卡片样式。
    card.className = "file-card";
    // 创建文件信息文字。
    const info = document.createElement("div");
    // 使用安全纯文本显示文件信息。
    info.textContent = `${file.filename} | 上传人：${file.uploader} | 状态：${file.status} | 大小：${file.size} bytes`;
    // 将信息加入文件卡片。
    card.appendChild(info);
    // 仅为待审核文件添加审核按钮。
    if (file.status === "pending") {
      // 创建操作按钮区域。
      const actions = document.createElement("div");
      // 设置操作按钮样式。
      actions.className = "file-actions";
      // 创建通过按钮。
      const approve = document.createElement("button");
      // 设置通过按钮文字。
      approve.textContent = "审核通过";
      // 创建驳回按钮。
      const reject = document.createElement("button");
      // 设置驳回按钮文字。
      reject.textContent = "驳回";
      // 绑定通过操作。
      approve.onclick = () => reviewFile(file.id, "approved");
      // 绑定驳回操作。
      reject.onclick = () => reviewFile(file.id, "rejected");
      // 添加操作按钮。
      actions.append(approve, reject);
      // 添加操作区域。
      card.appendChild(actions);
    }
    // 仅为审核通过文件添加入库按钮。
    if (file.status === "approved") {
      // 创建入库按钮。
      const ingest = document.createElement("button");
      // 设置入库按钮文字。
      ingest.textContent = "文件入库";
      // 绑定入库操作。
      ingest.onclick = () => ingestFile(file.id);
      // 添加入库按钮。
      card.appendChild(ingest);
    }
    // 将文件卡片加入列表。
    list.appendChild(card);
  });
}
// 提交管理员审核结果。
async function reviewFile(fileId, reviewStatus) {
  // 调用审核接口。
  await fetch(`/api/knowledge/files/${fileId}/review`, { method: "POST", headers: authHeaders(true), body: JSON.stringify({ status: reviewStatus, comment: "管理员审核" }) });
  // 刷新文件列表。
  await loadKnowledgeFiles();
}
// 提交管理员入库操作。
async function ingestFile(fileId) {
  // 调用入库接口。
  await fetch(`/api/knowledge/files/${fileId}/ingest`, { method: "POST", headers: authHeaders() });
  // 刷新文件列表。
  await loadKnowledgeFiles();
}
// 打开或关闭知识库管理区域。
document.getElementById("knowledge-button").addEventListener("click", async () => { document.getElementById("knowledge-panel").classList.toggle("hidden"); await loadKnowledgeFiles(); });
// 绑定知识库刷新按钮。
document.getElementById("refresh-files").addEventListener("click", loadKnowledgeFiles);
// 绑定退出登录按钮。
document.getElementById("logout-button").addEventListener("click", () => { sessionStorage.clear(); authToken = ""; currentUser = null; setLoggedIn(null); });
// 监听新建对话按钮。
document.getElementById("new-chat").addEventListener("click", () => {
  // 清空消息列表。
  messages.innerHTML = "";
  // 显示欢迎区域。
  welcome.classList.remove("hidden");
  // 清空图片解析结果。
  imageResult.className = "image-result hidden";
  // 清空输入框。
  queryInput.value = "";
});
// 监听快捷问题按钮。
document.querySelectorAll(".quick").forEach((button) => button.addEventListener("click", () => sendMessage(button.dataset.query || "")));
// 监听图片选择事件。
imageFile.addEventListener("change", () => {
  // 读取用户选择的图片。
  const file = imageFile.files[0];
  // 更新图片文件名显示。
  fileName.textContent = file ? file.name : "未选择图片";
  // 有图片时调用解析接口。
  analyzeImage(file);
});
// 监听知识文件选择事件。
documentFile.addEventListener("change", async () => {
  // 读取用户选择的知识文件。
  const file = documentFile.files[0];
  // 更新知识文件名显示。
  documentName.textContent = file ? file.name : "未选择文件";
  // 有文件时上传到待审核队列。
  try { await uploadKnowledgeFile(file); } catch (error) { addMessage("assistant", error instanceof Error ? error.message : "知识文件上传失败。", []); }
});
// 页面加载时检查后端健康状态。
fetch("/api/health").then((response) => response.json()).then((data) => { status.textContent = data.status === "ok" ? "本地服务可用" : "服务异常"; }).catch(() => { status.textContent = "后端未启动"; });
