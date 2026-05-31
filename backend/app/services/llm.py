import json
import logging
import random
import requests
from openai import OpenAI
from .llm_config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    ZHIPU_API_KEY, ZHIPU_BASE_URL, ZHIPU_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL, TIMEOUT,
)

logger = logging.getLogger(__name__)

CATEGORY_ICONS = {
    "security": "\U0001f512",
    "performance": "\u26a1",
    "boundary": "\U0001f50d",
    "logic": "\U0001f9e9",
    "style": "\U0001f4dd",
    "observability": "\U0001f4ca",
}

PROMPT_TEMPLATE = """请用中文分析以下代码变更，返回 JSON 格式（不要有其他文字）：

{context_str}

代码变更：
{diff}

要求：
1. 返回 3 条风险（risks）
2. 返回 3 条建议（suggestions）
3. 每条风险包含：text, confidence(0-100), category, severity, reasoning
4. 每条建议包含：text, confidence(0-100), category

返回格式：
{{
    "summary": "一句话总结变更内容（中文）",
    "risks": [
        {{"text": "风险描述", "confidence": 85, "category": "security", "severity": "high", "reasoning": "判断依据"}},
        {{"text": "风险描述", "confidence": 70, "category": "performance", "severity": "medium", "reasoning": "判断依据"}},
        {{"text": "风险描述", "confidence": 55, "category": "boundary", "severity": "low", "reasoning": "判断依据"}}
    ],
    "suggestions": [
        {{"text": "建议描述", "confidence": 90, "category": "security"}},
        {{"text": "建议描述", "confidence": 80, "category": "performance"}},
        {{"text": "建议描述", "confidence": 70, "category": "boundary"}}
    ]
}}"""


def _build_prompt(diff: str, context: dict | None) -> str:
    context_str = ""
    if context:
        parts = []
        if context.get("title"):
            parts.append(f"PR标题：{context['title']}")
        if context.get("description"):
            parts.append(f"PR描述：{context['description'][:500]}")
        if context.get("labels"):
            parts.append(f"标签：{', '.join(context['labels'])}")
        if context.get("related_issues"):
            for issue in context["related_issues"]:
                parts.append(f"关联Issue #{issue['number']}：{issue['title']}")
        context_str = "\n".join(parts)
    return PROMPT_TEMPLATE.format(
        context_str=context_str or "无额外上下文",
        diff=diff[:8000] if diff else "无代码变更（模拟分析）",
    )


def _try_parse_json(content: str) -> dict | None:
    raw = content.strip()

    # 1) extract content from ```json ... ``` or ``` ... ``` block
    import re
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
    if m:
        raw = m.group(1).strip()
        logger.info("Extracted JSON from code block")

    # 2) find outermost { … }
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    # 3) try to parse
    try:
        return json.loads(raw)
    except Exception as e:
        logger.warning("JSON parse failed, raw content (first 500): %s", raw[:500])
        logger.debug("Full raw content: %s", raw)
        return None


# ── Tier 1: DeepSeek ──────────────────────────────────────────

def call_deepseek(prompt: str) -> dict | None:
    if not DEEPSEEK_API_KEY:
        logger.info("DeepSeek skipped: no API key")
        return None
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, timeout=TIMEOUT)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        result = _try_parse_json(response.choices[0].message.content)
        if result:
            logger.info("DeepSeek succeeded")
            return result
        # API 返回了非 JSON 内容（可能是余额不足等提示）
        logger.warning("DeepSeek returned non-JSON content (possible insufficient balance): %.200s", response.choices[0].message.content)
        return None
    except Exception as e:
        logger.warning("DeepSeek failed (possible insufficient balance): %s", e)
        return None


# ── Tier 2: 智谱 ────────────────────────────────────────────

def call_zhipu(prompt: str) -> dict | None:
    if not ZHIPU_API_KEY:
        logger.info("智谱 skipped: no API key")
        return None
    try:
        logger.debug("智谱: 开始调用 API, model=%s, base_url=%s", ZHIPU_MODEL, ZHIPU_BASE_URL)
        client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL, timeout=TIMEOUT)
        response = client.chat.completions.create(
            model=ZHIPU_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw_content = response.choices[0].message.content
        logger.info("智谱: 原始响应内容 (前200字符): %.200s", raw_content or "")
        logger.info("智谱: 完整响应内容:\n%s", raw_content or "")
        result = _try_parse_json(raw_content)
        if result:
            logger.info("智谱 succeeded, summary=%s", result.get("summary", "")[:80])
            return result
        logger.warning("智谱: JSON 解析失败, raw=%.200s", raw_content)
        return None
    except Exception as e:
        logger.warning("智谱 failed: %s", e, exc_info=True)
        return None


# ── Tier 3: Ollama ──────────────────────────────────────────

def call_ollama(prompt: str) -> dict | None:
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body.get("response", "")
        result = _try_parse_json(content)
        if result:
            logger.info("Ollama succeeded")
        return result
    except Exception as e:
        logger.warning("Ollama failed: %s", e)
        return None


# ── Fallback: mock data ─────────────────────────────────────

MOCK_RISKS = [
    {"text": "未对用户输入做 SQL 注入防护", "confidence": 95, "category": "security", "severity": "critical", "reasoning": "用户输入直接拼接到 SQL 查询中，未做转义或参数化处理，攻击者可构造恶意 SQL 语句窃取或篡改数据"},
    {"text": "缺少请求频率限制", "confidence": 88, "category": "security", "severity": "high", "reasoning": "未对 API 端点实施限流措施，攻击者可进行暴力破解或 DDoS 攻击，导致服务不可用"},
    {"text": "关键路径缺少日志埋点", "confidence": 82, "category": "observability", "severity": "medium", "reasoning": "核心业务路径未记录关键操作日志，故障时无法定位问题根因，违反可观测性最佳实践"},
    {"text": "存在 XSS 跨站脚本攻击的可能性", "confidence": 91, "category": "security", "severity": "critical", "reasoning": "用户输入未经过滤直接渲染到页面，攻击者可注入恶意脚本窃取用户 Cookie 或执行未授权操作"},
    {"text": "未处理边界情况（空值/异常）", "confidence": 75, "category": "boundary", "severity": "medium", "reasoning": "代码未对空指针、越界等异常输入做保护，生产环境可能触发未捕获异常导致服务中断"},
    {"text": "敏感信息可能通过错误信息泄露", "confidence": 78, "category": "security", "severity": "high", "reasoning": "异常信息中包含堆栈跟踪或数据库详情，攻击者可利用这些信息推断系统架构和漏洞"},
    {"text": "缺乏事务管理，数据一致性无法保证", "confidence": 85, "category": "logic", "severity": "high", "reasoning": "涉及多表写入操作未使用事务，部分失败时会导致数据不一致，影响业务完整性"},
]

MOCK_SUGGESTIONS = [
    {"text": "添加输入验证中间件", "confidence": 92, "category": "security", "reasoning": "集中式输入验证可统一过滤恶意负载，减少在各控制器重复实现校验逻辑的遗漏风险"},
    {"text": "补充单元测试覆盖", "confidence": 88, "category": "style", "reasoning": "当前变更未包含对应单元测试，无法自动化验证逻辑正确性，后续重构易引入回归缺陷"},
    {"text": "引入 TypeScript 类型检查", "confidence": 72, "category": "style", "reasoning": "JavaScript 动态类型在大型项目中易导致运行时类型错误，TypeScript 可提前捕获接口不匹配问题"},
    {"text": "添加 API 版本控制机制", "confidence": 65, "category": "logic", "reasoning": "缺少版本前缀的 API 在迭代中难以保持向后兼容，客户端升级时可能因接口变更而中断"},
    {"text": "实现熔断降级策略", "confidence": 70, "category": "performance", "reasoning": "依赖外部服务未配置熔断器，当下游故障时会级联影响本服务，降低整体系统可用性"},
    {"text": "补充集成测试和端到端测试", "confidence": 80, "category": "boundary", "reasoning": "仅单元测试不足以验证模块间协作，集成测试可覆盖 API 契约和跨服务调用场景"},
    {"text": "添加 API 文档注释（OpenAPI）", "confidence": 55, "category": "observability", "reasoning": "接口缺少结构化文档，新成员接入成本高，且无法自动生成客户端 SDK 和测试桩"},
]

MOCK_SUMMARIES = [
    "本次 PR 主要增加了用户认证模块，优化了错误处理逻辑",
    "本次 PR 重构了核心业务逻辑，提升了系统可维护性",
    "本次 PR 修复了多处潜在的内存泄漏问题，增强了稳定性",
    "本次 PR 优化了数据库查询性能，减少了响应延迟",
    "本次 PR 引入了新的组件化架构方案，降低了模块耦合度",
    "本次 PR 增强了系统可观测性与日志记录，便于问题排查",
]


def get_mock_data(context: dict | None = None, files_changed: int = 0, additions: int = 0, deletions: int = 0) -> dict:
    summary = random.choice(MOCK_SUMMARIES)
    if context and context.get("title"):
        summary = context["title"]
    if context and context.get("labels"):
        summary += f"  [标签: {', '.join(context['labels'][:5])}]"
    if files_changed > 0:
        summary += f"（涉及 {files_changed} 个文件，+{additions}/-{deletions} 行）"

    risks = random.sample(MOCK_RISKS, min(3, len(MOCK_RISKS)))
    suggestions = random.sample(MOCK_SUGGESTIONS, min(3, len(MOCK_SUGGESTIONS)))

    if additions > 200:
        risks.append({"text": "变更量过大，建议拆分为多个 PR 以降低审查难度", "confidence": 93, "category": "style", "severity": "medium", "reasoning": "单次 PR 修改超过 200 行，审查者难以全面理解变更意图，建议拆分为多个独立 PR"})
    if deletions > 100:
        risks.append({"text": "大量删除操作，请确认没有误删必要逻辑", "confidence": 80, "category": "logic", "severity": "high", "reasoning": "删除超过 100 行代码，需逐一确认被删逻辑是否已被替代或确实不再需要，避免功能缺失"})

    return {"summary": summary, "risks": risks, "suggestions": suggestions}


# ── Main entry ──────────────────────────────────────────────

def analyze_diff(diff: str, context: dict | None = None) -> dict:
    lines = diff.splitlines()
    files_changed = sum(1 for l in lines if l.startswith("+++ b/"))
    additions = sum(1 for l in lines if l.startswith("+"))
    deletions = sum(1 for l in lines if l.startswith("-"))

    prompt = _build_prompt(diff, context)

    for tier_name, caller in [("DeepSeek", call_deepseek), ("智谱", call_zhipu), ("Ollama", call_ollama)]:
        logger.debug("尝试调用 %s ...", tier_name)
        result = caller(prompt)
        if result and "summary" in result:
            logger.info("使用 %s 完成分析", tier_name)
            return result
        logger.warning("降级: %s 返回无效结果或不可用, 尝试下一级", tier_name)

    logger.info("所有 AI 服务不可用，使用模拟数据兜底")
    return get_mock_data(context, files_changed, additions, deletions)


# ── Backward compatibility alias ────────────────────────────

def analyze_diff_with_llm(diff: str, context: dict | None = None) -> dict:
    return analyze_diff(diff, context)
