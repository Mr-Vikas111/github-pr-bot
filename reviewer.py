import requests
from llm import ask_llm

def fetch_diff(diff_url):
    return requests.get(diff_url).text


def load_agent():
    with open("agent/SOUL.md") as f:
        soul = f.read()
    with open("agent/RULES.md") as f:
        rules = f.read()
    return soul, rules


def review_diff(diff):
    soul, rules = load_agent()

    prompt = f"""
    {rules}

    You are a strict code reviewer.

    Return output in this format:

    ### AI Code Review

    #### Issues:
    - ...

    #### Severity:
    - High / Medium / Low

    #### Fix:
    - ...

    If no issues:
    Return: "No significant issues found"

    DIFF:
    {diff[:8000]}
    """

    return ask_llm(soul, prompt)


def run_review(diff_url):
    diff = fetch_diff(diff_url)

    if not diff.strip():
        return "No changes detected in PR."

    return review_diff(diff)