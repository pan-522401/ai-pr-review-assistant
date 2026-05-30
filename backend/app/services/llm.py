def analyze_diff_with_llm(diff: str) -> dict:
    lines = diff.splitlines()
    summary_parts = []
    risks = []
    suggestions = []

    files_changed = 0
    additions = 0
    deletions = 0
    for line in lines:
        if line.startswith("+++ b/"):
            files_changed += 1
            summary_parts.append(line[6:])
        elif line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1

    summary = (
        f"这是一段示例总结，描述 PR 变更的主要内容。"
        f"Changed {files_changed} file(s): {', '.join(summary_parts)}. "
        f"Total: +{additions} / -{deletions} lines."
    )

    if additions > 100:
        risks.append("示例风险1：可能存在性能问题 — large PR with over 100 additions")
    elif additions > 50:
        risks.append("示例风险2：需要增加错误处理 — moderately sized PR, consider splitting")
    else:
        risks.append("小范围变更，风险较低")

    if files_changed > 10:
        risks.append(f"涉及 {files_changed} 个文件，可能存在 scope creep 风险")

    suggestions.append("示例建议1：添加单元测试")
    suggestions.append("示例建议2：补充注释文档")
    suggestions.append("确保提交信息符合 conventional commit 格式")

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
    }
