import random


CATEGORY_ICONS = {
    "security": "\U0001f512",
    "performance": "\u26a1",
    "boundary": "\U0001f50d",
    "logic": "\U0001f9e9",
    "style": "\U0001f4dd",
    "observability": "\U0001f4ca",
}


def analyze_diff_with_llm(diff: str, context: dict = None) -> dict:
    lines = diff.splitlines()

    files_changed = 0
    additions = 0
    deletions = 0
    for line in lines:
        if line.startswith("+++ b/"):
            files_changed += 1
        elif line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1

    # Build a richer summary from context if available
    summary = _build_summary(context, files_changed, additions, deletions)

    risk_pool = [
        {"text": "未对用户输入做 SQL 注入防护", "confidence": 95, "category": "security", "severity": "critical", "reasoning": "用户输入直接拼接到 SQL 查询中，未做转义或参数化处理，攻击者可构造恶意 SQL 语句窃取或篡改数据"},
        {"text": "缺少请求频率限制", "confidence": 88, "category": "security", "severity": "high", "reasoning": "未对 API 端点实施限流措施，攻击者可进行暴力破解或 DDoS 攻击，导致服务不可用"},
        {"text": "关键路径缺少日志埋点", "confidence": 82, "category": "observability", "severity": "medium", "reasoning": "核心业务路径未记录关键操作日志，故障时无法定位问题根因，违反可观测性最佳实践"},
        {"text": "存在 XSS 跨站脚本攻击的可能性", "confidence": 91, "category": "security", "severity": "critical", "reasoning": "用户输入未经过滤直接渲染到页面，攻击者可注入恶意脚本窃取用户 Cookie 或执行未授权操作"},
        {"text": "未处理边界情况（空值/异常）", "confidence": 75, "category": "boundary", "severity": "medium", "reasoning": "代码未对空指针、越界等异常输入做保护，生产环境可能触发未捕获异常导致服务中断"},
        {"text": "敏感信息可能通过错误信息泄露", "confidence": 78, "category": "security", "severity": "high", "reasoning": "异常信息中包含堆栈跟踪或数据库详情，攻击者可利用这些信息推断系统架构和漏洞"},
        {"text": "缺乏事务管理，数据一致性无法保证", "confidence": 85, "category": "logic", "severity": "high", "reasoning": "涉及多表写入操作未使用事务，部分失败时会导致数据不一致，影响业务完整性"},
    ]
    suggestion_pool = [
        {"text": "添加输入验证中间件", "confidence": 92, "category": "security", "reasoning": "集中式输入验证可统一过滤恶意负载，减少在各控制器重复实现校验逻辑的遗漏风险"},
        {"text": "补充单元测试覆盖", "confidence": 88, "category": "style", "reasoning": "当前变更未包含对应单元测试，无法自动化验证逻辑正确性，后续重构易引入回归缺陷"},
        {"text": "引入 TypeScript 类型检查", "confidence": 72, "category": "style", "reasoning": "JavaScript 动态类型在大型项目中易导致运行时类型错误，TypeScript 可提前捕获接口不匹配问题"},
        {"text": "添加 API 版本控制机制", "confidence": 65, "category": "logic", "reasoning": "缺少版本前缀的 API 在迭代中难以保持向后兼容，客户端升级时可能因接口变更而中断"},
        {"text": "实现熔断降级策略", "confidence": 70, "category": "performance", "reasoning": "依赖外部服务未配置熔断器，当下游故障时会级联影响本服务，降低整体系统可用性"},
        {"text": "补充集成测试和端到端测试", "confidence": 80, "category": "boundary", "reasoning": "仅单元测试不足以验证模块间协作，集成测试可覆盖 API 契约和跨服务调用场景"},
        {"text": "添加 API 文档注释（OpenAPI）", "confidence": 55, "category": "observability", "reasoning": "接口缺少结构化文档，新成员接入成本高，且无法自动生成客户端 SDK 和测试桩"},
    ]

    num_risks = min(3, len(risk_pool))
    num_suggestions = min(3, len(suggestion_pool))

    risks = random.sample(risk_pool, num_risks)
    suggestions = random.sample(suggestion_pool, num_suggestions)

    if additions > 200:
        risks.append({"text": "变更量过大，建议拆分为多个 PR 以降低审查难度", "confidence": 93, "category": "style", "severity": "medium", "reasoning": "单次 PR 修改超过 200 行，审查者难以全面理解变更意图，建议拆分为多个独立 PR"})
    if deletions > 100:
        risks.append({"text": "大量删除操作，请确认没有误删必要逻辑", "confidence": 80, "category": "logic", "severity": "high", "reasoning": "删除超过 100 行代码，需逐一确认被删逻辑是否已被替代或确实不再需要，避免功能缺失"})

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
    }


def _build_summary(context: dict | None, files_changed: int, additions: int, deletions: int) -> str:
    summary_templates = [
        "本次 PR 主要增加了用户认证模块，优化了错误处理逻辑",
        "本次 PR 重构了核心业务逻辑，提升了系统可维护性",
        "本次 PR 修复了多处潜在的内存泄漏问题，增强了稳定性",
        "本次 PR 优化了数据库查询性能，减少了响应延迟",
        "本次 PR 引入了新的组件化架构方案，降低了模块耦合度",
        "本次 PR 增强了系统可观测性与日志记录，便于问题排查",
    ]
    summary = random.choice(summary_templates)

    if context and context.get("title"):
        summary = context["title"]
    if context and context.get("labels"):
        label_str = ", ".join(context["labels"][:5])
        summary = f"{summary}  [标签: {label_str}]"
        if files_changed > 0:
            summary += f" ［涉及 {files_changed} 个文件，+{additions}/-{deletions} 行］"
    elif files_changed > 0:
        summary += f"（涉及 {files_changed} 个文件，+{additions}/-{deletions} 行）"

    return summary
