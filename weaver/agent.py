from .llm import gemini
from .fs import read_repo, write_file
from .git_ops import commit_and_push
from .prompts import build_prompt
import re

def run(task: str):
    files = read_repo(".")
    prompt = build_prompt(task, files)
    response = gemini(prompt)

    pattern = r"--- FILE: (.*?) ---\n(.*?)(?=--- FILE:|\Z)"
    matches = re.findall(pattern, response, re.S)

    if not matches:
        raise RuntimeError("No files returned by model")

    for path, content in matches:
        write_file(path.strip(), content.strip())

    commit_and_push(f"Arkadia update: {task}")
