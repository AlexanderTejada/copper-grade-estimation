import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: str = None) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def git_status(repo_path: str) -> str:
    return run(["git", "status", "--short"], cwd=repo_path)


def git_log(repo_path: str, n: int = 10) -> str:
    return run(["git", "log", f"-{n}", "--oneline"], cwd=repo_path)


def git_commit(repo_path: str, message: str) -> str:
    run(["git", "add", "-A"], cwd=repo_path)
    return run(["git", "commit", "-m", message], cwd=repo_path)


def git_create_branch(repo_path: str, branch: str) -> str:
    return run(["git", "checkout", "-b", branch], cwd=repo_path)


def git_current_branch(repo_path: str) -> str:
    return run(["git", "branch", "--show-current"], cwd=repo_path)


def git_diff(repo_path: str) -> str:
    return run(["git", "diff"], cwd=repo_path)
