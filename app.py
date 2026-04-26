from fastapi import FastAPI, Request
from reviewer import run_review
import os
import requests

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def post_comment(repo, pr_number, comment):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    requests.post(url, headers=headers, json={"body": comment})


@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()

    if payload.get("action") not in ["opened", "synchronize"]:
        return {"status": "ignored"}

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    diff_url = pr["diff_url"]

    review = run_review(diff_url)

    post_comment(repo, pr_number, review)

    return {"status": "review posted"}