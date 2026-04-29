def load_agent(path) -> tuple[str, str]:
    """Load the agent's SOUL and RULES configuration files.

    Returns:
        A tuple of ``(soul, rules)`` where both are markdown strings
        that define the reviewer's persona and coding standards.
    """
    with open(f"{path}/SOUL.md") as f:
        soul = f.read()  # Reviewer persona / system identity
    with open(f"{path}/RULES.md") as f:
        rules = f.read()  # Project-specific coding rules
    return soul, rules