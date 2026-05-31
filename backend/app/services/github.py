import os
import re
import urllib3
import requests
from typing import Tuple, Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    owner, repo, pr_number = match.groups()
    return owner, repo, int(pr_number)


def _headers():
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "ai-pr-review-assistant"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = _headers()
    headers["Accept"] = "application/vnd.github.v3.diff"
    resp = requests.get(url, headers=headers, verify=False)
    resp.raise_for_status()
    return resp.text


def get_pr_context(owner: str, repo: str, pr_number: int) -> dict:
    context = {"title": "", "description": "", "labels": [], "related_issues": []}
    try:
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        resp = requests.get(pr_url, headers=_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            context["title"] = data.get("title", "")
            context["description"] = data.get("body", "")

            labels = data.get("labels", [])
            context["labels"] = [l["name"] for l in labels if "name" in l]

            desc = context["description"]
            issue_refs = re.findall(r"(?:fixes|closes|resolves|#)\s*#?(\d+)", desc, re.IGNORECASE)
            seen = set()
            for ref in issue_refs:
                num = int(ref)
                if num and num not in seen:
                    seen.add(num)
                    issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{num}"
                    try:
                        ir = requests.get(issue_url, headers=_headers(), timeout=10)
                        if ir.status_code == 200:
                            idata = ir.json()
                            context["related_issues"].append({
                                "number": num,
                                "title": idata.get("title", ""),
                                "body": (idata.get("body") or "")[:300],
                            })
                    except Exception:
                        pass
    except Exception:
        pass
    return context
