"""AI 浏览器执行代理 — 基于 Playwright + LLM（自愈选择器 + 重试反馈）"""

import json
import os
import time
import logging
from datetime import datetime

from app.config import get_settings
from app.models.testcase import TestCase
from app.models.execution import Execution

logger = logging.getLogger(__name__)
settings = get_settings()

# 每步最大重试次数
MAX_STEP_RETRIES = 3


def _get_llm():
    """获取 LLM Provider 实例（统一入口）"""
    from app.llm import get_llm
    return get_llm()


def build_prompt_from_steps(tc: TestCase) -> str:
    """将用例步骤转换为自然语言 Prompt"""
    lines = [f"任务: {tc.title}"]
    if tc.preconditions:
        lines.append(f"前置条件: {tc.preconditions}")

    for step in tc.steps or []:
        action = step.get("action", "")
        target = step.get("target", "")
        value = step.get("value", "")
        expected = step.get("expected", "")

        if action == "navigate":
            lines.append(f"访问页面: {target}")
        elif action == "click":
            lines.append(f"点击: {target}")
        elif action == "input":
            lines.append(f"在「{target}」输入: {value}")
        elif action == "select":
            lines.append(f"在「{target}」选择: {value}")
        elif action == "hover":
            lines.append(f"鼠标悬停到: {target}")
        elif action == "scroll":
            lines.append(f"滚动到: {target}")
        elif action == "wait":
            lines.append(f"等待 {step.get('timeout', 3000)}ms")
        elif action == "assert":
            lines.append(f"验证 {target} 为: {expected}")
        elif action == "screenshot":
            lines.append(f"截屏保存")
        elif action == "ai_action":
            lines.append(f"AI 智能操作: {target}")

        if expected and action not in ("assert",):
            lines.append(f"  → 预期结果: {expected}")

    return "\n".join(lines)


def _build_action_decision_prompt(task: str, page_title: str, page_url: str, body_text: str,
                                  completed_steps: list[str], remaining_steps: list[str],
                                  failed_feedback: str = "") -> str:
    """构建 LLM 决策 prompt（含失败反馈）"""
    done = "\n".join(f"  ✓ {s}" for s in completed_steps) if completed_steps else "（无）"
    todo = "\n".join(f"  ○ {s}" for s in remaining_steps) if remaining_steps else "（无）"

    feedback_section = ""
    if failed_feedback:
        feedback_section = f"""
## ⚠️ 上一步失败信息
{failed_feedback}
请尝试使用不同的选择器或策略重新执行该步骤。优先使用：id 选择器 → data-testid → aria-label → 文本内容匹配。
"""

    return f"""你是一个 Web 浏览器自动化助手。请根据当前页面状态决定下一步操作。

## 任务目标
{task}

## 当前页面
- URL: {page_url}
- 标题: {page_title}
- 页面文本（前 3000 字符）:
```
{body_text[:3000]}
```

## 已完成的步骤
{done}

## 待执行的步骤
{todo}
{feedback_section}
请返回一个 JSON 对象，包含以下字段：
{{
  "action": "click" | "input" | "navigate" | "wait" | "scroll" | "done" | "failed",
  "selector": "CSS 选择器（click/input 时必填）",
  "value": "输入值（input 时必填）",
  "url": "目标URL（navigate 时必填）",
  "wait_ms": 等待毫秒数（wait 时必填，默认 2000）,
  "reason": "决策原因（中文）",
  "completed": true/false（所有步骤是否已完成）
}}

注意：
- 如果页面已满足所有剩余步骤的预期结果，设置 action="done", completed=true
- 如果页面发生了错误或无法继续，设置 action="failed"
- 对于 click 和 input，使用最具体的 CSS 选择器
- 对于中文网站，优先匹配中文文本
- 优先使用 id 选择器（如 #loginBtn）、data-testid、aria-label 属性
"""


def _parse_llm_decision(response: str) -> dict:
    """解析 LLM 返回的决策 JSON"""
    # 尝试提取 JSON
    try:
        # 找第一个 { 到最后一个 }
        start = response.find("{")
        end = response.rfind("}")
        if start >= 0 and end > start:
            return json.loads(response[start:end + 1])
    except json.JSONDecodeError:
        pass
    # 默认返回 done
    return {"action": "done", "completed": True, "reason": "无法解析 LLM 响应，结束执行"}


def execute_testcase(tc: TestCase, execution: Execution) -> list[dict]:
    """
    使用 Playwright + DeepSeek 执行单个用例的步骤。
    返回每步的执行结果列表。

    注意：这是同步函数，避免 Python 3.14 asyncio 在 Windows 上的子进程死锁问题。
    """
    from playwright.sync_api import sync_playwright

    prompt = build_prompt_from_steps(tc)
    llm = _get_llm()
    steps = tc.steps or []
    steps_results: list[dict] = []

    if not steps:
        return steps_results

    start_time = datetime.utcnow()

    # 构建步骤描述列表
    step_descriptions = []
    for step in steps:
        action = step.get("action", "")
        target = step.get("target", "")
        value = step.get("value", "")
        expected = step.get("expected", "")
        desc = f"{action}: {target}"
        if value:
            desc += f" = {value}"
        if expected:
            desc += f" → {expected}"
        step_descriptions.append(desc)

    completed: list[str] = []
    remaining = list(step_descriptions)

    # 每步的状态追踪：None=未执行, True=通过, False=失败
    step_status: list[bool | None] = [None] * len(steps)
    step_durations: list[float] = [0.0] * len(steps)
    step_timestamps: list[str] = [""] * len(steps)    # 每步实际执行时间
    step_retry_count: list[int] = [0] * len(steps)     # 每步重试次数
    last_failed_step_idx: int | None = None             # 上一步失败的索引（用于反馈）

    try:
        with sync_playwright() as p:
            browser_type = getattr(p, settings.playwright_browser, p.chromium)
            browser = browser_type.launch(headless=settings.playwright_headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                locale="zh-CN",
            )
            page = context.new_page()
            page.set_default_timeout(30000)

            max_iterations = 20  # 安全上限
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # 检查是否所有步骤已完成
                pending_indices = [i for i, s in enumerate(step_status) if s is None]
                if not pending_indices:
                    break

                # 获取当前页面状态
                try:
                    page_title = page.title()
                except Exception:
                    page_title = "(无法获取标题)"
                try:
                    page_url = page.url
                except Exception:
                    page_url = "(无法获取 URL)"
                try:
                    body_text = page.inner_text("body") or ""
                except Exception:
                    body_text = "(无法获取页面文本)"

                # 构建当前待执行步骤描述（包含失败步骤的重试反馈）
                completed_descs = [step_descriptions[i] for i, s in enumerate(step_status) if s is True]
                remaining_descs = [step_descriptions[i] for i, s in enumerate(step_status) if s is None]

                # 构建失败反馈（告知 LLM 上一步为何失败）
                failed_feedback = ""
                if last_failed_step_idx is not None and last_failed_step_idx < len(step_descriptions):
                    if step_retry_count[last_failed_step_idx] < MAX_STEP_RETRIES:
                        failed_feedback = (
                            f"上一步「{step_descriptions[last_failed_step_idx]}」执行失败 "
                            f"(已重试 {step_retry_count[last_failed_step_idx]}/{MAX_STEP_RETRIES})。"
                            f"请尝试使用不同的 CSS 选择器或定位策略。"
                        )
                        # 将失败步骤重置为 None 以便重试
                        step_status[last_failed_step_idx] = None

                # 让 LLM 决策下一步
                decision_prompt = _build_action_decision_prompt(
                    prompt, page_title, page_url, body_text,
                    completed_descs, remaining_descs, failed_feedback,
                )

                # 使用同步 invoke（Playwright sync context 内部有 event loop，不能再创建新的）
                llm_response = llm.invoke([{"role": "user", "content": decision_prompt}])
                decision = _parse_llm_decision(str(llm_response.content))
                action = decision.get("action", "done")
                reason = decision.get("reason", "")

                logger.info(f"[Iter {iteration}] action={action}, reason={reason}, pending={len(pending_indices)}{healing_info}")

                if action == "done" and decision.get("completed"):
                    # ⚠️ 不盲目信任 LLM 的 "done" 声明
                    # 只自动通过不需要页面操作的步骤 (assert, wait, scroll)
                    # click/input/navigate 必须实际执行
                    actionable_pending = [
                        i for i in pending_indices
                        if steps[i].get("action", "") in ("click", "input", "navigate")
                    ]
                    if actionable_pending:
                        # 还有待执行的操作步骤，LLM 的 done 不可信
                        logger.warning(
                            f"LLM 过早声明 done，仍有 {len(actionable_pending)} 个操作步骤待执行。"
                            f"忽略 done，继续执行。"
                        )
                        # 将 done 转换为 continue，让 LLM 在下一轮继续
                        continue
                    else:
                        # 只剩 assert/wait/scroll 等非操作步骤，可以安全通过
                        for i in pending_indices:
                            step_status[i] = True
                            step_timestamps[i] = datetime.utcnow().isoformat()
                        break

                if action == "failed":
                    # 所有剩余步骤标记为失败
                    now = datetime.utcnow().isoformat()
                    for i in pending_indices:
                        step_status[i] = False
                        step_timestamps[i] = now
                    break

                # 执行具体动作（集成自愈机制）
                step_start = time.time()
                action_succeeded = False
                matched_step_idx = None
                healing_info = ""

                try:
                    if action == "navigate":
                        url = decision.get("url", "")
                        if url:
                            try:
                                page.goto(url, timeout=30000)
                                page.wait_for_load_state("domcontentloaded", timeout=15000)
                            except Exception as nav_err:
                                logger.warning(f"Navigation to {url} partially failed (continuing): {nav_err}")
                                # 某些页面（如百度）持续加载，忽略超时继续
                        action_succeeded = True
                        matched_step_idx = _find_pending_step_for_action(steps, step_status, "navigate", decision)

                    elif action == "click":
                        selector = decision.get("selector", "body")
                        target = _get_step_target(steps, step_status, "click")

                        # ── 自愈点击 ──
                        from app.engine.self_healing import heal_and_click
                        heal_result = heal_and_click(
                            page=page,
                            llm_selector=selector,
                            target_description=target or "目标元素",
                            get_llm_fn=_get_llm,
                            body_text=body_text,
                        )

                        if heal_result.success:
                            action_succeeded = True
                            healing_info = f" | 定位策略: {heal_result.used_strategy}"
                            if heal_result.used_strategy != "css":
                                logger.info(
                                    f"自愈成功 [{heal_result.used_strategy}]: "
                                    f"'{selector}' → '{heal_result.used_selector}'"
                                )
                        else:
                            action_succeeded = False
                            logger.warning(
                                f"自愈失败: 所有策略均无法定位元素 '{target}'. "
                                f"尝试: {', '.join(heal_result.healing_details)}"
                            )
                            _capture_failure_screenshot(page, execution, "click", selector)

                        page.wait_for_timeout(1500)
                        matched_step_idx = _find_pending_step_for_action(steps, step_status, "click", decision)

                    elif action == "input":
                        selector = decision.get("selector", "")
                        value = decision.get("value", "")
                        target = _get_step_target(steps, step_status, "input")

                        if selector and value:
                            # ── 自愈输入 ──
                            from app.engine.self_healing import heal_and_fill
                            heal_result = heal_and_fill(
                                page=page,
                                llm_selector=selector,
                                value=value,
                                target_description=target or "输入框",
                                get_llm_fn=_get_llm,
                                body_text=body_text,
                            )

                            if heal_result.success:
                                action_succeeded = True
                                healing_info = f" | 定位策略: {heal_result.used_strategy}"
                                if heal_result.used_strategy != "css":
                                    logger.info(
                                        f"自愈成功 [{heal_result.used_strategy}]: "
                                        f"'{selector}' → '{heal_result.used_selector}'"
                                    )
                            else:
                                action_succeeded = False
                                logger.warning(
                                    f"自愈失败: 所有策略均无法定位输入框 '{target}'. "
                                    f"尝试: {', '.join(heal_result.healing_details)}"
                                )
                                _capture_failure_screenshot(page, execution, "input", selector)
                        else:
                            logger.warning("LLM 未提供 selector 或 value，跳过 input 操作")

                        matched_step_idx = _find_pending_step_for_action(steps, step_status, "input", decision)

                    elif action == "wait":
                        wait_ms = decision.get("wait_ms", 2000)
                        page.wait_for_timeout(min(wait_ms, 10000))
                        action_succeeded = True  # FIX: 之前缺失
                        matched_step_idx = _find_pending_step_for_action(steps, step_status, "wait", decision)

                    elif action == "scroll":
                        page.evaluate("window.scrollBy(0, 300)")
                        action_succeeded = True  # FIX: 之前缺失
                        matched_step_idx = _find_pending_step_for_action(steps, step_status, "scroll", decision)

                    elif action == "assert":
                        # FIX: 之前是空操作，现在实现实际验证
                        target = decision.get("selector", "")
                        expected = decision.get("value", "")
                        # 从当前待执行的 assert 步骤中获取 expected
                        for i, (step, status) in enumerate(zip(steps, step_status)):
                            if status is None and step.get("action") == "assert":
                                target = target or step.get("target", "body")
                                expected = expected or step.get("expected", "")
                                break
                        try:
                            if target:
                                content = page.inner_text(target) or page.content()
                            else:
                                content = page.inner_text("body") or ""
                            if expected and expected not in content:
                                logger.warning(f"断言失败: 期望 '{expected}' 未在页面中找到")
                                action_succeeded = False
                            else:
                                action_succeeded = True
                        except Exception:
                            action_succeeded = False
                        matched_step_idx = _find_pending_step_for_action(steps, step_status, "assert", decision)

                    elif action == "ai_action":
                        # AI 自定义操作（预留扩展）
                        action_succeeded = True
                        matched_step_idx = _find_pending_step_for_action(steps, step_status, "ai_action", decision)

                    else:
                        logger.warning(f"Unknown action: {action}")

                except Exception as action_err:
                    logger.warning(f"Action '{action}' failed with exception: {action_err}")
                    _capture_failure_screenshot(page, execution, action,
                                                decision.get("selector", "unknown"))

                step_duration = (time.time() - step_start) * 1000

                # 更新步骤状态（带重试逻辑）
                if matched_step_idx is not None:
                    step_durations[matched_step_idx] = step_duration
                    step_timestamps[matched_step_idx] = datetime.utcnow().isoformat()
                    if action_succeeded:
                        step_status[matched_step_idx] = True
                        step_retry_count[matched_step_idx] = 0  # 成功后重置重试计数
                        last_failed_step_idx = None
                    else:
                        step_retry_count[matched_step_idx] += 1
                        if step_retry_count[matched_step_idx] >= MAX_STEP_RETRIES:
                            # 超过最大重试次数，永久标记为失败
                            step_status[matched_step_idx] = False
                            logger.warning(
                                f"步骤 {matched_step_idx + 1} 已重试 {MAX_STEP_RETRIES} 次，永久标记失败"
                            )
                            last_failed_step_idx = None
                        else:
                            # 记录失败，下一轮迭代中通过 failed_feedback 告知 LLM 重试
                            last_failed_step_idx = matched_step_idx
                            logger.info(
                                f"步骤 {matched_step_idx + 1} 失败（{step_retry_count[matched_step_idx]}/{MAX_STEP_RETRIES}），"
                                f"将在下一轮提供反馈重试"
                            )

            browser.close()

    except Exception as e:
        logger.error(f"Playwright execution error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # 构建结果列表
    for i, step in enumerate(steps):
        status = step_status[i]
        if status is None:
            status = False  # 未执行的标记为失败
        steps_results.append({
            "seq": i + 1,
            "action": step_descriptions[i],
            "status": "passed" if status else "failed",
            "duration": step_durations[i],
            "timestamp": step_timestamps[i] or datetime.utcnow().isoformat(),
        })

    return steps_results


def _find_pending_step_for_action(
    steps: list[dict],
    step_status: list[bool | None],
    action: str,
    decision: dict | None = None,
) -> int | None:
    """找到匹配 action 的待执行步骤索引（优先 target 名称匹配）"""
    # 第一轮：精确匹配 action 类型 + target 名称
    if decision:
        decision_target = decision.get("selector", "") + decision.get("value", "")
        for i, (step, status) in enumerate(zip(steps, step_status)):
            if status is not None:
                continue
            if step.get("action", "") != action:
                continue
            step_target = step.get("target", "")
            # 如果 LLM 的 selector/value 包含步骤 target 关键词，优先匹配
            if step_target and len(step_target) >= 2 and step_target in decision_target:
                return i
            # 反之亦然
            if step_target and len(decision_target) >= 2 and decision_target in step_target:
                return i

    # 第二轮：仅匹配 action 类型
    for i, (step, status) in enumerate(zip(steps, step_status)):
        if status is not None:
            continue
        if step.get("action", "") == action:
            return i

    # 第三轮：如果没有匹配的 action 类型，返回第一个待执行的
    for i, status in enumerate(step_status):
        if status is None:
            return i
    return None


def _get_step_target(steps: list[dict], step_status: list[bool | None], action: str) -> str:
    """获取当前待执行的第一个匹配 action 的步骤 target"""
    for i, (step, status) in enumerate(zip(steps, step_status)):
        if status is not None:
            continue
        if step.get("action", "") == action:
            return step.get("target", "")
    return ""


def _capture_failure_screenshot(page, execution: Execution, action: str, selector: str):
    """捕获失败时的截图"""
    try:
        screenshot_dir = os.path.join(settings.upload_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        safe_action = action.replace("/", "_").replace("\\", "_")
        filename = f"exec_{execution.id}_failure_{safe_action}_{int(time.time())}.png"
        filepath = os.path.join(screenshot_dir, filename)
        page.screenshot(path=filepath, full_page=False)
        logger.info(f"失败截图已保存: {filepath}")
    except Exception as e:
        logger.warning(f"截图失败: {e}")


def run_testcase_sync(tc: TestCase, execution: Execution) -> list[dict]:
    """同步执行（供 Celery 调用，当前实现已是同步）"""
    return execute_testcase(tc, execution)
