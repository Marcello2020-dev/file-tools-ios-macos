#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

DOUBLE_PDF_RE = re.compile(r"\.pdf\.pdf$", re.IGNORECASE)

@dataclass
class Item:
    old: Path
    new: Path
    status: str  # OK / SKIP / CONFLICT / RENAMED / ERROR
    note: str = ""

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def safe_target(path: Path) -> Path:
    """If target exists, append _1, _2, ... before extension."""
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for i in range(1, 10_000):
        cand = path.with_name(f"{stem}_{i}{suffix}")
        if not cand.exists():
            return cand
    raise RuntimeError(f"Too many conflicts for {path.name}")

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fix duplicate .pdf.pdf extensions recursively. Default is DRY-RUN."
    )
    ap.add_argument("root", nargs="?", default=".", help="Root folder (default: current folder)")
    ap.add_argument("--apply", action="store_true", help="Actually rename files (otherwise dry-run)")
    ap.add_argument("--report", default="", help="Report filename (.md). Default: FIX_PDF_NAMES_<ts>.md")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: root is not a folder: {root}")
        return 2

    report_name = args.report.strip() or f"FIX_PDF_NAMES_{ts()}.md"
    report_path = (Path.cwd() / report_name).resolve()

    items: list[Item] = []
    total = 0

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        total += 1
        name = p.name

        if not DOUBLE_PDF_RE.search(name):
            continue

        new_name = DOUBLE_PDF_RE.sub(".pdf", name)
        target = p.with_name(new_name)

        if target.resolve() == p.resolve():
            items.append(Item(p, target, "SKIP", "same path"))
            continue

        if target.exists():
            try:
                target2 = safe_target(target)
                note = f"target exists → using {target2.name}"
                target = target2
            except Exception as e:
                items.append(Item(p, target, "CONFLICT", str(e)))
                continue

        if args.apply:
            try:
                p.rename(target)
                items.append(Item(p, target, "RENAMED", "renamed"))
            except Exception as e:
                items.append(Item(p, target, "ERROR", str(e)))
        else:
            items.append(Item(p, target, "OK", "dry-run"))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode = "APPLY (rename)" if args.apply else "DRY-RUN (no changes)"

    ok = sum(1 for i in items if i.status in ("OK", "RENAMED"))
    conflicts = sum(1 for i in items if i.status in ("CONFLICT", "ERROR"))

    lines: list[str] = []
    lines.append("# PDF Filename Normalizer (.pdf.pdf → .pdf)\n\n")
    lines.append(f"Generated: **{now}**  \n")
    lines.append(f"Mode: **{mode}**  \n")
    lines.append(f"Root: `{root}`  \n")
    lines.append(f"Report: `{report_path.name}`\n\n")
    lines.append("## Summary\n\n")
    lines.append(f"- Scanned files: **{total}**\n")
    lines.append(f"- Matches (.pdf.pdf): **{len(items)}**\n")
    lines.append(f"- OK/RENAMED: **{ok}**\n")
    lines.append(f"- Conflicts/Errors: **{conflicts}**\n\n")

    lines.append("## Details\n\n")
    if items:
        lines.append("| Status | Old name | New name | Note |\n")
        lines.append("|---|---|---|---|\n")
        for it in items:
            lines.append(f"| {it.status} | `{it.old}` | `{it.new}` | {it.note} |\n")
    else:
        lines.append("_No files with double .pdf extension found._\n")

    report_path.write_text("".join(lines), encoding="utf-8")
    print(f"OK: wrote {report_path.name} (matches={len(items)}, mode={mode})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())