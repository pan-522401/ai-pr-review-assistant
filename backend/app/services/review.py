import logging
from app.services.github import parse_pr_url, get_pr_diff, get_pr_context
from app.services.llm import analyze_diff_with_llm

logger = logging.getLogger(__name__)


def perform_review(pr_url: str) -> dict:
    owner, repo, pr_number = parse_pr_url(pr_url)
    diff = ""
    context = {}
    try:
        diff = get_pr_diff(owner, repo, pr_number)
    except Exception as e:
        logger.warning("Failed to fetch diff from GitHub: %s. Using mock analysis.", e)
    try:
        context = get_pr_context(owner, repo, pr_number)
    except Exception as e:
        logger.warning("Failed to fetch PR context: %s", e)
    result = analyze_diff_with_llm(diff, context)
    return result
