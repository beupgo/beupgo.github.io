# 人教版小学数学 · 五 / 六年级知识点学习页

> 面向小学高年级的**人教版(PEP)数学**知识点学习页面:图形化讲解、母题精讲、生活应用三大板块,单文件、纯离线、手机 / 平板 / 电脑均可直接打开。

## 在线访问

| 年级 | 在线地址 |
|---|---|
| 五年级 | https://cucygh.github.io/<repo>/grade5.html |
| 六年级 | https://cucygh.github.io/<repo>/grade6.html |
| 导航首页 | https://cucygh.github.io/<repo>/ |

> 把 `<repo>` 换成仓库名。
> 若仓库名就叫 `cucygh.github.io`,则去掉路径里的 `/<repo>`,直接是 `https://cucygh.github.io/grade5.html`。

## 功能特点

- **三大板块**:知识点(图文/动画讲解)· 母题(典型例题分步精讲)· 应用(生活场景练习)。
- **图形结合**:大量 SVG 手绘示意图与动画,把抽象概念(如比例、分数除法、数与形)讲直观,帮助形成长期记忆。
- **单文件离线**:每个页面所有 CSS / JS / 图标(Lucide SVG 雪碧图)全部内联,断网也能用,无任何外部依赖。
- **移动端友好**:自适应布局,底部标签栏导航,适配手机与 iPad。
- **微信兼容**:纯 ES5 + SMIL 动画,兼容微信内置浏览器(X5 内核)。

## 目录结构

```
.
├─ index.html      # 导航首页(五 / 六年级入口)
├─ grade5.html     # 五年级数学(15 个单元)
├─ grade6.html     # 六年级数学(12 个单元)
└─ README.md
```

> 仓库里的文件建议使用英文名 `grade5.html` / `grade6.html`。
> 中文文件名(如「五年级数学.html」)在 GitHub Pages 链接里需要 URL 编码,容易出错,不推荐直接作为线上路径。

## 内容概览

**五年级(共 15 个单元)**
小数乘法 · 位置 · 小数除法 · 可能性 · 简易方程 · 多边形的面积 · 植树问题 · 观察物体(三) · 因数与倍数 · 长方体和正方体 · 分数的意义和性质 · 分数的加法和减法 · 图形的运动(三) · 折线统计图 · 打电话

**六年级(共 12 个单元)**
分数乘法 · 位置与方向(二) · 分数除法 · 比 · 圆 · 百分数 · 扇形统计图 · 数学广角(数与形) · 比例 · 圆柱与圆锥 · 百分数(二) · 统计与概率(整理复习)

## 部署到 GitHub Pages

1. 新建一个 GitHub 仓库(如 `math-notes`),把 `grade5.html`、`grade6.html`、`index.html`、`README.md` 上传到仓库根目录。
2. 进入仓库 **Settings → Pages**。
3. **Build and deployment → Source** 选 **Deploy from a branch**;**Branch** 选 `main`(或 `master`),目录选 `/ (root)`,点 **Save**。
4. 等 1–2 分钟,页面顶部会出现发布地址 `https://cucygh.github.io/<repo>/`,即可访问。

> 小技巧:iPad / iPhone 用 Safari 打开在线地址后,点分享 → **添加到主屏幕**,即可像 App 一样全屏使用。

## 更新内容

直接用新的 html 覆盖仓库里对应文件并提交(commit),GitHub Pages 会自动重新发布,通常 1–2 分钟生效。

## 许可与说明

- 内容依据人教版(PEP)小学数学教材编写整理,供个人学习使用。
- 页面图标复用自开源图标库 [Lucide](https://lucide.dev)(ISC License)。
