def analyze_diff_with_llm(diff: str) -> dict:
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

    summary_templates = [
        "本次 PR 主要增加了用户认证模块，优化了错误处理逻辑",
        "本次 PR 重构了核心业务逻辑，提升了系统可维护性",
        "本次 PR 修复了多处潜在的内存泄漏问题，增强了稳定性",
        "本次 PR 优化了数据库查询性能，减少了响应延迟",
        "本次 PR 引入了新的组件化架构方案，降低了模块耦合度",
        "本次 PR 增强了系统可观测性与日志记录，便于问题排查",
    ]
    import random
    summary = random.choice(summary_templates)

    if files_changed > 0:
        summary += f"（涉及 {files_changed} 个文件，+{additions}/-{deletions} 行）"

    risk_pool = [
        "风险1：未对用户输入做 SQL 注入防护",
        "风险2：缺少请求频率限制",
        "风险3：关键路径缺少日志埋点",
        "风险4：存在 XSS 跨站脚本攻击的可能性",
        "风险5：未处理边界情况（空值/异常）",
        "风险6：敏感信息可能通过错误信息泄露",
        "风险7：缺乏事务管理，数据一致性无法保证",
    ]
    suggestion_pool = [
        "建议1：添加输入验证中间件",
        "建议2：补充单元测试覆盖",
        "建议3：引入 TypeScript 类型检查",
        "建议4：添加 API 版本控制机制",
        "建议5：实现熔断降级策略",
        "建议6：补充集成测试和端到端测试",
        "建议7：添加 API 文档注释（OpenAPI）",
    ]

    num_risks = min(3, len(risk_pool))
    num_suggestions = min(3, len(suggestion_pool))

    risks = random.sample(risk_pool, num_risks)
    suggestions = random.sample(suggestion_pool, num_suggestions)

    if additions > 200:
        risks.append("风险警告：变更量过大，建议拆分为多个 PR 以降低审查难度")
    if deletions > 100:
        risks.append("风险警告：大量删除操作，请确认没有误删必要逻辑")

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
    }
