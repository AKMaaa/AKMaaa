#!/usr/bin/env python3
"""Aggregate languages across public + private + org repos, emit SVG + skillicons row."""

from __future__ import annotations

import base64
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

# Primary domain per language (exclusive — clean domain %)
DOMAIN_OF: dict[str, str] = {
    "JavaScript": "Frontend",
    "TypeScript": "Frontend",
    "HTML": "Frontend",
    "CSS": "Frontend",
    "SCSS": "Frontend",
    "Sass": "Frontend",
    "Less": "Frontend",
    "Stylus": "Frontend",
    "Vue": "Frontend",
    "Svelte": "Frontend",
    "Astro": "Frontend",
    "MDX": "Frontend",
    "Handlebars": "Frontend",
    "PHP": "Backend",
    "Python": "Backend",
    "Ruby": "Backend",
    "Go": "Backend",
    "Java": "Backend",
    "C#": "Backend",
    "Perl": "Backend",
    "Hack": "Backend",
    "Elixir": "Backend",
    "Scala": "Backend",
    "Dart": "Mobile",
    "Kotlin": "Mobile",
    "Swift": "Mobile",
    "Objective-C": "Mobile",
    "Dockerfile": "CI / DevOps",
    "Shell": "CI / DevOps",
    "PowerShell": "CI / DevOps",
    "Makefile": "CI / DevOps",
    "CMake": "CI / DevOps",
    "YAML": "CI / DevOps",
    "YML": "CI / DevOps",
    "Nix": "CI / DevOps",
    "Jupyter Notebook": "Data / ML",
    "R": "Data / ML",
    "MATLAB": "Data / ML",
    "PLpgSQL": "Data / ML",
    "SQL": "Data / ML",
    "C": "Systems",
    "C++": "Systems",
    "Rust": "Systems",
    "Zig": "Systems",
    "TeX": "Research / Docs",
    "Markdown": "Research / Docs",
    "Processing": "Creative",
    "Prolog": "Other",
}

DOMAIN_COLORS: dict[str, str] = {
    "Frontend": "#38BDF8",
    "Backend": "#FF2D95",
    "Mobile": "#A855F7",
    "CI / DevOps": "#22C55E",
    "Data / ML": "#FF9F1C",
    "Systems": "#2DE2E6",
    "Research / Docs": "#EAB308",
    "Creative": "#F472B6",
    "Other": "#9A93A5",
}

DOMAIN_GLYPH: dict[str, str] = {
    "Frontend": "FE",
    "Backend": "BE",
    "Mobile": "MO",
    "CI / DevOps": "CI",
    "Data / ML": "ML",
    "Systems": "SY",
    "Research / Docs": "RD",
    "Creative": "CR",
    "Other": "OT",
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
    "YAML": "githubactions",
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
    "Kotlin": "kotlin",
}


def domain_totals(lang_totals: dict[str, int]) -> dict[str, int]:
    domains: dict[str, int] = defaultdict(int)
    for name, bytes_count in lang_totals.items():
        domain = DOMAIN_OF.get(name, "Other")
        domains[domain] += bytes_count
    return dict(domains)


def render_domains_svg(lang_totals: dict[str, int]) -> str:
    domains = domain_totals(lang_totals)
    ranked = sorted(domains.items(), key=lambda x: x[1], reverse=True)
    total = sum(v for _, v in ranked) or 1

    row_h = 36
    pad_x = 24
    pad_top = 64
    width = 920
    height = pad_top + 16 + len(ranked) * row_h + 28
    bar_x = 200
    bar_w = 560
    pct_x = 880

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Domain spectrum for {USERNAME}">',
        f'<rect width="100%" height="100%" rx="14" fill="{BG}"/>',
        f'<rect x="10" y="10" width="{width-20}" height="{height-20}" rx="10" fill="{PANEL}" stroke="{CYAN}" stroke-opacity="0.4"/>',
        f'<text x="{pad_x}" y="36" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" font-weight="700">DOMAIN SPECTRUM</text>',
        f'<text x="{width - pad_x}" y="36" text-anchor="end" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">Frontend · Backend · Mobile · CI · Data…</text>',
        f'<text x="{pad_x}" y="52" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">mapped from language bytes · YAML/CI often under-counted by GitHub linguist</text>',
    ]

    for i, (name, bytes_count) in enumerate(ranked):
        y = pad_top + i * row_h
        pct = bytes_count / total * 100
        fill = DOMAIN_COLORS.get(name, "#9A93A5")
        glyph = DOMAIN_GLYPH.get(name, "??")
        filled = max(4, bar_w * (bytes_count / total))
        # member languages (top 3 in this domain)
        members = [
            lang
            for lang, _ in sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)
            if DOMAIN_OF.get(lang, "Other") == name
        ][:4]
        member_txt = escape(", ".join(members)) if members else ""

        parts.append(
            f'<rect x="{pad_x}" y="{y + 4}" width="22" height="22" rx="6" fill="{fill}"/>'
        )
        parts.append(
            f'<text x="{pad_x + 11}" y="{y + 19}" text-anchor="middle" fill="#0B0B10" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8" font-weight="700">{escape(glyph)}</text>'
        )
        parts.append(
            f'<text x="{pad_x + 30}" y="{y + 14}" fill="{TEXT}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">{escape(name)}</text>'
        )
        parts.append(
            f'<text x="{pad_x + 30}" y="{y + 28}" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9">{member_txt}</text>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 12}" width="{bar_w}" height="12" rx="6" fill="{BAR_TRACK}"/>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 12}" width="{filled:.2f}" height="12" rx="6" fill="{fill}"/>'
        )
        parts.append(
            f'<text x="{pct_x}" y="{y + 22}" text-anchor="end" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">{pct:.1f}%</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


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


# Detected via dependency manifests / common import strings
AI_SIGNALS: dict[str, list[str]] = {
    "Gemini": [
        "@google/generative-ai",
        "@google/genai",
        "google-generativeai",
        "google.generativeai",
        "generativelanguage.googleapis.com",
        "gemini-1.",
        "gemini-2.",
        "models/gemini",
    ],
    "OpenAI": [
        '"openai"',
        "'openai'",
        "openai>=",
        "openai==",
        "@openai/",
        "langchain-openai",
        "ChatOpenAI",
        "from openai",
        "import openai",
    ],
    "Claude / Anthropic": [
        "anthropic",
        "@anthropic-ai",
        "ChatAnthropic",
        "claude-3",
        "claude-sonnet",
    ],
    "LangChain": ["langchain", "@langchain/"],
    "LangGraph": ["langgraph", "@langchain/langgraph"],
    "Vercel AI SDK": ['"ai":', "'ai':", "@ai-sdk/", "from \"ai\"", "from 'ai'"],
    "LlamaIndex": ["llama-index", "llama_index", "llamaindex"],
    "Hugging Face": ["transformers", "huggingface_hub", "@huggingface/"],
    "Ollama": ["ollama", "langchain-ollama"],
    "Cohere": ["cohere", "@cohere"],
    "Mistral": ["mistralai", "@mistralai"],
}

MANIFEST_CANDIDATES = (
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "composer.json",
)


def list_repos() -> list:
    repos = paged(
        "https://api.github.com/user/repos?affiliation=owner,collaborator,organization_member&sort=updated"
    )
    return [r for r in repos if not r.get("fork")]


def collect_languages(repos: list) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    print(f"repos scanned: {len(repos)}")
    for repo in repos:
        full = repo["full_name"]
        try:
            langs = api(f"https://api.github.com/repos/{full}/languages")
        except urllib.error.HTTPError as exc:
            print(f"skip langs {full}: {exc}")
            continue
        if not isinstance(langs, dict):
            continue
        for lang, bytes_count in langs.items():
            totals[lang] += int(bytes_count)
    return dict(totals)


def fetch_text(full: str, path: str, branch: str) -> str | None:
    url = f"https://api.github.com/repos/{full}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(branch)}"
    try:
        data = api(url)
    except urllib.error.HTTPError:
        return None
    if not isinstance(data, dict) or data.get("encoding") != "base64":
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    except Exception:
        return None


def collect_ai_toolkit(repos: list) -> dict[str, dict]:
    """Return {label: {repos: int, hits: int}} for detected LLM / AI SDKs."""
    found: dict[str, dict] = {
        label: {"repos": set(), "hits": 0} for label in AI_SIGNALS
    }
    # Cap to keep Actions runtime / rate limits reasonable
    scan = repos[:80]
    print(f"ai toolkit scan: {len(scan)} repos")
    for repo in scan:
        full = repo["full_name"]
        branch = repo.get("default_branch") or "main"
        blob_parts: list[str] = []
        for path in MANIFEST_CANDIDATES:
            text = fetch_text(full, path, branch)
            if text:
                blob_parts.append(text.lower())
        if not blob_parts:
            continue
        blob = "\n".join(blob_parts)
        for label, needles in AI_SIGNALS.items():
            hit = False
            for needle in needles:
                if needle.lower() in blob:
                    found[label]["hits"] += 1
                    hit = True
            if hit:
                found[label]["repos"].add(full)

    out: dict[str, dict] = {}
    for label, data in found.items():
        if data["repos"]:
            out[label] = {"repos": len(data["repos"]), "hits": data["hits"]}
    return out


def render_ai_toolkit_svg(toolkit: dict[str, dict]) -> str:
    ranked = sorted(toolkit.items(), key=lambda x: (x[1]["repos"], x[1]["hits"]), reverse=True)
    width = 920
    if not ranked:
        height = 120
        return "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                f'<rect width="100%" height="100%" rx="14" fill="{BG}"/>',
                f'<rect x="10" y="10" width="{width-20}" height="{height-20}" rx="10" fill="{PANEL}" stroke="{PINK}" stroke-opacity="0.35"/>',
                f'<text x="28" y="48" fill="{PINK}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" font-weight="700">AI / LLM RADAR</text>',
                f'<text x="28" y="78" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12">no Gemini / OpenAI / LangChain signals in scanned manifests yet</text>',
                "</svg>",
            ]
        )

    pad_x = 24
    pad_top = 62
    row_h = 34
    height = pad_top + 12 + len(ranked) * row_h + 24
    max_repos = max(v["repos"] for _, v in ranked) or 1
    bar_x = 240
    bar_w = 520

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="AI LLM toolkit radar">',
        f'<rect width="100%" height="100%" rx="14" fill="{BG}"/>',
        f'<rect x="10" y="10" width="{width-20}" height="{height-20}" rx="10" fill="{PANEL}" stroke="{PINK}" stroke-opacity="0.45"/>',
        f'<text x="{pad_x}" y="36" fill="{PINK}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" font-weight="700">AI / LLM RADAR</text>',
        f'<text x="{width - pad_x}" y="36" text-anchor="end" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">deps + manifests · private/org included</text>',
        f'<text x="{pad_x}" y="52" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">Gemini · OpenAI · Claude · LangChain… scanned from package.json / requirements / pyproject</text>',
    ]

    palette = [PINK, CYAN, "#FF9F1C", "#A855F7", "#22C55E", "#38BDF8", "#F472B6", "#EAB308"]
    for i, (label, data) in enumerate(ranked):
        y = pad_top + i * row_h
        fill = palette[i % len(palette)]
        filled = max(8, bar_w * (data["repos"] / max_repos))
        parts.append(
            f'<text x="{pad_x}" y="{y + 18}" fill="{TEXT}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">{escape(label)}</text>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 8}" width="{bar_w}" height="12" rx="6" fill="{BAR_TRACK}"/>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 8}" width="{filled:.2f}" height="12" rx="6" fill="{fill}"/>'
        )
        parts.append(
            f'<text x="{width - pad_x}" y="{y + 18}" text-anchor="end" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12">{data["repos"]} repos</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


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
    repos = list_repos()
    totals = collect_languages(repos)
    if not totals:
        raise SystemExit("no language data found")

    svg = render_svg(totals)
    svg_path = OUT_DIR / "languages.svg"
    svg_path.write_text(svg, encoding="utf-8")
    print(f"wrote {svg_path}")

    domains_svg = render_domains_svg(totals)
    domains_path = OUT_DIR / "domains.svg"
    domains_path.write_text(domains_svg, encoding="utf-8")
    print(f"wrote {domains_path}")

    toolkit = collect_ai_toolkit(repos)
    ai_svg = render_ai_toolkit_svg(toolkit)
    ai_path = OUT_DIR / "ai-radar.svg"
    ai_path.write_text(ai_svg, encoding="utf-8")
    print(f"wrote {ai_path} ({len(toolkit)} signals)")

    icons_url = render_skillicons(totals)
    d_totals = domain_totals(totals)
    d_sum = sum(d_totals.values()) or 1
    meta = {
        "username": USERNAME,
        "languages": [
            {"name": n, "bytes": b, "percent": round(b / sum(totals.values()) * 100, 2)}
            for n, b in sorted(totals.items(), key=lambda x: x[1], reverse=True)
        ],
        "domains": [
            {"name": n, "bytes": b, "percent": round(b / d_sum * 100, 2)}
            for n, b in sorted(d_totals.items(), key=lambda x: x[1], reverse=True)
        ],
        "ai_toolkit": toolkit,
        "skillicons": icons_url,
        "note": "YAML/GitHub Actions often under-counted by the languages API",
    }
    meta_path = OUT_DIR / "languages.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {meta_path}")
    (OUT_DIR / "skillicons.url").write_text((icons_url or "") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
