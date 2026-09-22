import { defineConfig } from "vite"; // 导入 Vite 配置函数。
import react from "@vitejs/plugin-react"; // 导入 React Vite 插件。

export default defineConfig({ // 导出 Vite 配置对象。
  plugins: [react()], // 启用 React 编译插件。
  server: { // 配置开发服务器。
    port: 5173, // 固定前端开发端口。
    proxy: { // 配置 API 代理避免开发环境跨域。
      "/api": "http://127.0.0.1:8000", // 将前端 API 请求转发到 FastAPI 后端。
    }, // 结束 API 代理配置。
  }, // 结束开发服务器配置。
}); // 结束 Vite 配置。
