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


def load_agent() -> tuple[str, str]:
    """Load the agent's SOUL and RULES configuration files.

    Returns:
        A tuple of ``(soul, rules)`` where both are markdown strings
        that define the reviewer's persona and coding standards.
    """
    with open("agent/SOUL.md") as f:
        soul = f.read()  # Reviewer persona / system identity
    with open("agent/RULES.md") as f:
        rules = f.read()  # Project-specific coding rules
    return soul, rules


def review_diff(diff: str) -> str:
    """Generate an AI code review for the given diff.

    Builds a structured prompt containing the agent rules and the diff,
    then queries the LLM for a formatted review.

    Args:
        diff: The raw unified diff text to review.

    Returns:
        A markdown-formatted review string produced by the LLM.
    """
    soul, rules = load_agent()

    # Truncate diff to 8000 chars to stay within the model's context window
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


# def run_review(diff_url: str) -> str:
#     """Fetch a PR diff and return the AI-generated review.

#     Args:
#         diff_url: URL of the pull request's raw diff.

#     Returns:
#         A markdown review string, or a message if no changes are detected.
#     """
#     diff = fetch_diff(diff_url)

#     # Guard against empty diffs (e.g. draft PRs with no commits)
#     if not diff.strip():
#         return "No changes detected in PR."

#     return review_diff(diff)


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
