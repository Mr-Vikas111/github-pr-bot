"""
llm.py — Thin wrapper around the local Ollama inference API.

Handles prompt construction and communication with the Ollama server
running on localhost.
"""

import requests

# Base URL for the locally hosted Ollama API
OLLAMA_URL = "http://localhost:11434/api/generate"

# Model identifier as registered in Ollama
MODEL = "llama3.2"


def ask_llm(system: str, prompt: str) -> str:
    """Send a prompt to the local Ollama LLM and return its response.

    Combines the system persona and the user prompt into a single
    full-prompt string before posting to the Ollama generate endpoint.

    Args:
        system: The system/persona instruction (agent SOUL content).
        prompt: The user-facing prompt containing the diff and review rules.

    Returns:
        The model's text response as a string.
    """
    # Prepend system context to the prompt for models that don't support
    # a dedicated system role (Ollama /api/generate uses a single prompt field)
    full_prompt = f"{system}\n\n{prompt}"

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": full_prompt,
            "stream": False  # Receive the complete response in one go
        }
    )

    return response.json()["response"]