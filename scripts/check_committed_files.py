"""Check tracked (indexed) files: none over 1 MB, no .env/key files, no secret-like strings.

    git add -A && python scripts/check_committed_files.py

Exit code 0 only if every check passes.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 1_000_000
BAD_NAMES = re.compile(
    r"(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa.*|id_ed25519.*|.*\.p12|.*\.pfx)$"
)
SECRET_PATTERNS = {
    "private key block": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "GitHub token": re.compile(rb"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}"),
    "AWS access key id": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(rb"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "generic api key assignment": re.compile(
        rb"(?i)\b(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9/+_\-]{16,}['\"]"
    ),
}


def main() -> int:
    files = (
        subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
        .stdout.decode()
        .split("\0")
    )
    files = [f for f in files if f]
    problems: list[str] = []
    sizes = sorted(((ROOT / f).stat().st_size, f) for f in files)
    for size, f in sizes:
        if size > MAX_BYTES:
            problems.append(f"too large ({size} bytes > {MAX_BYTES}): {f}")
    for f in files:
        if BAD_NAMES.search(f):
            problems.append(f"sensitive file name: {f}")
        data = (ROOT / f).read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(data):
                problems.append(f"{label} pattern in {f}")
    print(f"tracked files checked: {len(files)}")
    print(f"total tracked bytes: {sum(s for s, _ in sizes)}")
    print("largest tracked files:")
    for size, f in sizes[-5:][::-1]:
        print(f"  {size:>9}  {f}")
    print(f"files over {MAX_BYTES} bytes: {sum(1 for s, _ in sizes if s > MAX_BYTES)}")
    print(f"sensitive file names (.env, keys): {sum(1 for f in files if BAD_NAMES.search(f))}")
    for p in problems:
        print(f"PROBLEM: {p}")
    print("OK: no problems found" if not problems else f"FAILED: {len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
