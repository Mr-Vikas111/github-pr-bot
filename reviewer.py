"""
reviewer.py — Core PR review logic for the GitHub PR bot.

Fetches the pull request diff, loads the agent personality and rules,
builds a review prompt, and delegates inference to the LLM module.
"""

import logging

import requests
from llm import ask_llm
from utils import load_agent
import requests

logger = logging.getLogger(__name__)


def fetch_diff(diff_url: str) -> str:
    """Download the raw unified diff for a pull request.

    Args:
        diff_url: The URL pointing to the PR's raw diff.

    Returns:
        The diff as a plain-text string.

    Raises:
        requests.exceptions.ConnectionError: If the diff URL is unreachable.
    """
    try:
        response = requests.get(diff_url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.ConnectionError as e:
        logger.error("Failed to fetch diff from %s: %s", diff_url, e)
        raise

def run_reviewer(diff):
    soul, rules = load_agent("agent")

    prompt = f"""
    {rules}

    Analyze this PR diff.

    Return:
    - Issues
    - Severity
    - Fix

    DIFF:
    {diff[:8000]}
    """

    return ask_llm(soul, prompt)


def run_validator(review_output):
    soul, rules = load_agent("agent/agents/validator")

    prompt = f"""
    {rules}

    Validate this code review.

    Remove incorrect or weak issues.

    Return only high-confidence issues.

    REVIEW:
    {review_output}
    """

    return ask_llm(soul, prompt)


def run_full_review(diff_url):
    diff = fetch_diff(diff_url)

    if not diff.strip():
        return "No changes detected."

    review = run_reviewer(diff)

    validated = run_validator(review)

    return validated
