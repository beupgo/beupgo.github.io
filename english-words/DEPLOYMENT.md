# English Words

访问地址：https://beupgo.github.io/english-words/

此目录是 Qwerty Learner 的静态构建产物，包含页面、词库、图片与音效，可由 GitHub Pages 直接托管。

上游项目：https://github.com/RealKai42/qwerty-learner

构建源码仓库：https://github.com/beupgo/qwerty-learner

许可证见 [LICENSE](LICENSE)。

## 子目录部署适配（2026-09-12）

- `index.html` 设置 `<base href="/english-words/">`，确保资源和音效从本目录加载。
- `assets/index-a3f343d1.js` 的 BrowserRouter basename、词库 URL 和窗口缩放时的首页跳转使用 `/english-words/`。
- `gallery`、`analysis`、`error-book`、`friend-links`、`mobile` 各自提供同一应用的 `index.html`，支持 GitHub Pages 直接访问和刷新子页面。
- 不挂载仅适用于 Vercel 的 Analytics 组件，避免 GitHub Pages 请求不存在的统计脚本。
- 仓库 README 和导航首页提供独立入口，不依赖只扫描根目录 HTML 的目录生成脚本。

## 更新

后续替换构建产物时，需要保留以上子目录配置；若从源码重建，应同步设置 Vite 的 base、React Router 的 basename 和词库请求前缀。更新主入口后同步五个子路由入口。

本地验证：在仓库根目录运行 `python3 -m http.server 8765`，访问 `http://localhost:8765/english-words/`，检查词库切换、打字练习以及子页面刷新。

发音等原应用的外部服务仍需要联网；此静态部署未增加后端服务。
