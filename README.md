# LeetCode 题目爬虫使用指南

一个基于 Playwright 的 LeetCode 题目爬虫，支持普通题库、标签题单（problem-list）和学习计划（studyplan）三种模式，可自动过滤会员题目，将题目描述（含图片）、难度、链接等信息生成为美观的 HTML 文档。

## ✨ 功能特性

- 支持三种爬取模式：`/problemset/`、`/problem-list/`、`/studyplan/`
- **浏览器本地缓存** – 保留登录状态，避免重复登录，提高爬取效率，浏览器二次启动加速
- **并发爬取** – 通过 asyncio 控制并发数，快速下载多道题目
- 保留题目描述中的图片（`<img>` 标签完整保存）
- 输出单文件 HTML，支持侧边栏目录和图片自适应

## 🛠️ 环境要求

- Python 3.8+
- 操作系统：Windows / macOS / Linux

## 📦 安装与配置

### 1. 克隆或下载本项目

将 `main.py`、`config.py`、`html_template.py` 三个文件放在同一目录下。

### 2. 安装依赖

```bash
pip install playwright asyncio
playwright install chromium   # 安装 Chromium 浏览器内核
```

### 3. 修改配置文件 `config.py`

- `USER_DATA_DIR` – 浏览器用户数据目录（用于缓存登录状态）
- `HTML_OUTPUT_FILE` – 输出 HTML 文件名（可以自行更改输出）
- `CRAWL_LIMIT` – 一次爬取多少道题目
- `MAX_PARALLEL` – 并发数（建议 2~5，过高可能被限制）
- `PROBLEM_LIST_URL` – 目标 URL（根据注释切换不同模式）

### 4. 首次运行

首次运行可能会比较慢，也可能无法正常爬取，这都是正常现象，只需等待生成好浏览器缓存之后再运行即可正常爬取

## 🚀 使用方法

```bash
python main.py
```

程序将自动打开浏览器窗口（非无头模式），爬取完成后生成 HTML 文件并退出。

## ⚙️ 配置详解

| 配置项             | 说明                                  | 示例                |
| ------------------ | ------------------------------------- | ------------------- |
| `USER_DATA_DIR`    | 本地缓存目录，存放 Cookies 和登录状态 | `"my_chrome_cache"` |
| `HTML_OUTPUT_FILE` | 输出文件路径                          | `"OutputFile.html"` |
| `CRAWL_LIMIT`      | 最多爬取题数（不包含会员题）          | `5`                 |
| `MAX_PARALLEL`     | 同时爬取的页面数量                    | `2`                 |
| `PROBLEM_LIST_URL` | 目标页面 URL                          | 见下方三种模式      |

### 三种模式切换

1. **普通题库**  
   `PROBLEM_LIST_URL = "https://leetcode.cn/problemset/"`

2. **标签题单**（例如数组、字符串）  
   `PROBLEM_LIST_URL = "https://leetcode.cn/problem-list/array/"`

3. **学习计划**（例如热题 100、面试 150）  
   `PROBLEM_LIST_URL = "https://leetcode.cn/studyplan/top-100-liked/"`

> 注意：学习计划模式会自动跳转到国际站 `leetcode.com` 抓取题目 slug，再回到中文站获取详情，因此网络需要能访问 `leetcode.com`。另外国际站某些学习计划模式的题单网站可能与中文站有所不同造成无法爬取的情况，本项目为了轻量化没有做适配，敬请谅解。

## 💡 亮点解析

### 1. 浏览器本地缓存

**原理**：  
Playwright 的 `launch_persistent_context` 方法会创建一个持久的浏览器上下文，将用户数据（Cookies、LocalStorage、IndexedDB 等）保存到本地目录（`USER_DATA_DIR`）。  
首次运行后，手动登录 LeetCode 产生的登录凭证会被保存下来；之后再次运行，浏览器会直接加载这些缓存数据，**无需重新登录**。  
这不仅节省了每次启动时手动登录的麻烦，也绕过了部分反爬机制（因为你的请求看起来像一个真实登录用户）。当然，多数情况下我们也没有必要登录。另一方面，浏览器本地缓存可以加快二次启动的速度，不用每运行一次代码就重新加载浏览器底层资源一次，大大提升爬取效率

**优势**：  

- 降低被风控的概率  
- 提速：省去登录等待时间
- 加速二次启动

### 2. 并发爬取

**原理**：  
使用 Python 的 `asyncio` 协程 + `Semaphore` 信号量控制并发度。  
- 主函数为每个 URL 创建一个异步任务（`asyncio.create_task`）  
- 每个任务内部使用信号量 `sem.acquire()` 限制同时运行的协程数量不超过 `MAX_PARALLEL`  
- 所有任务并发执行，比串行爬取快数倍  

**为什么不是多线程**？  
Playwright 的异步 API 本身基于 asyncio，使用协程可以复用同一个浏览器进程（不同页面），资源开销更小，且不受 Python GIL 限制。

**并发度建议**：  
设置为 2~5 较为合适，过高的并发会导致页面加载资源冲突或被 LeetCode 服务器限制。

## ⚠️ 注意事项

- 学习计划模式依赖国际站 `leetcode.com` 的页面结构，若 LeetCode 改版可能导致失效，届时需调整选择器。
- 会员题目无法进行爬取（如果没有登录会员账号）可能会造成爬取数量不符的情况，需相应修改 `crawl_one_page` 中的逻辑。
- 输出的 HTML 文件中，图片链接为 LeetCode 官方 CDN 地址，需要联网才能正常显示。如需离线使用，请自行下载图片并替换路径。
- 请合理设置并发数，不要过高以免对 LeetCode 服务器造成压力。

## 📁 文件结构

```
.
├── main.py          # 主程序
├── config.py        # 配置文件
├── html_template.py # HTML 模板（内嵌 CSS）
└── my_chrome_cache/ # 浏览器缓存目录（第一次运行后自动生成）
```

## 🐛 常见问题

**Q: 获取题目中包含会员题目造成卡住怎么办？**  
A: 如果没有进行登录或者登录了但不是会员账号，在爬取题目时爬取到了会员题目界面可能会卡在不动，你只需要手动关闭会员题目标签页即可。

**Q: 图片不显示？**  
A: 本项目图片资源使用的是\<img>标签，资源来自leetcode官方图片资源，需要联网才能正常显示。

**Q: 在学习计划模式下爬取失败怎么办？**

A: 由于该模式下会用到leetcode国际站，最大的可能是页面没有加载出来，跳转到了错误的页面（比如首页），只需多次尝试直到成功即可。另外一种可能是国际站与中文站学习计划题单的后缀网址不同造成的。

## 📄 许可证

本项目仅供个人学习研究使用，请勿用于商业或大规模爬取，遵守 LeetCode 网站服务条款。

---

**Happy Coding!** 🎉