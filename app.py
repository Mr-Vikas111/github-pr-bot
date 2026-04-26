"""
app.py — FastAPI entry point for the GitHub PR review bot.

Exposes a /webhook endpoint that listens for GitHub pull request events,
triggers an AI-powered code review, and posts the result as a PR comment.
"""

from fastapi import FastAPI, Request
from reviewer import run_review
import os
import requests

app = FastAPI()

# GitHub personal access token loaded from the environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def post_comment(repo: str, pr_number: int, comment: str) -> None:
    """Post a comment on a GitHub pull request.

    Args:
        repo: Full repository name in ``owner/repo`` format.
        pr_number: The pull request number to comment on.
        comment: The markdown-formatted comment body to post.
    """
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    # GitHub API requires Bearer auth and the correct Accept header
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    requests.post(url, headers=headers, json={"body": comment})


@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming GitHub webhook events for pull requests.

    Processes ``opened`` and ``synchronize`` PR actions, runs an AI review
    on the diff, and posts the result as a comment.

    Args:
        request: The incoming HTTP request containing the GitHub webhook payload.

    Returns:
        A dict with a ``status`` key indicating the outcome.
    """
    payload = await request.json()

    # Only act on PR open or new-commit events
    if payload.get("action") not in ["opened", "synchronize"]:
        return {"status": "ignored"}

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    diff_url = pr["diff_url"]  # URL to the raw unified diff for this PR

    # Run the AI review against the PR diff
    review = run_review(diff_url)

    # Post the generated review as a comment on the PR
    post_comment(repo, pr_number, review)

    return {"status": "review posted"}