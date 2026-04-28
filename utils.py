def load_agent(path):
    with open(f"{path}/SOUL.md") as f:
        soul = f.read()
    with open(f"{path}/RULES.md") as f:
        rules = f.read()
    return soul, rules