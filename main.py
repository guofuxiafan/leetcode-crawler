import asyncio
import re
from playwright.async_api import async_playwright

from config import *
from html_template import HTML_TEMPLATE


# ==============================
# HTML 生成
# ==============================
def gen_menu(items):
    return "\n".join([
        f'<li class="menu-item"><a href="#p{i["序号"]}">{i["序号"]}. {i["题目名称"]}</a></li>'
        for i in items
    ])


def gen_content(items):
    parts = []
    for i in items:
        cls = {"简单": "easy", "中等": "medium", "困难": "hard"}.get(i["难度"], "easy")
        parts.append(f'''
        <div class="content-box" id="p{i["序号"]}">
            <div class="content-title"><span class="diff {cls}">{i["难度"]}</span>{i["序号"]}. {i["题目名称"]}</div>
            <div class="url">链接：{i["题目链接"]}</div>
            <div class="content-body">{i["题目描述"]}</div>
        </div>''')
    return "\n".join(parts)


# ==============================
# 爬取单题
# ==============================
async def crawl_one_page(page, url, idx):
    try:
        print(f"[{idx}] 正在爬取: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_selector(".text-title-large a", timeout=30000)

        title = await page.locator(".text-title-large a").inner_text()
        diff = await page.locator("[class*='text-difficulty-']").inner_text()
        content = await page.locator(".HTMLContent_html__0OZLp").first.inner_html()

        return {
            "序号": idx,
            "题目名称": title.strip(),
            "难度": diff.strip(),
            "题目链接": url,
            "题目描述": content.strip()
        }
    except Exception as e:
        print(f"[{idx}] 爬取失败: {str(e)[:60]}")
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
        await page.wait_for_selector('a[href^="/problems/"]', timeout=15000)
        elements = await page.locator("a[href^='/problems/']").all()
        urls = []
        for e in elements:
            href = await e.get_attribute("href")
            if href and "?" not in href:
                urls.append(f"https://leetcode.cn{href}/description/")
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
# 主程序（不变）
# ==============================
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-images"]
        )

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