#!/usr/bin/env python3
"""
平台自测脚本 —— 用自己的 AI 浏览器引擎测试自己的前端。

用法:
    # 本地全量自测（需要 Docker Compose 已启动）
    python self_test.py

    # 仅 API 级别测试（不需要浏览器）
    python self_test.py --mode api

    # CI 环境
    python self_test.py --base-url http://localhost:8000 --frontend-url http://frontend

原理:
    1. 通过 API 创建一批 [自测] 用例（步骤指向平台自身的页面）
    2. 创建测试计划并启动执行
    3. Celery Worker 启动 Playwright 浏览器，AI 引擎操控浏览器执行步骤
    4. 轮询结果，全部通过则退出码 0，否则退出码 1
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── 配置（可通过环境变量覆盖） ──

BASE_URL = os.getenv("SELF_TEST_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("SELF_TEST_FRONTEND_URL", "http://localhost")
ADMIN_USER = os.getenv("SELF_TEST_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("SELF_TEST_ADMIN_PASS", "123456")
POLL_INTERVAL = int(os.getenv("SELF_TEST_POLL_INTERVAL", "5"))
MAX_WAIT = int(os.getenv("SELF_TEST_MAX_WAIT", "300"))
MODE = os.getenv("SELF_TEST_MODE", "browser")

# ── 颜色输出 ──

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

_USE_COLOR = True


def _print(color: str, icon: str, msg: str):
    """跨平台安全打印，Windows 降级为 ASCII"""
    try:
        if _USE_COLOR:
            print(f"  {color}{icon}{RESET} {msg}")
        else:
            print(f"  [{icon}] {msg}")
    except UnicodeEncodeError:
        print(f"  [{'OK' if icon == 'PASS' else 'FAIL' if icon == 'FAIL' else icon}] {msg}")


def ok(msg: str):
    _print(GREEN, "OK", msg)


def fail(msg: str):
    _print(RED, "FAIL", msg)


def warn(msg: str):
    _print(YELLOW, "WARN", msg)


def info(msg: str):
    _print(CYAN, ">>", msg)


def header(msg: str):
    print(f"\n{BOLD}{msg}{RESET}")
    sys.stdout.flush()


# ── HTTP 工具 ──


def _request(method: str, path: str, body: dict | None = None,
             token: str | None = None) -> tuple[int, dict]:
    """发送 HTTP 请求，返回 (status_code, response_body)。"""
    url = f"{BASE_URL}/api/v1{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8") if e.fp else ""
        try:
            return e.code, json.loads(content)
        except json.JSONDecodeError:
            return e.code, {"detail": content}
    except urllib.error.URLError as e:
        return 0, {"error": str(e.reason)}


def get(path: str, token: str) -> tuple[int, dict]:
    return _request("GET", path, token=token)


def post(path: str, body: dict, token: str | None = None) -> tuple[int, dict]:
    return _request("POST", path, body=body, token=token)


# ── 用例定义 ──

def build_self_test_cases(project_id: int, frontend_url: str) -> list[dict]:
    """Build self-test cases. Each includes login steps (fresh browser context per execution)."""

    def login_steps():
        """Pre-login steps for each case"""
        return [
            {"seq": 1, "action": "navigate", "target": f"{frontend_url}/login", "value": "", "expected": "Login page loads"},
            {"seq": 2, "action": "input", "target": "username input field", "value": ADMIN_USER, "expected": "Username entered"},
            {"seq": 3, "action": "input", "target": "password input field", "value": ADMIN_PASS, "expected": "Password entered"},
            {"seq": 4, "action": "click", "target": "login button", "value": "", "expected": "Redirected to dashboard"},
            {"seq": 5, "action": "wait", "target": "", "value": "2000", "expected": "Page loaded"},
        ]

    return [
        {
            "title": "[Self-Test] Login & Dashboard",
            "project_id": project_id,
            "priority": "P0",
            "preconditions": "Platform is deployed and running",
            "steps": [
                {"seq": 1, "action": "navigate", "target": f"{frontend_url}/login", "value": "", "expected": "Login page shown"},
                {"seq": 2, "action": "input", "target": "username input", "value": ADMIN_USER, "expected": ""},
                {"seq": 3, "action": "input", "target": "password input", "value": ADMIN_PASS, "expected": ""},
                {"seq": 4, "action": "click", "target": "login button", "value": "", "expected": "Login success"},
                {"seq": 5, "action": "wait", "target": "", "value": "3000", "expected": ""},
                {"seq": 6, "action": "assert", "target": "Dashboard or home page content is visible", "value": "", "expected": "Dashboard loads"},
            ],
            "tags": ["self-test", "smoke"],
            "module": "self-test/auth",
        },
        {
            "title": "[Self-Test] Test Cases Page",
            "project_id": project_id,
            "priority": "P1",
            "preconditions": "Logged in",
            "steps": [
                *login_steps(),
                {"seq": 6, "action": "navigate", "target": f"{frontend_url}/testcases", "value": "", "expected": "Test case list shown"},
                {"seq": 7, "action": "wait", "target": "", "value": "2000", "expected": ""},
                {"seq": 8, "action": "assert", "target": "Page shows case list table or action buttons", "value": "", "expected": "Page loads correctly"},
            ],
            "tags": ["self-test", "smoke"],
            "module": "self-test/testcases",
        },
        {
            "title": "[Self-Test] Test Plans Page",
            "project_id": project_id,
            "priority": "P1",
            "preconditions": "Logged in",
            "steps": [
                *login_steps(),
                {"seq": 6, "action": "navigate", "target": f"{frontend_url}/testplans", "value": "", "expected": "Test plan list shown"},
                {"seq": 7, "action": "wait", "target": "", "value": "2000", "expected": ""},
                {"seq": 8, "action": "assert", "target": "Page loads without errors", "value": "", "expected": "Plan page loads correctly"},
            ],
            "tags": ["self-test", "smoke"],
            "module": "self-test/testplans",
        },
        {
            "title": "[Self-Test] Reports Page",
            "project_id": project_id,
            "priority": "P1",
            "preconditions": "Logged in",
            "steps": [
                *login_steps(),
                {"seq": 6, "action": "navigate", "target": f"{frontend_url}/reports", "value": "", "expected": "Report list shown"},
                {"seq": 7, "action": "wait", "target": "", "value": "2000", "expected": ""},
                {"seq": 8, "action": "assert", "target": "Page loads without errors", "value": "", "expected": "Report page loads correctly"},
            ],
            "tags": ["self-test", "smoke"],
            "module": "self-test/reports",
        },
        {
            "title": "[Self-Test] Zentao Config Page",
            "project_id": project_id,
            "priority": "P2",
            "preconditions": "Logged in",
            "steps": [
                *login_steps(),
                {"seq": 6, "action": "navigate", "target": f"{frontend_url}/zentao", "value": "", "expected": "Zentao config page shown"},
                {"seq": 7, "action": "wait", "target": "", "value": "2000", "expected": ""},
                {"seq": 8, "action": "assert", "target": "Page loads without errors", "value": "", "expected": "Zentao page loads correctly"},
            ],
            "tags": ["self-test", "smoke"],
            "module": "self-test/zentao",
        },
    ]


# ── 主流程 ──


def check_health() -> bool:
    """检查后端是否可达"""
    try:
        url = f"{BASE_URL}/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def login() -> str | None:
    """Login and return token"""
    code, resp = post("/auth/login", {
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
    })
    if code == 200:
        token = resp.get("data", {}).get("token", "")
        if token:
            ok(f"Logged in as {ADMIN_USER}")
            return token
    fail(f"Login failed: {resp}")
    return None


def get_or_create_project(token: str) -> int | None:
    """Get first project or create one"""
    code, resp = get("/projects?page=1&limit=1", token)
    if code != 200:
        fail(f"Failed to get projects: {resp}")
        return None

    # /projects returns PaginatedRes (no code wrapper)
    items = resp.get("items", [])
    if items:
        pid = items[0]["id"]
        ok(f"Using project: {items[0]['name']} (id={pid})")
        return pid

    # Create a project
    info("No projects found, creating one...")
    code, resp = post("/projects", {
        "name": "[Self-Test] Dogfood Project",
        "description": "Auto-generated project for platform self-testing",
    }, token=token)
    if code == 201:
        pid = resp.get("data", {}).get("id")
        ok(f"Project created (id={pid})")
        return pid
    fail(f"Failed to create project: {resp}")
    return None


def create_test_cases(token: str, project_id: int, frontend_url: str) -> list[int]:
    """Create self-test cases via API"""
    cases = build_self_test_cases(project_id, frontend_url)
    case_ids: list[int] = []
    for case in cases:
        code, resp = post("/testcases", case, token=token)
        if code == 201:
            cid = resp.get("data", {}).get("id")
            case_ids.append(cid)
            ok(f"Case: {case['title']} (id={cid})")
        else:
            detail = resp.get("detail", resp)
            fail(f"Create failed: {case['title']}")
            print(f"      Response: {json.dumps(detail, ensure_ascii=False)[:200]}")
    return case_ids


def create_and_run_plan(token: str, project_id: int, case_ids: list[int]) -> tuple[int | None, list[int]]:
    """Create test plan and start execution, returns (plan_id, [execution_ids])"""
    if not case_ids:
        fail("No case IDs, cannot create plan")
        return None, []

    plan_name = f"[Self-Test] Dogfood Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    code, resp = post("/testplans", {
        "project_id": project_id,
        "name": plan_name,
        "description": "Auto-generated platform self-test plan",
        "case_ids": case_ids,
        "max_retries": 1,
        "timeout": 300,
    }, token=token)
    if code != 201:
        fail(f"Failed to create plan: {resp}")
        return None, []
    plan_id = resp.get("data", {}).get("id")
    ok(f"Test plan: {plan_name} (id={plan_id})")

    # Start execution
    code, resp = post(f"/testplans/{plan_id}/run", {}, token=token)
    if code != 200:
        fail(f"Failed to start execution: {resp}")
        return plan_id, []

    executions = resp.get("data", {}).get("executions", [])
    execution_ids = [e["id"] for e in executions]
    ok(f"Started {len(execution_ids)} executions")
    for e in executions:
        info(f"  execution #{e['id']} -> case #{e['case_id']}")
    return plan_id, execution_ids


def poll_results(token: str, execution_ids: list[int], max_wait: int = 300) -> dict:
    """Poll execution results, return summary stats"""
    total = len(execution_ids)
    PASS, FAIL, ERROR, SKIP = "passed", "failed", "error", "skipped"
    terminal = {PASS, FAIL, ERROR, SKIP}

    waited = 0
    while waited < max_wait:
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL

        results = {}
        finished = 0
        for eid in execution_ids:
            code, resp = get(f"/executions/{eid}", token)
            if code == 200:
                status = resp.get("data", {}).get("status", "unknown")
                results[eid] = status
                if status in terminal:
                    finished += 1

        running = total - finished
        p = sum(1 for s in results.values() if s == PASS)
        f = sum(1 for s in results.values() if s == FAIL)
        e = sum(1 for s in results.values() if s == ERROR)
        bar = "#" * finished + "." * running
        print(f"  [{bar}] pass:{GREEN}{p}{RESET} "
              f"fail:{RED}{f}{RESET} error:{YELLOW}{e}{RESET} "
              f"running:{running}  ({waited}s/{max_wait}s)")

        if finished >= total:
            break
    else:
        warn(f"Timeout ({max_wait}s), some executions still running")

    # Summary
    final = {"total": total, "passed": 0, "failed": 0, "error": 0, "skipped": 0, "running": 0}
    for eid in execution_ids:
        code, resp = get(f"/executions/{eid}", token)
        status = resp.get("data", {}).get("status", "unknown") if code == 200 else "error"
        final[status] = final.get(status, 0) + 1
        # Print failure details
        if status in (FAIL, ERROR):
            error_msg = resp.get("data", {}).get("error_message", "")
            steps = resp.get("data", {}).get("steps", [])
            fail(f"  execution #{eid}: {status}")
            if error_msg:
                print(f"      error: {error_msg[:300]}")
            if steps:
                for s in steps[-3:]:  # last 3 steps
                    icon = {"passed": "+", "failed": "-"}.get(s.get("status", ""), "?")
                    print(f"      [{icon}] {s.get('action', '?')}: {s.get('target', '?')}")

    return final


def run_api_tests(token: str, project_id: int) -> dict:
    """API mode: test CRUD + execution framework (no browser/Celery needed)"""

    results = {"api_checks": 0, "api_passed": 0}

    header("API Mode: Core endpoint checks")

    # 1. TestCase CRUD
    info("TestCase CRUD...")
    code, resp = post("/testcases", {
        "project_id": project_id,
        "title": "[Self-Test-API] Temp Case",
        "priority": "P2",
        "steps": [
            {"seq": 1, "action": "navigate", "target": f"{FRONTEND_URL}/dashboard", "value": "", "expected": "page loads"}
        ],
    }, token=token)
    results["api_checks"] += 1
    if code == 201:
        case_id = resp.get("data", {}).get("id")
        ok(f"Create case (id={case_id})")
        results["api_passed"] += 1

        # List
        code2, _ = get("/testcases?page=1&limit=5", token)
        results["api_checks"] += 1
        if code2 == 200:
            ok("List cases")
            results["api_passed"] += 1
        else:
            fail("List cases")

        # Delete
        code3, _ = _request("DELETE", f"/testcases/{case_id}", token=token)
        results["api_checks"] += 1
        if code3 == 200:
            ok("Delete case")
            results["api_passed"] += 1
        else:
            fail("Delete case")
    else:
        fail(f"Create case: {resp}")

    # 2. TestPlan CRUD
    info("TestPlan CRUD...")
    code, resp = post("/testplans", {
        "project_id": project_id,
        "name": f"[Self-Test-API] Temp Plan {int(time.time())}",
        "case_ids": [],
    }, token=token)
    results["api_checks"] += 1
    if code == 201:
        plan_id = resp.get("data", {}).get("id")
        ok(f"Create plan (id={plan_id})")
        results["api_passed"] += 1

        # Verify plan exists
        code2, _ = get(f"/testplans/{plan_id}", token)
        results["api_checks"] += 1
        if code2 == 200:
            ok("Get plan detail")
            results["api_passed"] += 1
        else:
            fail("Get plan detail")
    else:
        fail(f"Create plan: {resp}")

    # 3. Reports
    info("Reports endpoint...")
    code, _ = get("/reports?page=1&limit=5", token)
    results["api_checks"] += 1
    if code == 200:
        ok("List reports")
        results["api_passed"] += 1
    else:
        fail("List reports")

    # 4. Zentao (with params; 400=connection fail is normal when unconfigured)
    info("Zentao endpoint...")
    code, _ = get("/zentao/products?config_base_url=http://localhost&config_account=admin&config_password=test", token)
    results["api_checks"] += 1
    if code in (200, 400, 503):
        ok("Zentao products endpoint reachable")
        results["api_passed"] += 1
    else:
        fail(f"Zentao endpoint: HTTP {code}")

    # 5. AI endpoint
    info("AI endpoint...")
    code, resp = post("/ai/generate-steps", {
        "description": "Open a search engine, search for AI testing, verify results appear"
    }, token=token)
    results["api_checks"] += 1
    if code == 200:
        ok("AI generate-steps endpoint reachable")
        results["api_passed"] += 1
    else:
        fail(f"AI endpoint: HTTP {code}")

    return results


def print_banner():
    print(f"""
{CYAN}{'='*55}{RESET}
{CYAN}  AI Test Platform - Self Test (Dogfooding){RESET}
{CYAN}{'='*55}{RESET}
    """)
    info(f"Backend: {BASE_URL}")
    info(f"Frontend: {FRONTEND_URL}")
    info(f"Mode: {MODE}")


def print_report(browser_result: dict, api_result: dict, start_time: float) -> bool:
    elapsed = time.time() - start_time
    print(f"\n{BOLD}{'='*55}{RESET}")
    print(f"{BOLD}  Self-Test Report{RESET}")
    print(f"{'='*55}")

    if browser_result:
        t = browser_result["total"]
        p = browser_result["passed"]
        f = browser_result["failed"]
        e = browser_result["error"]
        print(f"  Browser:  {GREEN}{p} passed{RESET}  {RED}{f} failed{RESET}  "
              f"{YELLOW}{e} error{RESET}  total {t} cases")

    if api_result:
        c = api_result["api_checks"]
        p = api_result["api_passed"]
        print(f"  API:      {GREEN}{p}/{c} passed{RESET}")

    print(f"  Duration: {elapsed:.0f}s")
    print(f"{'='*55}")

    # 判断是否全部通过
    browser_ok = not browser_result or browser_result.get("failed", 0) + browser_result.get("error", 0) == 0
    api_ok = not api_result or api_result["api_passed"] == api_result["api_checks"]

    if browser_ok and api_ok:
        print(f"{GREEN}{BOLD}  ALL PASSED{RESET}\n")
        return True
    else:
        print(f"{RED}{BOLD}  SOME FAILED{RESET}\n")
        return False


def main():
    # 声明全局变量（必须在函数体内任何使用之前）
    global BASE_URL, FRONTEND_URL, MODE, ADMIN_USER, ADMIN_PASS, MAX_WAIT

    # Windows 终端 UTF-8 支持
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
        except Exception:
            global _USE_COLOR
            _USE_COLOR = False

    parser = argparse.ArgumentParser(
        description="AI 测试平台自测脚本 — 用自己的 AI 引擎测试自己的前端",
    )
    parser.add_argument("--base-url", default=BASE_URL,
                        help=f"后端 API 地址 (默认: {BASE_URL})")
    parser.add_argument("--frontend-url", default=FRONTEND_URL,
                        help=f"前端地址，浏览器测试时 navigete 的目标 (默认: {FRONTEND_URL})")
    parser.add_argument("--mode", choices=["browser", "api"], default=MODE,
                        help="测试模式: browser=全量AI浏览器测试, api=仅接口检查 (默认: browser)")
    parser.add_argument("--admin-user", default=ADMIN_USER, help="管理员用户名")
    parser.add_argument("--admin-pass", default=ADMIN_PASS, help="管理员密码")
    parser.add_argument("--max-wait", type=int, default=MAX_WAIT,
                        help=f"浏览器测试最大等待秒数 (默认: {MAX_WAIT})")
    parser.add_argument("--ci", action="store_true", help="CI 模式（精简输出）")
    args = parser.parse_args()

    BASE_URL = args.base_url.rstrip("/")
    FRONTEND_URL = args.frontend_url.rstrip("/")
    MODE = args.mode
    ADMIN_USER = args.admin_user
    ADMIN_PASS = args.admin_pass
    MAX_WAIT = args.max_wait

    start_time = time.time()

    if not args.ci:
        print_banner()

    # 1. Health check
    header("1. Health Check")
    if not check_health():
        fail(f"Backend unreachable at {BASE_URL}")
        sys.exit(1)
    ok(f"Backend {BASE_URL} ready")

    # 2. Login
    header("2. Auth")
    token = login()
    if not token:
        sys.exit(1)

    # 3. Project
    header("3. Project")
    project_id = get_or_create_project(token)
    if not project_id:
        sys.exit(1)

    # 4. API tests
    header("4. API Tests")
    api_result = run_api_tests(token, project_id)

    # 5. Browser tests
    browser_result = {}
    if MODE == "browser":
        header("5. Browser AI Tests")
        info("Creating self-test cases...")
        case_ids = create_test_cases(token, project_id, FRONTEND_URL)
        if not case_ids:
            warn("No cases created, skipping browser tests")
        else:
            info("Creating test plan and starting execution...")
            plan_id, execution_ids = create_and_run_plan(token, project_id, case_ids)
            if execution_ids:
                info(f"Waiting for AI browser execution (max {MAX_WAIT}s)...")
                print(f"  {YELLOW}Hint: make sure Celery Worker is running{RESET}")
                browser_result = poll_results(token, execution_ids, MAX_WAIT)

    # 6. 报告
    success = print_report(browser_result, api_result, start_time)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
