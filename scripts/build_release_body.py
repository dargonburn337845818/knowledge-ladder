"""从 RELEASE_NOTES.md 提取最新版本段落，供 GitHub Release 使用。

用法：python scripts/build_release_body.py
输出：release_body.md（只保留第一个 # v... 段落到下一个 --- 之前）
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES = os.path.join(REPO_ROOT, "RELEASE_NOTES.md")
OUTPUT = os.path.join(REPO_ROOT, "release_body.md")


def main():
    with open(NOTES, encoding="utf-8") as f:
        lines = f.readlines()

    start = None
    for i, line in enumerate(lines):
        if line.startswith("# v"):
            start = i
            break
    if start is None:
        raise SystemExit("RELEASE_NOTES.md has no '# v' section")

    body = [lines[start]]
    for line in lines[start + 1:]:
        if line.strip() == "---":
            break
        body.append(line)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.writelines(body)

    print(f"Written: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
