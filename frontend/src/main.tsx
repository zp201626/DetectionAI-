import React from "react"; // 导入 React 运行时。
import ReactDOM from "react-dom/client"; // 导入 React 根节点渲染器。
import App from "./App"; // 导入应用主组件。
import "./index.css"; // 导入全局样式。

ReactDOM.createRoot(document.getElementById("root")!).render( // 将 React 应用挂载到页面节点。
  <React.StrictMode> {/* 启用 React 严格模式帮助发现潜在问题。 */}
    <App /> {/* 渲染 DetectionAI 主应用。 */}
  </React.StrictMode>, // 结束严格模式节点。
); // 完成 React 应用挂载。
