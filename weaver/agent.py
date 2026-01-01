from .llm import call_llm
from .fs import read_repo, write_file
from .git_ops import commit_and_push
from .prompts import build_prompt
from .logger import get_logger
import re

LOGGER = get_logger()

def run(task: str, engine_cycle: int | None = None):
    files = read_repo(".")
    prompt = build_prompt(task, files)
    try:
        response = call_llm("gemini", prompt)
    except Exception as e:
        # Log gracefully and return no updates
        LOGGER.warning("LLM call failed for task '%s': %s", task, e)
        return [], None

    pattern = r"--- FILE: (.*?) ---\n(.*?)(?=--- FILE:|\Z)"
    matches = re.findall(pattern, response, re.S)

    if not matches:
        LOGGER.info("LLM returned no file updates for task: %s", task)
        return [], None

    updated_files = []
    for path, content in matches:
        changed = write_file(path.strip(), content.strip())
        if changed:
            updated_files.append(path.strip())

    if updated_files:
        commit_msg = f"weaver: auto update - {task}"
        # attempt to parse engine cycle from task if provided
        try:
            m = re.search(r"recursive step (\d+)", task)
            engine_cycle = int(m.group(1)) if m else engine_cycle
        except Exception:
            engine_cycle = engine_cycle
        meta = {"engine_cycle": engine_cycle} if engine_cycle is not None else None
        success = commit_and_push(commit_msg, paths=updated_files, meta=meta)
        if success:
            LOGGER.info("Committed changes: %s", commit_msg)
            return updated_files, commit_msg
        else:
            LOGGER.warning("Commit or push failed for %s", commit_msg)
            return updated_files, None
    return [], None
