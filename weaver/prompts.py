SYSTEM_PROMPT = """
You are Arkadia Code Weaver.
You rewrite code precisely.
You return FULL FILE CONTENTS.
You never explain.
You never summarize.
You output in this format only:

--- FILE: path/to/file.py ---
<full file code>
"""

def build_prompt(task, files):
    blob = "\n\n".join(
        f"--- FILE: {k} ---\n{v}" for k, v in files.items()
    )
    return f"{SYSTEM_PROMPT}\n\nTASK:\n{task}\n\nREPO:\n{blob}"

