import subprocess

def run(cmd):
    subprocess.run(cmd, check=True)

def commit_and_push(msg="Arkadia Code Weaver update"):
    run(["git", "add", "."])
    run(["git", "commit", "-m", msg])
    run(["git", "push"])
