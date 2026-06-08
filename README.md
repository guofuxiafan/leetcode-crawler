# LeetCode 爬虫 —— 自动化数据采集与算法题库整理

基于 **Playwright + asyncio** 的 LeetCode 中文站爬虫，支持**普通题库、标签题单、学习计划**三种模式。一键将题目描述、难度、链接抓取到本地，生成带侧边栏目录、按难度分组的**单文件 HTML** 文档。

---

## ✨ 效果预览

生成的 HTML 文档结构如下：

- **左侧目录栏**：按「简单 / 中等 / 困难」分组，带颜色标签，点击即可跳转
- **右侧内容区**：每道题独立卡片，包含题目标题、难度标识、原题链接、完整题目描述（保留图片与公式）
- **单文件输出**：零依赖，双击即用浏览器打开，无需数据库或服务器

---

## 🚀 功能特性

| 特性 | 说明 |
|------|------|
| 🌐 **三模式支持** | 普通题库 `problemset`、标签题单 `problem-list`、学习计划 `studyplan` |
| 🖥️ **浏览器持久化** | 缓存 Cookie 与登录态，二次启动加速，降低反爬风险 |
| ⚡ **异步并发** | `asyncio` + `Semaphore` 控制并发，20 题约 30~60 秒完成 |
| 🔍 **懒加载处理** | 自动滚动到底部，触发 LeetCode 懒加载，抓取完整题目列表 |
| 🌍 **学习计划兼容** | 自动跳转国际站提取 slug，解决中文站动态渲染无静态链接问题 |
| 🖼️ **富文本保留** | 完整保留题目描述中的图片、数学公式、代码块 |
| 🔧 **跨平台 Chrome 探测** | Windows / macOS / Linux 自动探测系统 Chrome 路径 |
| 🛡️ **失败重试** | 单题超时或异常时自动重试，避免整体中断 |

---

## 🛠️ 技术栈

- **浏览器自动化**：Playwright (async API)
- **并发控制**：Python `asyncio` + `Semaphore`
- **数据提取**：CSS Selector + 正则表达式
- **输出渲染**：内嵌 CSS 的 HTML 字符串模板

---

## 📦 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/guofuxiafan/leetcode-crawler.git
cd leetcode-crawler
```

### 2. 安装依赖

```bash
pip install playwright asyncio
playwright install chromium
```

> `playwright install chromium` 用于安装 Playwright 自带的 Chromium 内核。如果系统已安装 Chrome，项目会优先使用系统 Chrome。

### 3. 修改配置

编辑 `config.py`，修改以下关键项：

```python
# 目标 URL（三种模式任选其一，取消注释即可）
PROBLEM_LIST_URL = "https://leetcode.cn/problemset/"            # 普通题库
# PROBLEM_LIST_URL = "https://leetcode.cn/problem-list/array/"  # 标签题单：数组
# PROBLEM_LIST_URL = "https://leetcode.cn/studyplan/top-100-liked/"  # 学习计划：热题 100

# 爬取数量限制
CRAWL_LIMIT = 20

# 并发数（建议 2~5，过高可能被限制）
MAX_PARALLEL = 3
```

### 4. 运行

```bash
python main.py
```

程序会自动打开 Chrome 窗口（非无头模式），抓取完成后生成 `OutputFile.html`。

---

## 📋 三种爬取模式详解

### 模式一：普通题库

```python
PROBLEM_LIST_URL = "https://leetcode.cn/problemset/"
```

- 页面使用**懒加载**，程序会自动循环滚动到底部，直到全部题目加载完成
- 通过正则 `^/problems/([^/]+)/?$` 严格过滤题解、编辑页等杂质链接
- 使用 `set` 去重，生成完整 URL 列表

### 模式二：标签题单

```python
PROBLEM_LIST_URL = "https://leetcode.cn/problem-list/array/"
```

- 按算法专题分类（数组、字符串、动态规划等）
- 无懒加载，所有链接一次性获取
- 适合针对薄弱知识点集中训练

### 模式三：学习计划

```python
PROBLEM_LIST_URL = "https://leetcode.cn/studyplan/top-100-liked/"
```

- **核心难点**：中文站学习计划页面采用 JavaScript 动态渲染，HTML 源码中**不存在**题目静态链接
- **解决方案**：自动跳转至国际站 `leetcode.com`，在渲染后的 DOM 中提取 slug，再拼接回中文站 URL
- 保留学习计划参数（`envType=study-plan-v2`），确保生成的链接在 LeetCode 中仍能显示所属计划

---

## 📁 项目结构

```
leetcode-crawler/
├── main.py              # 主程序：三模式 URL 提取、异步并发爬取、HTML 生成
├── config.py            # 全局配置：URL、并发数、输出文件名、Chrome 路径
├── html_template.py     # HTML 模板（内嵌 CSS）：单文件输出、侧边栏目录、卡片式布局
├── my_chrome_cache/     # 浏览器持久化缓存目录（首次运行后自动生成）
├── OutputFile.html      # 生成的题目文档（示例）
└── README.md            # 本文档
```

---

## 💡 核心原理与技术亮点

### 1. 为什么用 Playwright 而非 requests？

LeetCode 题库页采用**前端渲染**（懒加载 + JS 动态插入内容），`requests` 只能获取原始 HTML 源码，无法拿到渲染后的题目链接。Playwright 操控真实浏览器，等待 JS 执行完毕后再提取 DOM，才能获取完整数据。

### 2. 持久化浏览器上下文

```python
browser = await p.chromium.launch_persistent_context(
    user_data_dir="my_chrome_cache"
)
```

- 将 Cookie、LocalStorage 等数据持久化到本地目录
- 首次手动登录后，后续运行自动复用登录态
- 浏览器缓存加速二次启动

### 3. 异步并发控制

```python
sem = asyncio.Semaphore(MAX_PARALLEL)

async def job(idx, url):
    async with sem:
        page = await browser.new_page()
        result = await crawl_one_page(page, url, idx)
        await page.close()
        return result
```

- `Semaphore(3)` 作为并发阀门，限制同时打开的标签页数量
- 每道题独立页面，隔离性强，单题失败不影响其他任务
- `asyncio.gather()` 汇总所有任务结果

### 4. 跨平台 Chrome 自动探测

```python
def find_chrome():
    # Windows / macOS / Linux 常见安装路径自动探测
    # 优先使用 config.py 中手动配置的路径
```

无需手动指定 Chrome 路径，项目自动适配不同操作系统。

---

## ⚙️ 配置项说明

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `USER_DATA_DIR` | `str` | 浏览器缓存目录，存放 Cookies 与登录状态 |
| `HTML_OUTPUT_FILE` | `str` | 输出 HTML 文件名 |
| `CRAWL_LIMIT` | `int` | 最多爬取题目数（防止全量抓取） |
| `MAX_PARALLEL` | `int` | 并发页面数，建议 2~5 |
| `PROBLEM_LIST_URL` | `str` | 目标页面 URL，三种模式任选 |
| `CHROME_PATH` | `str` | 手动指定 Chrome 路径，留空则自动探测 |

---

## ⚠️ 注意事项

1. **学习计划依赖国际站**：`studyplan` 模式需要网络可访问 `leetcode.com`，且依赖国际站当前页面结构。若 LeetCode 改版，可能需要更新 CSS 选择器。
2. **会员题目过滤**：未登录会员账号时，会员题目页面结构异常，会被自动跳过（表现为爬取数量少于配置值）。
3. **图片依赖网络**：输出 HTML 中的图片使用 LeetCode 官方 CDN 地址，离线环境下图片无法显示。
4. **合理控制并发**：请勿设置过高并发，避免对 LeetCode 服务器造成压力。
5. **首次运行**：首次启动可能较慢，需等待浏览器缓存目录生成，属正常现象。

---

## 📄 License

本项目仅供个人学习研究使用，请勿用于商业或大规模爬取。请遵守 LeetCode 网站服务条款与 `robots.txt` 协议。

---

**Happy Coding!** 🎉
