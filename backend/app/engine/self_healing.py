"""自愈选择器策略 — 多级元素定位回退

当 LLM 提供的 CSS 选择器无法定位元素时，依次尝试:
  1. CSS 选择器（LLM 原始输出）
  2. 文本选择器（Playwright text=、get_by_text）
  3. 角色选择器（get_by_role: button, link, textbox 等）
  4. 模糊属性匹配（aria-label, placeholder, title, alt）
  5. LLM 重新分析（发送当前页面 HTML 请求新选择器）
  6. XPath 兜底（contains(text(), ...)、contains(@placeholder, ...)）

用法:
    from app.engine.self_healing import HealResult, heal_and_click, heal_and_fill

    result = heal_and_click(page, selector, target_description, get_llm, body_text)
    if result.success:
        logger.info(f"自愈成功: {result.used_strategy} → {result.used_selector}")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class HealResult:
    """自愈操作结果"""
    success: bool
    used_strategy: str = ""       # "css" | "text" | "role" | "fuzzy" | "llm_reanalysis" | "xpath" | "none"
    used_selector: str = ""
    healing_details: list[str] = field(default_factory=list)  # 尝试过的策略日志


# ──────────────────────────────────────────────
# 公共入口
# ──────────────────────────────────────────────

def heal_and_click(
    page,
    llm_selector: str,
    target_description: str,
    get_llm_fn: Callable,
    body_text: str = "",
) -> HealResult:
    """对 click 操作执行多级选择器自愈"""
    strategies: list[tuple[str, Callable[[], str | None]]] = [
        ("css",            lambda: _try_css(page, llm_selector)),
        ("text",           lambda: _try_text_selectors(page, target_description)),
        ("role",           lambda: _try_role_selectors(page, target_description)),
        ("fuzzy",          lambda: _try_fuzzy_attributes(page, target_description)),
        ("llm_reanalysis", lambda: _try_llm_reanalysis_click(page, llm_selector, target_description, get_llm_fn, body_text)),
        ("xpath",          lambda: _try_xpath(page, target_description)),
    ]

    details: list[str] = []
    for strategy_name, strategy_fn in strategies:
        try:
            result = strategy_fn()
            if result:
                details.append(f"{strategy_name}: ✓ → {result}")
                return HealResult(success=True, used_strategy=strategy_name,
                                  used_selector=result, healing_details=details)
            else:
                details.append(f"{strategy_name}: ✗")
        except Exception as e:
            details.append(f"{strategy_name}: ✗ ({e})")

    return HealResult(success=False, used_strategy="none",
                      used_selector=llm_selector, healing_details=details)


def heal_and_fill(
    page,
    llm_selector: str,
    value: str,
    target_description: str,
    get_llm_fn: Callable,
    body_text: str = "",
) -> HealResult:
    """对 input/fill 操作执行多级选择器自愈"""
    strategies: list[tuple[str, Callable[[], str | None]]] = [
        ("css",            lambda: _try_fill_css(page, llm_selector, value)),
        ("text",           lambda: _try_fill_text(page, target_description, value)),
        ("role",           lambda: _try_fill_role(page, target_description, value)),
        ("fuzzy",          lambda: _try_fill_fuzzy(page, target_description, value)),
        ("llm_reanalysis", lambda: _try_llm_reanalysis_fill(page, llm_selector, target_description, value, get_llm_fn, body_text)),
        ("xpath",          lambda: _try_fill_xpath(page, target_description, value)),
    ]

    details: list[str] = []
    for strategy_name, strategy_fn in strategies:
        try:
            result = strategy_fn()
            if result:
                details.append(f"{strategy_name}: ✓ → {result}")
                return HealResult(success=True, used_strategy=strategy_name,
                                  used_selector=result, healing_details=details)
            else:
                details.append(f"{strategy_name}: ✗")
        except Exception as e:
            details.append(f"{strategy_name}: ✗ ({e})")

    return HealResult(success=False, used_strategy="none",
                      used_selector=llm_selector, healing_details=details)


# ──────────────────────────────────────────────
# Level 1: CSS 选择器
# ──────────────────────────────────────────────

def _try_css(page, selector: str) -> str | None:
    """Level 1: 尝试 LLM 提供的 CSS 选择器"""
    try:
        page.wait_for_selector(selector, timeout=5000)
        page.click(selector, timeout=5000)
        return selector
    except Exception:
        return None


def _try_fill_css(page, selector: str, value: str) -> str | None:
    """Level 1 fill: 尝试 CSS 选择器并填入值"""
    try:
        page.wait_for_selector(selector, timeout=5000)
        page.fill(selector, value, timeout=5000)
        return selector
    except Exception:
        return None


# ──────────────────────────────────────────────
# Level 2: 文本选择器
# ──────────────────────────────────────────────

def _try_text_selectors(page, target: str) -> str | None:
    """Level 2: 尝试 Playwright 文本定位"""
    # 2a: get_by_text (精确 + 模糊)
    try:
        locator = page.get_by_text(target, exact=False)
        if locator.count() > 0:
            locator.first.click(timeout=5000)
            return f"get_by_text({target})"
    except Exception:
        pass

    # 2b: text= 选择器
    try:
        page.click(f"text={target}", timeout=5000)
        return f"text={target}"
    except Exception:
        pass

    # 2c: 部分文本匹配（截取前 20 个字符的关键词）
    keywords = target.split()
    if len(keywords) > 1:
        for kw in keywords:
            if len(kw) >= 2:
                try:
                    page.click(f"text={kw}", timeout=3000)
                    return f"text={kw}"
                except Exception:
                    continue

    return None


def _try_fill_text(page, target: str, value: str) -> str | None:
    """Level 2 fill: 文本定位后填入"""
    try:
        locator = page.get_by_text(target, exact=False)
        if locator.count() > 0:
            # 文本定位到的是标签，需要找到相邻的 input
            # 尝试通过 label 关联或父元素查找
            input_locator = page.get_by_label(target)
            if input_locator.count() > 0:
                input_locator.fill(value, timeout=5000)
                return f"get_by_label({target})"
    except Exception:
        pass

    try:
        page.fill(f"text={target}", value, timeout=5000)
        return f"text={target}"
    except Exception:
        pass

    return None


# ──────────────────────────────────────────────
# Level 3: 角色选择器
# ──────────────────────────────────────────────

def _try_role_selectors(page, target: str) -> str | None:
    """Level 3: 尝试 ARIA 角色定位"""
    roles = ["button", "link", "textbox", "combobox", "checkbox", "radio", "tab", "menuitem"]
    for role in roles:
        try:
            locator = page.get_by_role(role, name=target)
            if locator.count() > 0:
                locator.first.click(timeout=5000)
                return f"role={role}[name={target}]"
        except Exception:
            continue

    # 宽松匹配：子串
    for role in roles:
        try:
            locator = page.get_by_role(role)
            for i in range(min(locator.count(), 50)):
                el = locator.nth(i)
                text_content = el.text_content() or ""
                if target.lower() in text_content.lower():
                    el.click(timeout=5000)
                    return f"role={role}[contains(text(), {target})]"
        except Exception:
            continue

    return None


def _try_fill_role(page, target: str, value: str) -> str | None:
    """Level 3 fill: 角色定位后填入"""
    try:
        locator = page.get_by_role("textbox", name=target)
        if locator.count() > 0:
            locator.first.fill(value, timeout=5000)
            return f"role=textbox[name={target}]"
    except Exception:
        pass

    # 通过 label 关联找 input
    try:
        locator = page.get_by_label(target)
        if locator.count() > 0:
            locator.first.fill(value, timeout=5000)
            return f"get_by_label({target})"
    except Exception:
        pass

    return None


# ──────────────────────────────────────────────
# Level 4: 模糊属性匹配
# ──────────────────────────────────────────────

def _try_fuzzy_attributes(page, target: str) -> str | None:
    """Level 4: 通过 aria-label / placeholder / title / alt 定位"""
    attributes = [
        f"[aria-label*=\"{target}\"]",
        f"[placeholder*=\"{target}\"]",
        f"[title*=\"{target}\"]",
        f"[alt*=\"{target}\"]",
    ]
    for attr_selector in attributes:
        try:
            page.wait_for_selector(attr_selector, timeout=3000)
            page.click(attr_selector, timeout=5000)
            return attr_selector
        except Exception:
            continue

    # 分拆关键词逐个尝试
    keywords = target.split()
    if len(keywords) > 1:
        for kw in keywords:
            if len(kw) >= 2:
                for attr_tmpl in ["[aria-label*=\"{}\"]", "[placeholder*=\"{}\"]"]:
                    attr_selector = attr_tmpl.format(kw)
                    try:
                        page.wait_for_selector(attr_selector, timeout=2000)
                        page.click(attr_selector, timeout=3000)
                        return attr_selector
                    except Exception:
                        continue

    return None


def _try_fill_fuzzy(page, target: str, value: str) -> str | None:
    """Level 4 fill: 模糊属性匹配后填入"""
    attributes = [
        f"[aria-label*=\"{target}\"]",
        f"[placeholder*=\"{target}\"]",
        f"[title*=\"{target}\"]",
    ]
    for attr_selector in attributes:
        try:
            page.wait_for_selector(attr_selector, timeout=3000)
            page.fill(attr_selector, value, timeout=5000)
            return attr_selector
        except Exception:
            continue
    return None


# ──────────────────────────────────────────────
# Level 5: LLM 重新分析
# ──────────────────────────────────────────────

def _try_llm_reanalysis_click(
    page, original_selector: str, target: str,
    get_llm_fn: Callable, body_text: str,
) -> str | None:
    """Level 5: 请求 LLM 根据当前页面 HTML 给出新的选择器"""
    try:
        llm = get_llm_fn()
        html_snippet = page.evaluate("""() => {
            const body = document.body;
            if (!body) return '';
            // 只取交互元素的 HTML，减少 token
            const interactive = body.querySelectorAll(
                'a, button, input, select, textarea, [role="button"], [onclick], [data-testid]'
            );
            const parts = [];
            interactive.forEach(el => {
                const tag = el.tagName.toLowerCase();
                const text = (el.textContent || '').trim().substring(0, 100);
                const id = el.id ? ` id="${el.id}"` : '';
                const cls = el.className && typeof el.className === 'string' ? ` class="${el.className.substring(0, 80)}"` : '';
                const aria = el.getAttribute('aria-label') ? ` aria-label="${el.getAttribute('aria-label')}"` : '';
                const placeholder = el.getAttribute('placeholder') ? ` placeholder="${el.getAttribute('placeholder')}"` : '';
                parts.push(`<${tag}${id}${cls}${aria}${placeholder}>${text}</${tag}>`);
                if (parts.length >= 80) return;  // 限制元素数量
            });
            return parts.join('\\n');
        }""")

        # 防止 prompt 过长
        html_snippet = html_snippet[:6000] if html_snippet else ""

        prompt = f"""The CSS selector "{original_selector}" failed for target "{target}".

Current page interactive elements (truncated HTML):
```html
{html_snippet}
```

Page visible text:
```
{body_text[:1500]}
```

Suggest ONE alternative CSS selector to locate the element matching "{target}".
Consider: id, data-testid, class, aria-label, or a combination.
Return ONLY a JSON object with a single "selector" field. Example: {{"selector": "#login-btn"}}
"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        content = response.content

        # 解析 JSON
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(content[start:end + 1])
            new_selector = data.get("selector", "").strip()
            if new_selector:
                page.wait_for_selector(new_selector, timeout=5000)
                page.click(new_selector, timeout=5000)
                return new_selector
    except Exception as e:
        logger.warning(f"LLM reanalysis click failed: {e}")

    return None


def _try_llm_reanalysis_fill(
    page, original_selector: str, target: str, value: str,
    get_llm_fn: Callable, body_text: str,
) -> str | None:
    """Level 5: LLM 重新分析 fill 选择器"""
    try:
        llm = get_llm_fn()
        html_snippet = page.evaluate("""() => {
            const inputs = document.body ? document.body.querySelectorAll(
                'input, textarea, select, [contenteditable="true"]'
            ) : [];
            const parts = [];
            inputs.forEach(el => {
                const tag = el.tagName.toLowerCase();
                const id = el.id ? ` id="${el.id}"` : '';
                const cls = el.className && typeof el.className === 'string' ? ` class="${el.className.substring(0, 80)}"` : '';
                const name = el.getAttribute('name') ? ` name="${el.getAttribute('name')}"` : '';
                const placeholder = el.getAttribute('placeholder') ? ` placeholder="${el.getAttribute('placeholder')}"` : '';
                const aria = el.getAttribute('aria-label') ? ` aria-label="${el.getAttribute('aria-label')}"` : '';
                parts.push(`<${tag}${id}${cls}${name}${placeholder}${aria}/>`);
                if (parts.length >= 60) return;
            });
            return parts.join('\\n');
        }""")

        html_snippet = html_snippet[:5000] if html_snippet else ""

        prompt = f"""The CSS selector "{original_selector}" failed for input target "{target}".

Input elements on page:
```html
{html_snippet}
```

Page visible text:
```
{body_text[:1500]}
```

Suggest ONE alternative CSS selector for the input field matching "{target}".
Consider: id, name, placeholder, aria-label, or a combination.
Return ONLY a JSON object: {{"selector": "..."}}
"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        content = response.content

        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(content[start:end + 1])
            new_selector = data.get("selector", "").strip()
            if new_selector:
                page.wait_for_selector(new_selector, timeout=5000)
                page.fill(new_selector, value, timeout=5000)
                return new_selector
    except Exception as e:
        logger.warning(f"LLM reanalysis fill failed: {e}")

    return None


# ──────────────────────────────────────────────
# Level 6: XPath 兜底
# ──────────────────────────────────────────────

def _try_xpath(page, target: str) -> str | None:
    """Level 6: XPath 选择器兜底"""
    xpath_expressions = [
        f"//*[contains(text(), '{target}')]",
        f"//button[contains(text(), '{target}')]",
        f"//a[contains(text(), '{target}')]",
        f"//*[contains(@aria-label, '{target}')]",
        f"//*[contains(@placeholder, '{target}')]",
        f"//*[contains(@title, '{target}')]",
        f"//input[@placeholder='{target}']",
    ]
    for xpath in xpath_expressions:
        try:
            locator = page.locator(f"xpath={xpath}")
            if locator.count() > 0:
                locator.first.click(timeout=5000)
                return f"xpath={xpath}"
        except Exception:
            continue

    # 分拆关键词
    for kw in target.split():
        if len(kw) >= 3:
            for tmpl in [
                "//*[contains(text(), '{}')]",
                "//button[contains(text(), '{}')]",
                "//a[contains(text(), '{}')]",
            ]:
                try:
                    xpath = tmpl.format(kw)
                    locator = page.locator(f"xpath={xpath}")
                    if locator.count() > 0:
                        locator.first.click(timeout=3000)
                        return f"xpath={xpath}"
                except Exception:
                    continue

    return None


def _try_fill_xpath(page, target: str, value: str) -> str | None:
    """Level 6 fill: XPath 兜底"""
    xpath_expressions = [
        f"//input[contains(@placeholder, '{target}')]",
        f"//textarea[contains(@placeholder, '{target}')]",
        f"//*[contains(@aria-label, '{target}')]",
        f"//input[@name='{target}']",
        f"//input[@id='{target}']",
    ]
    for xpath in xpath_expressions:
        try:
            locator = page.locator(f"xpath={xpath}")
            if locator.count() > 0:
                locator.first.fill(value, timeout=5000)
                return f"xpath={xpath}"
        except Exception:
            continue

    # 分拆关键词
    for kw in target.split():
        if len(kw) >= 3:
            for tmpl in [
                "//input[contains(@placeholder, '{}')]",
                "//*[contains(@aria-label, '{}')]",
            ]:
                try:
                    xpath = tmpl.format(kw)
                    locator = page.locator(f"xpath={xpath}")
                    if locator.count() > 0:
                        locator.first.fill(value, timeout=3000)
                        return f"xpath={xpath}"
                except Exception:
                    continue

    return None
