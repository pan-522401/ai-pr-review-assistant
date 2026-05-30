from app.services.github import parse_pr_url, get_pr_diff
from app.services.llm import analyze_diff_with_llm


def perform_review(pr_url: str) -> dict:
    owner, repo, pr_number = parse_pr_url(pr_url)
    diff = get_pr_diff(owner, repo, pr_number)
    result = analyze_diff_with_llm(diff)
    return result
