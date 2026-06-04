HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>LeetCode 题目文档</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        body {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            background: #f5f7fa;
        }
        header {
            background: #2c3e50;
            color: white;
            padding: 16px 24px;
            font-size: 18px;
            font-weight: 500;
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 100;
        }
        .container {
            display: flex;
            margin-top: 60px;
            flex: 1;
        }
        aside {
            width: 260px;
            background: white;
            border-right: 1px solid #e4e7ed;
            padding: 24px 0;
            height: calc(100vh - 60px);
            position: fixed;
            overflow-y: auto;
        }
        .aside-title {
            padding: 0 20px 12px;
            font-size: 14px;
            color: #909399;
        }
        .menu-list { list-style: none; }
        .menu-item a {
            display: block;
            padding: 10px 20px;
            color: #303133;
            text-decoration: none;
            font-size: 14px;
        }
        .menu-item a:hover {
            background: #f5f7fa;
            color: #409eff;
        }
        main {
            flex: 1;
            margin-left: 260px;
            padding: 30px;
        }
        .content-box {
            background: white;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .content-title {
            font-size: 20px;
            font-weight: 500;
            color: #303133;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e4e7ed;
        }
        .diff {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            color: white;
            margin-right: 8px;
        }
        .easy { background: #67c23a; }
        .medium { background: #e6a23c; }
        .hard { background: #f56c6c; }
        .content-body {
            line-height: 1.7;
            color: #606266;
            white-space: pre-wrap;
            background: #fafafa;
            padding: 16px;
            border-radius: 6px;
            border-left: 3px solid #409eff;
        }
        .url {
            color: #409eff;
            word-break: break-all;
            font-size: 13px;
            margin-bottom: 12px;
        }
        .content-body img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1em 0;
}
    </style>
</head>
<body>
    <header>LeetCode 算法题目文档</header>
    <div class="container">
        <aside>
            <div class="aside-title">📚 题目列表</div>
            <ul class="menu-list">{{MENU}}</ul>
        </aside>
        <main>{{CONTENT}}</main>
    </div>
</body>
</html>
"""