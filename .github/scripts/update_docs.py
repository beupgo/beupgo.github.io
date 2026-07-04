#!/usr/bin/env python3
"""
update_docs.py
Scan all HTML learning pages and regenerate the auto-generated sections
in README.md, index.html, and each sub-page.

Sentinel markers used:
  README.md  : <!-- AUTO-TABLE-START --> / <!-- AUTO-TABLE-END -->
               <!-- AUTO-FILES-START --> / <!-- AUTO-FILES-END -->
  index.html : <!-- AUTO-CARDS-START --> / <!-- AUTO-CARDS-END -->
  sub-pages  : <!-- AUTO-BACK-NAV-START --> / <!-- AUTO-BACK-NAV-END -->
               (sticky "back to home" nav bar; injected right after <body>
               on first run, updated in-place on subsequent runs)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root

GRADE_NAMES_ZH = {
    1: "一年级", 2: "二年级", 3: "三年级",
    4: "四年级", 5: "五年级", 6: "六年级",
    7: "七年级", 8: "八年级", 9: "九年级",
}

SUBJECT_NAMES_ZH = {
    "math":      "数学",
    "chinese":   "语文",
    "english":   "英语",
    "science":   "科学",
    "physics":   "物理",
    "chemistry": "化学",
    "biology":   "生物",
    "history":   "历史",
    "geography": "地理",
    "art":       "美术",
    "music":     "音乐",
    "pe":        "体育",
}

ARROW_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
    ' stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>'
)

BACK_NAV_START = "<!-- AUTO-BACK-NAV-START -->"
BACK_NAV_END   = "<!-- AUTO-BACK-NAV-END -->"

BACK_NAV_HTML = (
    '<style id="auto-back-nav-style">\n'
    '#auto-back-nav{position:sticky;top:0;z-index:999;'
    'background:rgba(249,250,251,.9);backdrop-filter:blur(8px);'
    '-webkit-backdrop-filter:blur(8px);border-bottom:1px solid #e5e7eb;'
    'display:flex;align-items:center;padding:0 20px;height:44px;}\n'
    '@media(prefers-color-scheme:dark){'
    '#auto-back-nav{background:rgba(13,17,23,.9);border-bottom-color:#2d333b;}}\n'
    '#auto-back-nav a{display:inline-flex;align-items:center;gap:6px;'
    'text-decoration:none;color:#4b5563;font-size:14px;font-weight:600;'
    'font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",'
    '"Hiragino Sans GB","Microsoft YaHei",Roboto,Arial,sans-serif;}\n'
    '@media(prefers-color-scheme:dark){#auto-back-nav a{color:#9da7b3;}}\n'
    '</style>\n'
    '<nav id="auto-back-nav">\n'
    '  <a href="index.html">\n'
    '    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"'
    ' stroke="currentColor" stroke-width="2.4" stroke-linecap="round"'
    ' stroke-linejoin="round">'
    '<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>\n'
    '    暑假成长加油站\n'
    '  </a>\n'
    '</nav>'
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_title(html_path: Path) -> str:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else html_path.stem


def extract_meta_description(html_path: Path) -> str:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
        text, re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def parse_filename(name: str):
    """
    Return (grade_num, subject_slug, extra) for known patterns, else (None, None, None).
    Patterns handled:
      gradeN-subject.html
      gradeN-subject-extra.html
      gN-subject.html
      gN-subject-extra.html
    """
    m = re.match(r"(?:grade|g)(\d+)-([a-z]+)(?:-(.+))?\.html$", name, re.IGNORECASE)
    if m:
        return int(m.group(1)), m.group(2).lower(), m.group(3)
    return None, None, None


def collect_pages() -> list[dict]:
    pages = []
    for f in sorted(ROOT.glob("*.html")):
        if f.name == "index.html":
            continue
        grade_num, subject_slug, extra = parse_filename(f.name)
        title = extract_title(f)
        description = extract_meta_description(f)
        pages.append(
            dict(
                file=f.name,
                grade_num=grade_num,
                subject_slug=subject_slug,
                extra=extra,
                title=title,
                description=description,
            )
        )
    # Graded pages first (sorted by grade then filename), ungrouped pages last
    pages.sort(key=lambda p: (0 if p["grade_num"] else 1, p["grade_num"] or 0, p["file"]))
    return pages


# ---------------------------------------------------------------------------
# Sentinel-based replace
# ---------------------------------------------------------------------------

def replace_between(text: str, start: str, end: str, new_content: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{new_content}\n{end}"
    new_text, n = pattern.subn(replacement, text)
    if not n:
        raise ValueError(f"Sentinel markers not found: {start!r} … {end!r}")
    return new_text


# ---------------------------------------------------------------------------
# README.md generators
# ---------------------------------------------------------------------------

def gen_readme_table(pages: list[dict]) -> str:
    lines = ["| 页面 | 在线地址 |", "|---|---|"]
    for p in pages:
        url = f"https://beupgo.github.io/{p['file']}"
        lines.append(f"| {p['title']} | {url} |")
    lines.append("| 导航首页 | https://beupgo.github.io/ |")
    return "\n".join(lines)


def gen_readme_files(pages: list[dict]) -> str:
    lines = ["```", "."]
    lines.append("├─ index.html      # 导航首页")
    for i, p in enumerate(pages):
        prefix = "└─" if i == len(pages) - 1 else "├─"
        lines.append(f"{prefix} {p['file']}  # {p['title']}")
    lines.append("└─ README.md")
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# index.html card generator
# ---------------------------------------------------------------------------

def gen_card(p: dict) -> str:
    grade_num = p["grade_num"]
    title = p["title"]
    description = p["description"] or title
    short_title = title.split("·")[0].strip() if "·" in title else title

    if grade_num:
        grade_zh = GRADE_NAMES_ZH.get(grade_num, f"{grade_num}年级")
        subject_zh = SUBJECT_NAMES_ZH.get(p["subject_slug"] or "", "")
        grade_en = f"GRADE {grade_num}"
        if p["subject_slug"]:
            grade_en += f" · {p['subject_slug'].upper()}"
        icon = str(grade_num)
        h2 = short_title if p["extra"] else (grade_zh + subject_zh if subject_zh else grade_zh)
    else:
        grade_en = p["file"].replace(".html", "").upper()
        icon = short_title[0] if short_title else "?"
        h2 = short_title

    return (
        f'    <a class="card" href="{p["file"]}">\n'
        f'      <div class="top">\n'
        f'        <div class="icon">{icon}</div>\n'
        f'        <div>\n'
        f'          <h2>{h2}</h2>\n'
        f'          <div class="grade-en">{grade_en}</div>\n'
        f'        </div>\n'
        f'      </div>\n'
        f'      <p class="desc">{description}</p>\n'
        f'      <span class="go">开始学习\n'
        f'        {ARROW_SVG}\n'
        f'      </span>\n'
        f'    </a>'
    )


def gen_cards(pages: list[dict]) -> str:
    return "\n\n".join(gen_card(p) for p in pages)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def update_readme(pages: list[dict]) -> bool:
    path = ROOT / "README.md"
    original = path.read_text(encoding="utf-8")
    updated = original
    updated = replace_between(updated, "<!-- AUTO-TABLE-START -->", "<!-- AUTO-TABLE-END -->", gen_readme_table(pages))
    updated = replace_between(updated, "<!-- AUTO-FILES-START -->", "<!-- AUTO-FILES-END -->", gen_readme_files(pages))
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print("README.md updated.")
        return True
    print("README.md unchanged.")
    return False


def update_index(pages: list[dict]) -> bool:
    path = ROOT / "index.html"
    original = path.read_text(encoding="utf-8")
    updated = replace_between(original, "<!-- AUTO-CARDS-START -->", "<!-- AUTO-CARDS-END -->", gen_cards(pages))
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print("index.html updated.")
        return True
    print("index.html unchanged.")
    return False


def update_subpage_back_nav(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    if BACK_NAV_START in original:
        updated = replace_between(original, BACK_NAV_START, BACK_NAV_END, BACK_NAV_HTML)
    else:
        # First run: inject sentinel block right after <body ...>
        nav_block = f"{BACK_NAV_START}\n{BACK_NAV_HTML}\n{BACK_NAV_END}"
        updated = re.sub(
            r'(<body[^>]*>)',
            lambda m: m.group(0) + "\n" + nav_block,
            original,
            count=1,
        )
        if updated == original:
            print(f"  WARNING: could not inject back nav into {path.name} (no <body> found)")
            return False
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"  {path.name}: back nav injected/updated.")
        return True
    return False


def update_subpages(pages: list[dict]) -> bool:
    changed = False
    for p in pages:
        if update_subpage_back_nav(ROOT / p["file"]):
            changed = True
    return changed


def main() -> int:
    pages = collect_pages()
    print(f"Found {len(pages)} page(s): {[p['file'] for p in pages]}")
    changed_readme = update_readme(pages)
    changed_index = update_index(pages)
    changed_subpages = update_subpages(pages)
    return 0 if (changed_readme or changed_index or changed_subpages) else 1


if __name__ == "__main__":
    sys.exit(main())
