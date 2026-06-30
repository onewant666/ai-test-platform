"""自然语言 → 测试步骤 解析器（基于 LLM）"""

import json
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """你是一个专业的测试工程师。请将用户的自然语言描述转换为结构化的测试步骤 JSON 数组。

每个步骤包含以下字段:
- seq: 步骤序号 (从 1 开始)
- action: 操作类型，可选值: navigate, click, input, select, hover, scroll, wait, assert, screenshot, ai_action
- target: 目标元素描述
- value: 输入值（仅 input/select 需要）
- expected: 预期结果

请严格按 JSON 数组格式输出，不要包含额外说明。

示例输入: "打开百度首页，搜索AI测试"
示例输出:
[
  {"seq": 1, "action": "navigate", "target": "https://www.baidu.com", "expected": "页面显示百度搜索框"},
  {"seq": 2, "action": "input", "target": "搜索输入框", "value": "AI测试", "expected": "输入成功"},
  {"seq": 3, "action": "click", "target": "百度一下按钮", "expected": "显示搜索结果列表"}
]"""


async def parse_description_to_steps(description: str) -> list[dict]:
    """将自然语言描述解析为测试步骤"""
    try:
        from app.llm import get_llm

        llm = get_llm()

        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ])

        # 提取 JSON
        content = str(response.content).strip()
        # 移除可能的 markdown 代码块标记
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        steps = json.loads(content)
        return steps

    except (ImportError, Exception) as e:
        # LLM 不可用时的降级方案
        return [
            {"seq": 1, "action": "navigate", "target": "目标页面", "expected": "页面加载成功"},
            {"seq": 2, "action": "click", "target": "目标元素", "expected": "操作成功"},
            {"seq": 3, "action": "assert", "target": "结果区域", "expected": "显示预期内容"},
        ]
