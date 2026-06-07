# ==============================
# 全局配置文件（全部可修改）
# ==============================

# 浏览器缓存
USER_DATA_DIR = "my_chrome_cache"

# 输出 HTML
HTML_OUTPUT_FILE = "OutputFile.html"

# 爬取数量
CRAWL_LIMIT = 20#一次爬几道题

# 并发数
MAX_PARALLEL = 3

# 目标网站
#===普通题单===#
PROBLEM_LIST_URL = "https://leetcode.cn/problemset/"
#===学习计划===#
#    leetcode热题100
#PROBLEM_LIST_URL = "https://leetcode.cn/studyplan/top-100-liked/"

#    面试经典150题#
#PROBLEM_LIST_URL = "https://leetcode.cn/studyplan/top-interview-150/"

#    动态规划
# PROBLEM_LIST_URL = "https://leetcode.cn/studyplan/dynamic-programming/"

#===标签题单===#
#    数组
# PROBLEM_LIST_URL = "https://leetcode.cn/problem-list/array/"
#    字符串
# PROBLEM_LIST_URL = "https://leetcode.cn/problem-list/string/"

# 系统 Chrome 路径（留空则自动检测；Windows/Mac/Linux 均可）
# 例: CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PATH = ""

