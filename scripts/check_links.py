"""Check that every relative link in tracked Markdown files points to an existing file.

python scripts/check_links.py
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def main() -> int:
    files = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    # snapshot fixtures describe a run's report/ directory, not navigable repository links
    files = [f for f in files if not f.startswith("tests/snapshots/")]
    broken, checked = [], 0
    for f in files:
        text = (ROOT / f).read_text(encoding="utf-8")
        # ignore links inside fenced code blocks (verbatim logs)
        text = re.sub(r"````.*?````|```.*?```", "", text, flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            checked += 1
            if not (ROOT / f).parent.joinpath(path).exists():
                broken.append(f"{f}: {target}")
    print(f"markdown files: {len(files)}; relative links checked: {checked}")
    for b in broken:
        print(f"BROKEN: {b}")
    print("OK: no broken links" if not broken else f"FAILED: {len(broken)} broken link(s)")
    return 0 if not broken else 1


if __name__ == "__main__":
    sys.exit(main())
