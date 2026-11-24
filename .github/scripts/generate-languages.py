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

# Litty cyan × Badhop cream × brand pink — RPG / pixel night board
BG = "#07070C"
PANEL = "#101018"
PINK = "#FF2D95"
CYAN = "#2DE2E6"
CREAM = "#E8E0D0"
TEXT = "#F4F0F7"
MUTED = "#9A93A5"
BAR_TRACK = "#1E1E2A"
SLOT = "#0B0B12"

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


# ぶき = hardware you fight with (manual — GitHub can't see your desk)
HARDWARE_WEAPONS: list[tuple[str, str, int]] = [
    ("MacBook Pro", "main rig", 99),
    ("Windows", "dual boot", 70),
    ("Linux", "server / CLI", 85),
]

# よろい = stack that protects / carries production work
ARMOR_LANG_PRIORITY = [
    "TypeScript",
    "JavaScript",
    "PHP",
    "Python",
    "Vue",
    "Go",
    "Java",
    "Dockerfile",
    "Astro",
    "Swift",
    "Kotlin",
]

# じゅもん = AI APIs + research magic (always show research identity)
RESEARCH_SPELLS: list[tuple[str, str, int]] = [
    ("Agent Design", "research core", 90),
    ("AI Literacy", "workshop magic", 88),
    ("Discussion Agents", "learning UX", 86),
]


def build_loadout(
    toolkit: dict[str, dict], lang_totals: dict[str, int]
) -> dict[str, list[tuple[str, str, int]]]:
    """
    ぶき   = hardware
    よろい = languages / frameworks from repos
    じゅもん = AI SDKs + research spells
    """
    weapons = [(n, sub, lv) for n, sub, lv in HARDWARE_WEAPONS]

    armor: list[tuple[str, str, int]] = []
    total_bytes = sum(lang_totals.values()) or 1
    # prefer curated order, then fill by size
    seen = set()
    for name in ARMOR_LANG_PRIORITY:
        if name in lang_totals and lang_totals[name] > 0:
            pct = max(1, round(100 * lang_totals[name] / total_bytes))
            armor.append((name, f"{pct}% of code", min(99, max(10, pct * 2))))
            seen.add(name)
    for name, b in sorted(lang_totals.items(), key=lambda x: x[1], reverse=True):
        if name in seen or name in ("HTML", "CSS", "SCSS", "Markdown", "TeX", "Hack"):
            continue
        if len(armor) >= 4:
            break
        pct = max(1, round(100 * b / total_bytes))
        armor.append((name, f"{pct}% of code", min(99, max(10, pct * 2))))
    armor.sort(key=lambda x: x[2], reverse=True)

    spells: list[tuple[str, str, int]] = []
    for label, data in sorted(
        toolkit.items(), key=lambda x: (x[1]["repos"], x[1]["hits"]), reverse=True
    ):
        spells.append((label, f'{data["repos"]} repos', min(99, 40 + data["repos"] * 15)))
    for name, sub, lv in RESEARCH_SPELLS:
        if len(spells) >= 4:
            break
        if all(name != s[0] for s in spells):
            spells.append((name, sub, lv))

    return {
        "WEAPON": weapons[:3],
        "ARMOR": armor[:3],
        "SKILL": spells[:3],
    }


def render_ai_toolkit_svg(
    toolkit: dict[str, dict], lang_totals: dict[str, int] | None = None
) -> str:
    """DQ command window: hardware / stack / AI+research loadout."""
    width = 920
    height = 320
    buckets = build_loadout(toolkit, lang_totals or {})

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" shape-rendering="crispEdges" role="img" aria-label="RPG loadout inventory">',
        f'<rect width="100%" height="100%" fill="{BG}"/>',
        f'<rect x="6" y="6" width="{width-12}" height="{height-12}" fill="{CREAM}"/>',
        f'<rect x="12" y="12" width="{width-24}" height="{height-24}" fill="{BG}"/>',
        f'<rect x="18" y="18" width="{width-36}" height="{height-36}" fill="{PANEL}"/>',
        f'<text x="36" y="44" fill="{CREAM}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="18" font-weight="700">どうぐ / LOADOUT</text>',
        f'<text x="{width-36}" y="44" text-anchor="end" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">ぶき=ハード · よろい=スタック · じゅもん=AI/研究</text>',
    ]

    col_meta = [
        ("ぶき", 36, PINK, "HARDWARE"),
        ("よろい", 328, CYAN, "STACK"),
        ("じゅもん", 620, CREAM, "AI / MAGIC"),
    ]
    kind_map = {"ぶき": "WEAPON", "よろい": "ARMOR", "じゅもん": "SKILL"}
    for title, x0, accent, eng in col_meta:
        kind = kind_map[title]
        parts.append(f'<rect x="{x0}" y="58" width="264" height="238" fill="{CREAM}"/>')
        parts.append(f'<rect x="{x0+6}" y="64" width="252" height="226" fill="{SLOT}"/>')
        parts.append(f'<rect x="{x0+6}" y="64" width="252" height="32" fill="{accent}"/>')
        parts.append(
            f'<text x="{x0 + 132}" y="86" text-anchor="middle" fill="{BG}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="16" font-weight="700">{title}</text>'
        )
        parts.append(
            f'<text x="{x0 + 132}" y="112" text-anchor="middle" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">{eng}</text>'
        )
        items = buckets.get(kind, [])[:3]
        for i, (label, sub, lv) in enumerate(items):
            y = 124 + i * 50
            parts.append(f'<rect x="{x0 + 18}" y="{y}" width="228" height="42" fill="{CREAM}"/>')
            parts.append(f'<rect x="{x0 + 22}" y="{y+4}" width="220" height="34" fill="#14141E"/>')
            parts.append(f'<rect x="{x0 + 28}" y="{y+11}" width="20" height="20" fill="{accent}"/>')
            short = label if len(label) <= 16 else label[:15] + "…"
            parts.append(
                f'<text x="{x0 + 56}" y="{y + 18}" fill="{TEXT}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="700">{escape(short)}</text>'
            )
            parts.append(
                f'<text x="{x0 + 56}" y="{y + 32}" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">LV{lv} · {escape(sub)}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def _parse_commit_hour(iso: str) -> int | None:
    # author date like 2026-01-02T15:04:05+09:00 or Z
    if "T" not in iso:
        return None
    try:
        from datetime import datetime, timezone, timedelta

        jst = timezone(timedelta(hours=9))
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(jst)
        return dt.hour
    except Exception:
        return None


def collect_commit_hours(repos: list) -> dict[int, int]:
    """Hour-of-day histogram in Asia/Tokyo from recent authored commits."""
    hours: dict[int, int] = defaultdict(int)
    scan = repos[:35]
    print(f"commit-hour scan: {len(scan)} repos")
    for repo in scan:
        full = repo["full_name"]
        try:
            commits = api(
                f"https://api.github.com/repos/{full}/commits?author={urllib.parse.quote(USERNAME)}&per_page=40"
            )
        except urllib.error.HTTPError as exc:
            print(f"skip commits {full}: {exc}")
            continue
        if not isinstance(commits, list):
            continue
        for c in commits:
            try:
                iso = c["commit"]["author"]["date"]
            except (KeyError, TypeError):
                continue
            h = _parse_commit_hour(iso)
            if h is not None:
                hours[h] += 1
    return dict(hours)


def render_hour_ring_svg(hours: dict[int, int]) -> str:
    import math

    width, height = 420, 420
    cx, cy, r_out, r_in = 210, 220, 150, 88
    total = sum(hours.values()) or 1
    peak_h = max(range(24), key=lambda h: hours.get(h, 0)) if hours else 0
    peak_n = hours.get(peak_h, 0)
    night = sum(hours.get(h, 0) for h in list(range(0, 6)) + list(range(22, 24)))
    night_pct = round(100 * night / total)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" shape-rendering="crispEdges" role="img" aria-label="Commit hour ring">',
        f'<rect width="100%" height="100%" fill="{BG}"/>',
        f'<rect x="6" y="6" width="{width-12}" height="{height-12}" fill="{CREAM}"/>',
        f'<rect x="12" y="12" width="{width-24}" height="{height-24}" fill="{BG}"/>',
        f'<rect x="18" y="18" width="{width-36}" height="{height-36}" fill="{PANEL}"/>',
        f'<text x="32" y="44" fill="{CREAM}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="16" font-weight="700">じかんたい</text>',
        f'<text x="{width-32}" y="44" text-anchor="end" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">JST COMMIT RING</text>',
    ]

    max_h = max(hours.values()) if hours else 1
    for h in range(24):
        start = -math.pi / 2 + (h / 24) * 2 * math.pi
        end = -math.pi / 2 + ((h + 1) / 24) * 2 * math.pi
        val = hours.get(h, 0)
        t = val / max_h if max_h else 0
        # night hours lean pink, day lean cyan
        fill = PINK if h >= 22 or h < 6 else CYAN
        if t == 0:
            fill = "#22222C"
            alpha = 0.55
            rr = r_in + 18
        else:
            alpha = 0.35 + 0.65 * t
            rr = r_in + 18 + (r_out - r_in - 18) * t
        # wedge as path
        x1, y1 = cx + r_in * math.cos(start), cy + r_in * math.sin(start)
        x2, y2 = cx + rr * math.cos(start), cy + rr * math.sin(start)
        x3, y3 = cx + rr * math.cos(end), cy + rr * math.sin(end)
        x4, y4 = cx + r_in * math.cos(end), cy + r_in * math.sin(end)
        large = 0
        parts.append(
            f'<path d="M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f} A{rr:.2f},{rr:.2f} 0 {large} 1 {x3:.2f},{y3:.2f} L{x4:.2f},{y4:.2f} A{r_in:.2f},{r_in:.2f} 0 {large} 0 {x1:.2f},{y1:.2f} Z" fill="{fill}" fill-opacity="{alpha:.2f}" stroke="{BG}" stroke-width="1"/>'
        )

    # labels N/E/S/W
    for label, ang in (("0", -math.pi / 2), ("6", 0), ("12", math.pi / 2), ("18", math.pi)):
        lx = cx + (r_out + 18) * math.cos(ang)
        ly = cy + (r_out + 18) * math.sin(ang) + 4
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" fill="{MUTED}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">{label}</text>'
        )

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_in-6}" fill="{SLOT}" stroke="{CREAM}" stroke-width="2"/>')
    parts.append(
        f'<text x="{cx}" y="{cy - 18}" text-anchor="middle" fill="{PINK}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="700">さいこう</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" fill="{TEXT}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="28" font-weight="700">{peak_h:02d}:00</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy + 28}" text-anchor="middle" fill="{CYAN}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">{peak_n} commits</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy + 46}" text-anchor="middle" fill="{CREAM}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11">よる {night_pct}%</text>'
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
    ai_svg = render_ai_toolkit_svg(toolkit, totals)
    ai_path = OUT_DIR / "ai-radar.svg"
    ai_path.write_text(ai_svg, encoding="utf-8")
    print(f"wrote {ai_path} ({len(toolkit)} signals)")

    hour_hist = collect_commit_hours(repos)
    hour_svg = render_hour_ring_svg(hour_hist)
    hour_path = OUT_DIR / "hour-ring.svg"
    hour_path.write_text(hour_svg, encoding="utf-8")
    print(f"wrote {hour_path} ({sum(hour_hist.values())} commits sampled)")

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
        "commit_hours_jst": {str(k): v for k, v in sorted(hour_hist.items())},
        "skillicons": icons_url,
        "note": "YAML/GitHub Actions often under-counted by the languages API",
    }
    meta_path = OUT_DIR / "languages.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {meta_path}")
    (OUT_DIR / "skillicons.url").write_text((icons_url or "") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
