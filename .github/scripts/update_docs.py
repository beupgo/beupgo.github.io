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
import subprocess
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

SUBJECT_ORDER = ["math", "english", "chinese", "other"]

SUBJECT_SECTION_META = {
    "math": {
        "title": "数学",
        "description": "分数、方程、几何、奥数等数学页面集中查看。",
    },
    "english": {
        "title": "英语",
        "description": "单词、句型、时态、介词与综合练习统一整理。",
    },
    "chinese": {
        "title": "语文",
        "description": "聚合当前语文写作与作文相关页面。",
    },
    "other": {
        "title": "其他",
        "description": "暂未识别学科的页面。",
    },
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


def normalize_display_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s*\|\s*小学(?:数学|英语|语文)\s*$", "", title)
    return title.strip()


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


def infer_subject(file_name: str, title: str, description: str, subject_slug: str | None) -> str:
    if subject_slug in SUBJECT_NAMES_ZH:
        return subject_slug

    haystack = " ".join(filter(None, [file_name, title, description, subject_slug])).lower()

    keyword_groups = [
        ("english", [
            "english", "vocabulary", "collocation", "sentence", "tense", "preposition",
            "英语", "单词", "词汇", "词根", "词缀", "句型", "句子", "时态", "介词", "搭配",
        ]),
        ("chinese", [
            "chinese", "语文", "作文", "写作", "习作", "阅读",
        ]),
        ("math", [
            "math", "数学", "奥数", "方程", "分数", "通分", "因数", "倍数", "运算", "面积",
            "圆", "图形", "几何", "计算", "应用题",
        ]),
    ]
    for subject, keywords in keyword_groups:
        if any(keyword in haystack for keyword in keywords):
            return subject
    return "other"


def sort_key_within_subject(page: dict):
    return (0 if page["grade_num"] else 1, page["grade_num"] or 99, page["display_title"], page["file"])


def group_pages_by_subject(pages: list[dict]) -> dict[str, list[dict]]:
    grouped = {subject: [] for subject in SUBJECT_ORDER}
    for page in pages:
        grouped.setdefault(page["inferred_subject"], []).append(page)
    for subject, items in grouped.items():
        grouped[subject] = sorted(items, key=sort_key_within_subject)
    return grouped


def collect_pages() -> list[dict]:
    pages = []
    for f in sorted(ROOT.glob("*.html")):
        if f.name == "index.html":
            continue
        grade_num, subject_slug, extra = parse_filename(f.name)
        title = extract_title(f)
        description = extract_meta_description(f)
        display_title = normalize_display_title(title) or f.stem
        inferred_subject = infer_subject(f.name, title, description, subject_slug)
        updated_ts, updated_at = get_git_last_updated(f.name)
        pages.append(
            dict(
                file=f.name,
                grade_num=grade_num,
                subject_slug=subject_slug,
                extra=extra,
                title=title,
                display_title=display_title,
                description=description,
                inferred_subject=inferred_subject,
                updated_ts=updated_ts,
                updated_at=updated_at,
            )
        )
    # Graded pages first (sorted by grade then filename), ungrouped pages last
    pages.sort(key=lambda p: (0 if p["grade_num"] else 1, p["grade_num"] or 0, p["file"]))
    return pages


def get_git_last_updated(filename: str) -> tuple[int, str]:
    try:
        ts = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--format=%ct", "--", filename],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        at = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--date=format:%Y-%m-%d %H:%M", "--format=%cd", "--", filename],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return (int(ts), at) if ts and at else (0, "")
    except Exception:
        return 0, ""


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
    grouped = group_pages_by_subject(pages)
    lines = []
    for subject in SUBJECT_ORDER:
        items = grouped.get(subject, [])
        if not items or subject == "other":
            continue
        lines.append(f"### {SUBJECT_NAMES_ZH[subject]}")
        for p in items:
            url = f"https://beupgo.github.io/{p['file']}"
            lines.append(f"- [{p['display_title']}]({url})")
        lines.append("")
    if grouped.get("other"):
        lines.append("### 其他")
        for p in grouped["other"]:
            url = f"https://beupgo.github.io/{p['file']}"
            lines.append(f"- [{p['display_title']}]({url})")
        lines.append("")
    lines.append("- [导航首页](https://beupgo.github.io/)")
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
    title = p["display_title"]
    description = p["description"] or title
    subject_zh = SUBJECT_NAMES_ZH.get(p["inferred_subject"], "")

    if grade_num:
        grade_zh = GRADE_NAMES_ZH.get(grade_num, f"{grade_num}年级")
        grade_en = f"{grade_zh} · {subject_zh}" if subject_zh else grade_zh
        icon = str(grade_num)
    else:
        grade_en = f"{subject_zh}专题" if subject_zh else "专题页"
        icon = subject_zh[:1] if subject_zh else (title[0] if title else "?")

    return (
        f'    <a class="card" href="{p["file"]}">\n'
        f'      <div class="top">\n'
        f'        <div class="icon">{icon}</div>\n'
        f'        <div>\n'
        f'          <h3>{title}</h3>\n'
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
    grouped = group_pages_by_subject(pages)
    sections = []
    for subject in SUBJECT_ORDER:
        items = grouped.get(subject, [])
        if not items or subject == "other":
            continue
        meta = SUBJECT_SECTION_META[subject]
        cards = "\n\n".join(gen_card(p) for p in items)
        sections.append(
            "    <section class=\"subject-section\">\n"
            "      <div class=\"subject-head\">\n"
            f"        <div><h2>{meta['title']}</h2><p>{meta['description']}</p></div>\n"
            f"        <span class=\"subject-count\">共 {len(items)} 个页面</span>\n"
            "      </div>\n"
            "      <div class=\"subject-grid\">\n"
            f"{cards}\n"
            "      </div>\n"
            "    </section>"
        )
    if grouped.get("other"):
        meta = SUBJECT_SECTION_META["other"]
        cards = "\n\n".join(gen_card(p) for p in grouped["other"])
        sections.append(
            "    <section class=\"subject-section\">\n"
            "      <div class=\"subject-head\">\n"
            f"        <div><h2>{meta['title']}</h2><p>{meta['description']}</p></div>\n"
            f"        <span class=\"subject-count\">共 {len(grouped['other'])} 个页面</span>\n"
            "      </div>\n"
            "      <div class=\"subject-grid\">\n"
            f"{cards}\n"
            "      </div>\n"
            "    </section>"
        )
    return "\n\n".join(sections)


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
