
import re

def extract_code(text):
    matches = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if matches:
        # Join all code blocks in case there are multiple
        return "\n".join(matches).strip()
    else:
        return text.strip()

def extract_type(text: str) -> str:
    match = re.search(r"(Final Code):\s*```python", text, re.S)
    if match:
        return match.group(1) + ":"
    
    match = re.search(r"(Code):\s*```python", text, re.S)
    if match:
        return match.group(1) + ":"
    
    return ""

def return_shared_env_summary(env):
    res = ""
    for name, value in env.items():
        if name.startswith("__") and name.endswith("__"):
            continue  # skip built-ins like __builtins__
        res += f"{name} : {type(value).__name__}\n"
    return res