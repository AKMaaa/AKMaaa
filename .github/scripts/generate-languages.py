#!/usr/bin/env python3
"""Aggregate languages across public + private + org repos, emit SVG + skillicons row."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("PERSONAL_ACCESS_TOKEN")
USERNAME = os.environ.get("USERNAME") or os.environ.get("GITHUB_ACTOR") or "AKMaaa"
OUT_DIR = Path(os.environ.get("OUT_DIR") or "output")

# Hot pink / electric cyan — distinct from default metrics look
BG = "#0B0B10"
PANEL = "#12121A"
PINK = "#FF2D95"
CYAN = "#2DE2E6"
TEXT = "#F4F0F7"
MUTED = "#9A93A5"
BAR_TRACK = "#1E1E2A"

# GitHub linguist-ish colors (fallback hash if missing)
LANG_COLORS: dict[str, str] = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "Astro": "#ff5a03",
    "MDX": "#fcb32c",
    "Markdown": "#083fa1",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "Toml": "#9c4221",
    "SQL": "#e38c00",
    "GraphQL": "#e10098",
    "Dart": "#00B4AB",
    "Lua": "#000080",
    "R": "#198CE7",
    "Scala": "#c22d40",
    "Haskell": "#5e5086",
    "Elixir": "#6e4a7e",
    "Zig": "#ec915c",
    "Nix": "#7e7eff",
    "TeX": "#3D6117",
    "Jupyter Notebook": "#DA5B0B",
}

# skillicons / simple slug map
SKILLICON: dict[str, str] = {
    "TypeScript": "ts",
    "JavaScript": "js",
    "Python": "py",
    "Java": "java",
    "Go": "go",
    "Rust": "rust",
    "C": "c",
    "C++": "cpp",
    "C#": "cs",
    "Swift": "swift",
    "Kotlin": "kotlin",
    "Ruby": "ruby",
    "PHP": "php",
    "HTML": "html",
    "CSS": "css",
    "SCSS": "sass",
    "Vue": "vue",
    "Svelte": "svelte",
    "Shell": "bash",
    "Dockerfile": "docker",
    "Astro": "astro",
    "Markdown": "md",
    "SQL": "postgres",
    "GraphQL": "graphql",
    "Dart": "dart",
    "Lua": "lua",
    "R": "r",
    "Scala": "scala",
    "Haskell": "haskell",
    "Elixir": "elixir",
    "Zig": "zig",
    "Nix": "nix",
}


def api(url: str) -> object:
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN / PERSONAL_ACCESS_TOKEN is required")
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AKMaaa-language-spectrum",
        },
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as res:
        return json.loads(res.read().decode())


def paged(url: str) -> list:
    items: list = []
    page = 1
    while True:
        sep = "&" if "?" in url else "?"
        chunk = api(f"{url}{sep}per_page=100&page={page}")
        if not isinstance(chunk, list) or not chunk:
            break
        items.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return items


def color_for(name: str) -> str:
    if name in LANG_COLORS:
        return LANG_COLORS[name]
    h = sum(ord(c) * (i + 1) for i, c in enumerate(name)) % 360
    return f"hsl({h} 72% 58%)"


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def collect_languages() -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    repos = paged(
        "https://api.github.com/user/repos?affiliation=owner,collaborator,organization_member&sort=updated"
    )
    print(f"repos scanned: {len(repos)}")
    for repo in repos:
        if repo.get("fork"):
            continue
        full = repo["full_name"]
        try:
            langs = api(f"https://api.github.com/repos/{full}/languages")
        except urllib.error.HTTPError as exc:
            print(f"skip {full}: {exc}")
            continue
        if not isinstance(langs, dict):
            continue
        for lang, bytes_count in langs.items():
            totals[lang] += int(bytes_count)
    return dict(totals)


def render_svg(totals: dict[str, int]) -> str:
    """Compact 2-column spectrum — still lists every language."""
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in ranked) or 1
    rows = ranked

    cols = 2
    row_h = 22
    pad_x = 20
    pad_top = 56
    width = 920
    col_w = (width - pad_x * 2) // cols
    n_rows = (len(rows) + cols - 1) // cols
    height = pad_top + 12 + n_rows * row_h + 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Language spectrum for {USERNAME}">',
        f'<rect width="100%" height="100%" rx="14" fill="{BG}"/>',
        f'<rect x="10" y="10" width="{width-20}" height="{height-20}" rx="10" fill="{PANEL}" stroke="{PINK}" stroke-opacity="0.35"/>',
        f'<text x="{pad_x}" y="34" fill="{PINK}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" font-weight="700">LANGUAGE SPECTRUM</text>',
        f'<text x="{width - pad_x}" y="34" text-anchor="end" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">{escape(USERNAME)} · private + org · {len(rows)} langs</text>',
    ]

    for i, (name, bytes_count) in enumerate(rows):
        col = i // n_rows
        row = i % n_rows
        x0 = pad_x + col * col_w
        y = pad_top + row * row_h
        pct = bytes_count / total * 100
        fill = color_for(name)
        abbrev = escape((name[:2] if len(name) > 1 else name).upper())
        glyph = 16
        label_x = x0 + glyph + 6
        bar_x = x0 + 118
        bar_w = col_w - 168
        pct_x = x0 + col_w - 12
        filled = max(3, bar_w * (bytes_count / total))

        parts.append(
            f'<rect x="{x0}" y="{y + 2}" width="{glyph}" height="{glyph}" rx="4" fill="{fill}"/>'
        )
        parts.append(
            f'<text x="{x0 + glyph/2}" y="{y + 13}" text-anchor="middle" fill="#0B0B10" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8" font-weight="700">{abbrev}</text>'
        )
        # Truncate long names so two columns stay readable
        shown = name if len(name) <= 12 else name[:11] + "…"
        parts.append(
            f'<text x="{label_x}" y="{y + 14}" fill="{TEXT}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">{escape(shown)}</text>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 5}" width="{bar_w}" height="8" rx="4" fill="{BAR_TRACK}"/>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 5}" width="{filled:.2f}" height="8" rx="4" fill="{fill}"/>'
        )
        parts.append(
            f'<text x="{pct_x}" y="{y + 14}" text-anchor="end" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" font-weight="700">{pct:.1f}%</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def render_skillicons(totals: dict[str, int]) -> str:
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    icons = []
    for name, _ in ranked:
        slug = SKILLICON.get(name)
        if slug and slug not in icons:
            icons.append(slug)
    if not icons:
        return ""
    # skillicons caps URL length; chunk if needed
    joined = ",".join(icons)
    return f"https://skillicons.dev/icons?i={joined}&perline=12"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    totals = collect_languages()
    if not totals:
        raise SystemExit("no language data found")

    svg = render_svg(totals)
    svg_path = OUT_DIR / "languages.svg"
    svg_path.write_text(svg, encoding="utf-8")
    print(f"wrote {svg_path}")

    icons_url = render_skillicons(totals)
    meta = {
        "username": USERNAME,
        "languages": [
            {"name": n, "bytes": b, "percent": round(b / sum(totals.values()) * 100, 2)}
            for n, b in sorted(totals.items(), key=lambda x: x[1], reverse=True)
        ],
        "skillicons": icons_url,
    }
    meta_path = OUT_DIR / "languages.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {meta_path}")
    (OUT_DIR / "skillicons.url").write_text((icons_url or "") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
