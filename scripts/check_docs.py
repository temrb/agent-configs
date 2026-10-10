#!/usr/bin/env python3
"""Check local Markdown paths in maintained repository documentation."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
PATHS = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md")),
         *sorted((ROOT / "agents").rglob("README.md"))]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
HEAD = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def anchors(markdown):
    result = set()
    counts = {}
    for text in HEAD.findall(markdown):
        normalized = re.sub(r"[^\w -]", "", re.sub(r"\[[^\]]+\]\([^)]+\)", "", text.lower()))
        normalized = re.sub(r"\s+", "-", normalized.strip())
        counts[normalized] = counts.get(normalized, 0) + 1
        suffix = f"-{counts[normalized] - 1}" if counts[normalized] > 1 else ""
        result.add(normalized + suffix)
    return result


def main():
    errors = []
    for source in PATHS:
        document = source.read_text()
        for destination in LINK.findall(document):
            if "://" in destination or destination.startswith(("mailto:", "#")):
                continue
            path, _, fragment = destination.partition("#")
            target = (source.parent / unquote(path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f"{source.relative_to(ROOT)}: missing {destination}")
            elif fragment and target.is_file() and target.suffix == ".md":
                if unquote(fragment).lower() not in anchors(target.read_text()):
                    errors.append(f"{source.relative_to(ROOT)}: missing anchor {destination}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Documentation links are valid.")


if __name__ == "__main__":
    main()
