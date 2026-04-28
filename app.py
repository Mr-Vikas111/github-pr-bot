"""
app.py — FastAPI entry point for the GitHub PR review bot.

Exposes a /webhook endpoint that listens for GitHub pull request events,
triggers an AI-powered code review, and posts the result as a PR comment.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from reviewer import run_full_review
from dotenv import load_dotenv
import logging
import os
import requests

load_dotenv()  # Load variables from .env file into the environment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    try:
        response = requests.post(url, headers=headers, json={"body": comment}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        logger.error("Failed to reach GitHub API (network/DNS issue): %s", e)
        raise
    except requests.exceptions.HTTPError as e:
        logger.error("GitHub API returned an error: %s", e)
        raise


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
    body = await request.body()
    if not body:
        return JSONResponse(status_code=400, content={"status": "error", "detail": "Empty request body"})

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"status": "error", "detail": "Invalid JSON payload"})

    # Only act on PR open or new-commit events
    if payload.get("action") not in ["opened", "synchronize"]:
        return {"status": "ignored"}

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    diff_url = pr["diff_url"]  # URL to the raw unified diff for this PR

    # Run the AI review against the PR diff
    try:
        # review = run_review(diff_url)
        review = run_full_review(diff_url)
    except requests.exceptions.ConnectionError:
        return JSONResponse(status_code=502, content={"status": "error", "detail": "Could not fetch PR diff — network unreachable"})

    # Post the generated review as a comment on the PR
    try:
        post_comment(repo, pr_number, review)
    except requests.exceptions.ConnectionError:
        return JSONResponse(status_code=502, content={"status": "error", "detail": "Could not post comment — GitHub API unreachable (DNS/network failure)"})
    except requests.exceptions.HTTPError as e:
        return JSONResponse(status_code=502, content={"status": "error", "detail": f"GitHub API error: {e}"})

    return {"status": "review posted"}