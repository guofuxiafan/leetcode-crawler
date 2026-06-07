import asyncio
import os
import platform
import re
from playwright.async_api import async_playwright

from config import *
from html_template import HTML_TEMPLATE


def find_chrome():
    """优先使用配置的 CHROME_PATH，否则按操作系统自动探测。"""
    if CHROME_PATH and os.path.exists(CHROME_PATH):
        return CHROME_PATH

    system = platform.system()
    candidates = []
    if system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    elif system == "Darwin":  # macOS
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    else:  # Linux / 其他
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ==============================
# HTML 生成
# ==============================
def gen_menu(items):
    order = ["简单", "中等", "困难"]
    groups = {k: [] for k in order}
    for i in items:
        diff = i["难度"] if i["难度"] in order else "简单"
        groups[diff].append(i)

    parts = []
    for diff in order:
        lst = groups[diff]
        if not lst:
            continue
        cls = {"简单": "easy", "中等": "medium", "困难": "hard"}[diff]
        parts.append(f'<li class="menu-group"><span class="menu-diff {cls}">{diff}</span><span class="menu-count">{len(lst)}题</span></li>')
        for i in lst:
            parts.append(f'<li class="menu-item"><a href="#p{i["序号"]}">{i["题目名称"]}</a></li>')
    return "\n".join(parts)


def gen_content(items):
    parts = []
    for i in items:
        cls = {"简单": "easy", "中等": "medium", "困难": "hard"}.get(i["难度"], "easy")
        parts.append(f'''
        <div class="content-box" id="p{i["序号"]}">
            <div class="content-title"><span class="diff {cls}">{i["难度"]}</span>{i["题目名称"]}</div>
            <div class="url">链接：{i["题目链接"]}</div>
            <div class="content-body">{i["题目描述"]}</div>
        </div>''')
    return "\n".join(parts)


# ==============================
# 爬取单题
# ==============================
async def crawl_one_page(page, url, idx, retries=2):
    for attempt in range(retries + 1):
        try:
            print(f"[{idx}] 正在爬取{' (重试)' if attempt > 0 else ''}: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_selector(".text-title-large a", timeout=30000)

            raw_title = await page.locator(".text-title-large a").inner_text()
            title = re.sub(r'^\d+\.\s*', '', raw_title.strip())
            diff = await page.locator("[class*='text-difficulty-']").inner_text()
            content = await page.locator(".HTMLContent_html__0OZLp").first.inner_html()

            return {
                "序号": idx,
                "题目名称": title,
                "难度": diff.strip(),
                "题目链接": url,
                "题目描述": content.strip()
            }
        except Exception as e:
            err_msg = str(e)[:60]
            if attempt < retries:
                print(f"[{idx}] 爬取失败，准备重试: {err_msg}")
                await page.wait_for_timeout(2000)
            else:
                print(f"[{idx}] 爬取失败（已重试{retries}次）: {err_msg}")
    return None


# ==============================
# 获取题目URLs
# ==============================
async def get_problem_urls(page):
    cn_url = page.url

    # --------------------------
    # 普通题库
    # --------------------------
    if "problemset" in cn_url:
        print("普通题库模式")
        # 等待表格或列表加载
        await page.wait_for_selector('a[href^="/problems/"]', timeout=15000)

        # 滚动到底部加载全部题目
        last_count = 0
        for _ in range(20):
            elements = await page.locator("a[href^='/problems/']").all()
            if len(elements) == last_count:
                break
            last_count = len(elements)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(800)
        print(f"页面中共找到 {last_count} 个 /problems/ 链接")

        seen = set()
        urls = []
        for e in elements:
            href = await e.get_attribute("href")
            if not href or "?" in href:
                continue
            # 严格匹配 /problems/<slug>/ 格式，过滤 editorial/solution
            m = re.match(r'^/problems/([^/]+)/?$', href)
            if not m:
                continue
            slug = m.group(1)
            if slug in seen:
                continue
            seen.add(slug)
            urls.append(f"https://leetcode.cn/problems/{slug}/description/")

        print(f"去重后有效题目链接: {len(urls)} 个")
        return urls[:CRAWL_LIMIT]

    # --------------------------
    # 标签题单
    # --------------------------
    elif "problem-list" in cn_url:
        print("标签题单模式")
        # 等待题目链接出现
        await page.wait_for_selector('a[href^="/problems/"]', timeout=15000)
        elements = await page.locator('a[href^="/problems/"]').all()
        urls = []
        for e in elements:
            href = await e.get_attribute("href")
            if href:
                slug = href.split("/problems/")[1].split("/")[0]
                full_url = f"https://leetcode.cn/problems/{slug}/description/"
                if full_url not in urls:
                    urls.append(full_url)
        final_urls = urls[:CRAWL_LIMIT]
        print(f"共获取 {len(urls)} 个题目，按配置取前 {len(final_urls)} 题开始爬取\n")
        return final_urls

    # --------------------------
    # 学习计划：自动跳国际版+精准提取slug
    # --------------------------
    elif "studyplan" in cn_url:
        print("学习计划：自动加载国际版全部题目")
        plan_id = cn_url.strip("/").split("/")[-1]
        en_url = f"https://leetcode.com/studyplan/{plan_id}/"

        print(f"跳转到国际版题单: {en_url}")
        await page.goto(en_url, timeout=90000)
        await page.wait_for_timeout(3000)

        # 滚动加载全部题目
        for i in range(15):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)
        await page.wait_for_timeout(3000)

        # 精准定位题目链接
        rows = page.locator('[class*="hover:bg-lc-fill-02"]')
        count = await rows.count()
        print(f"共找到 {count} 行题目")

        slugs = []
        for i in range(count):
            row = rows.nth(i)
            # 获取该行内所有链接的 href 属性
            hrefs = await row.locator('a').get_attribute('href')
            if hrefs:
                # 匹配 problems/ 后面的 slug，例如 /problems/two-sum/editorial 提取出 two-sum
                match = re.search(r'/problems/([^/]+)', hrefs)
                if match:
                    slugs.append(match.group(1))

        # 去重（同时保留顺序）
        slugs = list(dict.fromkeys(slugs))
        print(f"去重后有效题目: {len(slugs)}个")

        # 拼接中文站链接（带plan_id有助于稳定）
        urls = [f"https://leetcode.cn/problems/{slug}/?envType=study-plan-v2&envId={plan_id}" for slug in
                slugs[:CRAWL_LIMIT]]
        print(f"按配置截取前 {len(urls)} 题开始爬取\n")
        return urls




    return []


# ==============================
# 主程序
# ==============================
async def main():
    async with async_playwright() as p:
        chrome_path = find_chrome()
        launch_opts = dict(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-images"]
        )
        if chrome_path:
            launch_opts["executable_path"] = chrome_path
            print(f"使用系统 Chrome: {chrome_path}")
        else:
            print("未检测到系统 Chrome，使用 Playwright 自带 Chromium")

        browser = await p.chromium.launch_persistent_context(**launch_opts)

        page = await browser.new_page()
        print(f"配置文件URL: {PROBLEM_LIST_URL}")
        await page.goto(PROBLEM_LIST_URL, timeout=60000)

        all_urls = await get_problem_urls(page)
        await page.close()

        if not all_urls:
            print("未获取到题目链接")
            await browser.close()
            return

        print(f"\n开始并发爬取 {len(all_urls)} 题\n")

        sem = asyncio.Semaphore(MAX_PARALLEL)
        tasks = []

        async def job(idx, u):
            async with sem:
                np = await browser.new_page()
                res = await crawl_one_page(np, u, idx)
                await np.close()
                return res

        for idx, u in enumerate(all_urls, 1):
            tasks.append(asyncio.create_task(job(idx, u)))

        results = await asyncio.gather(*tasks)
        final_data = [r for r in results if r]

        if final_data:
            menu = gen_menu(final_data)
            content = gen_content(final_data)
            html = HTML_TEMPLATE.replace("{{MENU}}", menu).replace("{{CONTENT}}", content)
            with open(HTML_OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"\n全部完成！成功爬取 {len(final_data)} 题")
        else:
            print("\n未爬取到有效数据")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())