"""播种示例数据 — 用于开发环境快速填充演示数据"""
import pymysql, json, datetime, os

conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    port=int(os.getenv('MYSQL_PORT', '3306')),
    user=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', ''),
    database=os.getenv('MYSQL_DATABASE', 'ai_test_platform'),
    charset='utf8mb4',
)
cursor = conn.cursor()

# 1. Project
cursor.execute(
    "INSERT INTO projects (name, description, status, created_by, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s)",
    ('电商平台测试', '某电商平台 Web 端功能测试项目，覆盖用户登录、商品搜索、购物车、下单等核心流程',
     'active', 1, datetime.datetime.now(), datetime.datetime.now()))
proj_id = cursor.lastrowid
print(f'Created project: {proj_id}')

# 2. Test Cases
cases = [
    ('用户登录-正常流程', '验证用户使用正确的用户名和密码能够成功登录系统', 'P0', 'approved',
     '用户已注册且账户状态正常',
     [{'seq': 1, 'action': 'navigate', 'target': '/login', 'expected': '显示登录页面'},
      {'seq': 2, 'action': 'input', 'target': '#username', 'value': 'testuser', 'expected': '用户名输入成功'},
      {'seq': 3, 'action': 'input', 'target': '#password', 'value': 'password123', 'expected': '密码输入成功'},
      {'seq': 4, 'action': 'click', 'target': '#loginBtn', 'expected': '跳转到首页，显示用户名信息'}],
     ['smoke', 'login'], 'login'),
    ('商品搜索-关键词搜索', '验证用户输入关键词后能正确搜索到相关商品', 'P0', 'approved',
     '用户已登录，系统中存在相关商品数据',
     [{'seq': 1, 'action': 'navigate', 'target': '/search', 'expected': '显示搜索页面'},
      {'seq': 2, 'action': 'input', 'target': '#searchInput', 'value': 'iPhone 15', 'expected': '关键词输入成功'},
      {'seq': 3, 'action': 'click', 'target': '#searchBtn', 'expected': '显示搜索结果列表，包含相关商品'}],
     ['smoke', 'search'], 'search'),
    ('购物车-添加商品', '验证用户能将商品添加到购物车', 'P1', 'approved',
     '用户已登录，商品详情页可正常访问',
     [{'seq': 1, 'action': 'navigate', 'target': '/product/123', 'expected': '显示商品详情页'},
      {'seq': 2, 'action': 'click', 'target': '#addToCartBtn', 'expected': '已加入购物车'},
      {'seq': 3, 'action': 'navigate', 'target': '/cart', 'expected': '购物车中显示刚添加的商品'}],
     ['regression', 'cart'], 'cart'),
    ('用户注册-验证码校验', '验证注册时验证码校验功能是否正常', 'P2', 'reviewing',
     '手机号未注册',
     [{'seq': 1, 'action': 'navigate', 'target': '/register', 'expected': '显示注册页面'},
      {'seq': 2, 'action': 'input', 'target': '#phone', 'value': '13800138000', 'expected': '手机号输入成功'},
      {'seq': 3, 'action': 'click', 'target': '#sendCodeBtn', 'expected': '发送验证码，按钮显示倒计时'},
      {'seq': 4, 'action': 'input', 'target': '#code', 'value': '123456', 'expected': '验证码输入成功'}],
     ['register'], 'register'),
    ('订单-提交订单', '验证用户能正确提交订单', 'P1', 'draft',
     '购物车中有商品，用户已填写收货地址',
     [{'seq': 1, 'action': 'navigate', 'target': '/cart', 'expected': '显示购物车页面'},
      {'seq': 2, 'action': 'click', 'target': '#checkoutBtn', 'expected': '跳转到结算页面'},
      {'seq': 3, 'action': 'click', 'target': '#submitOrderBtn', 'expected': '订单提交成功，显示订单号'}],
     ['order'], 'order'),
]
case_ids = []
for title, desc, priority, status, precond, steps, tags, module in cases:
    cursor.execute(
        "INSERT INTO testcases (project_id, title, description, priority, status, preconditions, steps, tags, module, created_by, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (proj_id, title, desc, priority, status, precond,
         json.dumps(steps, ensure_ascii=False),
         json.dumps(tags, ensure_ascii=False),
         module, 1, datetime.datetime.now(), datetime.datetime.now()))
    case_ids.append(cursor.lastrowid)
    print(f'Created testcase {cursor.lastrowid}: {title}')

# 3. Test Plan
cursor.execute(
    "INSERT INTO testplans (project_id, name, description, case_ids, status, cron_expr, max_retries, timeout, created_by, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
    (proj_id, '核心流程回归测试 v1.0',
     '覆盖登录、搜索、购物车、下单等核心业务流程的回归测试计划',
     json.dumps(case_ids), 'completed', None, 2, 600, 1,
     datetime.datetime.now(), datetime.datetime.now()))
plan_id = cursor.lastrowid
print(f'Created testplan: {plan_id}')

# 4. Executions
exec_statuses = ['passed', 'passed', 'failed', 'passed', 'pending']
exec_ids = []
for i, cid in enumerate(case_ids):
    status = exec_statuses[i]
    start = datetime.datetime.now() - datetime.timedelta(hours=i+1)
    end = start + datetime.timedelta(seconds=15 + i * 10)
    duration = (end - start).total_seconds() * 1000
    log_text = f'[Test] Executing case {cid}...\n[Step] Starting browser...\n[AI] Analyzing page...\n[Result] {status}'
    screenshots = json.dumps(['screenshot_001.png', 'screenshot_002.png']) if status == 'failed' else json.dumps([])
    error = 'Element #checkoutBtn not found - page structure changed' if status == 'failed' else None

    cursor.execute(
        "INSERT INTO executions (plan_id, case_id, status, trigger_type, start_time, end_time, duration, error_message, screenshots, log, steps, retry_count, executed_by, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (plan_id, cid, status, 'manual', start, end, duration, error, screenshots, log_text,
         json.dumps([]), 0, 'admin', datetime.datetime.now()))
    exec_ids.append(cursor.lastrowid)
    print(f'Created execution {cursor.lastrowid} for case {cid}: {status}')

# 5. Reports (with all required columns)
case_results_detail = [
    {'case_id': case_ids[0], 'case_title': '用户登录-正常流程', 'priority': 'P0', 'module': 'login',
     'status': 'passed', 'duration': 15200.0, 'error_message': None, 'screenshots': [], 'steps': []},
    {'case_id': case_ids[1], 'case_title': '商品搜索-关键词搜索', 'priority': 'P0', 'module': 'search',
     'status': 'passed', 'duration': 18800.0, 'error_message': None, 'screenshots': [], 'steps': []},
    {'case_id': case_ids[2], 'case_title': '购物车-添加商品', 'priority': 'P1', 'module': 'cart',
     'status': 'failed', 'duration': 25200.0,
     'error_message': 'Element #checkoutBtn not found',
     'screenshots': ['screenshot_001.png', 'screenshot_002.png'], 'steps': []},
    {'case_id': case_ids[3], 'case_title': '用户注册-验证码校验', 'priority': 'P2', 'module': 'register',
     'status': 'passed', 'duration': 16300.0, 'error_message': None, 'screenshots': [], 'steps': []},
    {'case_id': case_ids[4], 'case_title': '订单-提交订单', 'priority': 'P1', 'module': 'order',
     'status': 'skipped', 'duration': 0, 'error_message': None, 'screenshots': [], 'steps': []},
]
start_time = datetime.datetime.now() - datetime.timedelta(hours=5)
end_time = datetime.datetime.now()

cursor.execute(
    "INSERT INTO reports (plan_id, plan_name, project_id, project_name, total_count, passed_count, failed_count, skipped_count, error_count, pass_rate, duration, case_results, start_time, end_time, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
    (plan_id, '核心流程回归测试 v1.0', proj_id, '电商平台测试',
     len(case_ids), 3, 1, 1, 0, 75.00, 125500.0,
     json.dumps(case_results_detail, ensure_ascii=False),
     start_time, end_time, datetime.datetime.now()))
report_id = cursor.lastrowid
print(f'Created report: {report_id}')

# 6. Case Results (detail rows for report)
case_results_data = [
    (report_id, case_ids[0], '用户登录-正常流程', 'P0', 'login', 'passed', 15200.0, None, '[]', '[]'),
    (report_id, case_ids[1], '商品搜索-关键词搜索', 'P0', 'search', 'passed', 18800.0, None, '[]', '[]'),
    (report_id, case_ids[2], '购物车-添加商品', 'P1', 'cart', 'failed', 25200.0,
     'Element #checkoutBtn not found', '["screenshot_001.png"]', '[]'),
    (report_id, case_ids[3], '用户注册-验证码校验', 'P2', 'register', 'passed', 16300.0, None, '[]', '[]'),
]
for cr in case_results_data:
    cursor.execute(
        "INSERT INTO case_results (report_id, case_id, case_title, priority, module, status, duration, error_message, screenshots, steps) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        cr)
print(f'Created {len(case_results_data)} case_results')

conn.commit()
cursor.close()
conn.close()
print('\nSeed data insertion complete!')
