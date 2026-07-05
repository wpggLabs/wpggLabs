#!/usr/bin/env python3
"""
Self-updating profile builder for github.com/wpggLabs.

Pulls live data from the GitHub API and regenerates:
  - assets/banner.svg   (PowerShell-terminal wordmark, Cascadia Code -> vector paths)
  - assets/langs.svg    (aggregated language bar across every repo the token can see)
  - README.md sections between  <!--X:START-->  /  <!--X:END-->  markers:
        BUILDS  STACK  STATS  UPDATED

Run locally:   GH_TOKEN=$(gh auth token) python scripts/build.py
Runs in CI via .github/workflows/profile.yml on a schedule.

Auth:
  * GITHUB_TOKEN (default in Actions) sees public repos + this repo.
  * A PAT in secret GH_PAT (repo scope) additionally folds *private* repos
    into the aggregate language bar and stats counts (never by name).
"""
import os
import sys
import json
import datetime
import urllib.request
import urllib.error
from collections import Counter
from mono import Mono

USER = "wpggLabs"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BOLD = os.path.join(ROOT, "assets", "fonts", "CascadiaCode-Bold.ttf")
PAT = os.environ.get("GH_PAT") or os.environ.get("GH_TOKEN")   # a *user* token (sees private repos)
TOKEN = PAT or os.environ.get("GITHUB_TOKEN")                  # any token (auth + rate limit)
HAVE_USER = bool(PAT)                                          # can we hit /user/repos?

# ── terminal palette (black & white, one whisper of green for the live prompt) ──
BG = "#0c0c0c"        # Windows Terminal default black
FG = "#f2f2f2"        # bright white text
DIM = "#8a8a8a"       # secondary grey
FAINT = "#3a3a3a"     # chrome lines
PROMPT = "#19c37d"    # subtle terminal-green prompt glyph
CURSOR = "#f2f2f2"

MARKUP = {"HTML", "CSS", "SCSS", "Vue", "Svelte"}  # excluded from the "languages" bar
LANG_COLOR = {
    "TypeScript": "#f2f2f2", "JavaScript": "#d0d0d0", "Python": "#b8b8b8",
    "Rust": "#9a9a9a", "PLpgSQL": "#7a7a7a", "Shell": "#6a6a6a",
    "Swift": "#8a8a8a", "Java": "#707070", "PowerShell": "#606060",
}
GREYS = ["#f2f2f2", "#c8c8c8", "#a0a0a0", "#7c7c7c", "#585858", "#404040"]

# language / topic -> (label, shields logo slug)
BADGE = {
    "typescript": ("TypeScript", "typescript"), "javascript": ("JavaScript", "javascript"),
    "python": ("Python", "python"), "rust": ("Rust", "rust"), "react": ("React", "react"),
    "tauri": ("Tauri", "tauri"), "electron": ("Electron", "electron"), "vite": ("Vite", "vite"),
    "cloudflare-workers": ("Cloudflare Workers", "cloudflare"), "node": ("Node.js", "nodedotjs"),
    "tailwindcss": ("Tailwind", "tailwindcss"), "pwa": ("PWA", "pwa"),
    "ffmpeg": ("FFmpeg", "ffmpeg"), "postgresql": ("PostgreSQL", "postgresql"),
    "durable-objects": ("Durable Objects", "cloudflare"), "manifest-v3": ("Manifest V3", "googlechrome"),
    "esbuild": ("esbuild", "esbuild"), "swift": ("Swift", "swift"),
}


def api(path):
    url = path if path.startswith("http") else f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "wpggLabs-profile-bot",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def all_repos():
    repos, page = [], 1
    while True:
        chunk = api(f"/user/repos?per_page=100&affiliation=owner&page={page}") if HAVE_USER \
            else api(f"/users/{USER}/repos?per_page=100&page={page}")
        if not chunk:
            break
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    return repos


# ─────────────────────────── data ───────────────────────────
def gather():
    repos = all_repos()
    lang_bytes = Counter()
    topics = Counter()
    public, private = [], 0
    stars = 0
    for r in repos:
        if r["name"] == USER:            # skip the profile repo itself
            continue
        stars += r.get("stargazers_count", 0)
        for t in (r.get("topics") or []):
            topics[t] += 1
        try:
            for lang, b in api(f"/repos/{USER}/{r['name']}/languages").items():
                lang_bytes[lang] += b
                topics[lang.lower()] += 1
        except Exception:
            pass
        if r["private"]:
            private += 1
        elif not r["fork"]:
            public.append(r)
    public.sort(key=lambda r: r["pushed_at"], reverse=True)
    return dict(repos=repos, lang_bytes=lang_bytes, topics=topics,
                public=public, private=private, stars=stars)


# ─────────────────────── svg: banner ───────────────────────
def banner(d):
    M = Mono(FONT_BOLD)
    W = 1200
    fs = 26                       # code font size
    cw = M.cw(fs)
    x = 40
    top = 108                     # first content baseline
    lh = 46                       # line height
    rows = []

    def put(cells, y):
        # cells: list of (text, color); laid out on the mono grid
        col = 0
        for text, color in cells:
            rows.append(f'<g fill="{color}">{M.line(text, fs, x + col * cw, y)}</g>')
            col += len(text)

    lines = [
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM), ("whoami", FG)],
        [("bootstrapper · full-stack builder · New York", DIM)],
        [("", FG)],
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM), ("Get-Focus", FG)],
        [("local-first desktop apps · browser extensions · streaming tools", DIM)],
        [("", FG)],
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM), ("Get-Manifesto", FG)],
        [("no accounts · no cloud lock-in · no telemetry · ship it yourself", DIM)],
        [("", FG)],
        [("PS", PROMPT), (" C:\\wpggLabs> ", DIM)],
    ]
    for i, cells in enumerate(lines):
        put(cells, top + i * lh)
    H = top + len(lines) * lh + 28

    # blinking block cursor after the final prompt
    cur_x = x + len("PS C:\\wpggLabs> ") * cw
    cur_y = top + (len(lines) - 1) * lh
    cursor = (f'<rect x="{cur_x:.1f}" y="{cur_y - fs + 4:.1f}" width="{cw*0.9:.1f}" height="{fs:.1f}" '
              f'fill="{CURSOR}"><animate attributeName="opacity" values="1;1;0;0" dur="1.06s" '
              f'repeatCount="indefinite"/></rect>')

    title = M.line("Windows PowerShell", 20, 118, 48)
    dots = "".join(f'<circle cx="{40+i*26}" cy="41" r="7" fill="{c}"/>'
                   for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]))
    ctrls = M.line("—  ▢  ✕", 20, W - 150, 48)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="wpggLabs — PowerShell">
<defs><clipPath id="w"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>
<g clip-path="url(#w)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="72" fill="#161616"/>
  <line x1="0" y1="72" x2="{W}" y2="72" stroke="{FAINT}" stroke-width="1"/>
  {dots}
  <g fill="{DIM}">{title}</g>
  <g fill="{DIM}">{ctrls}</g>
  {''.join(rows)}
  {cursor}
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FAINT}" stroke-width="1"/>
</g>
</svg>'''


# ─────────────────────── svg: language bar ───────────────────────
def langs_svg(d):
    M = Mono(FONT_BOLD)
    items = [(k, v) for k, v in d["lang_bytes"].most_common() if k not in MARKUP]
    top = items[:5]
    other = sum(v for _, v in items[5:])
    if other:
        top.append(("Other", other))
    tot = sum(v for _, v in top) or 1
    W, H = 1200, 150
    x0, x1 = 40, 1160
    barw = x1 - x0
    barY, barH = 60, 22
    segs, cx = [], x0
    for i, (name, v) in enumerate(top):
        w = barw * v / tot
        col = LANG_COLOR.get(name, GREYS[min(i, len(GREYS) - 1)])
        segs.append(f'<rect x="{cx:.2f}" y="{barY}" width="{max(w-3,3):.2f}" height="{barH}" fill="{col}"/>')
        cx += w
    # legend
    leg, lx = [], 40
    for i, (name, v) in enumerate(top):
        col = LANG_COLOR.get(name, GREYS[min(i, len(GREYS) - 1)])
        pct = f"{100*v/tot:.1f}%"
        leg.append(f'<rect x="{lx}" y="{112}" width="11" height="11" fill="{col}"/>')
        leg.append(f'<g fill="{FG}">{M.line(name, 15, lx+20, 123)}</g>')
        nx = lx + 20 + M.cw(15) * len(name) + 8
        leg.append(f'<g fill="{DIM}">{M.line(pct, 15, nx, 123)}</g>')
        lx = nx + M.cw(15) * len(pct) + 30
    seen = len([r for r in d["repos"] if r["name"] != USER])
    scope = "public + private" if HAVE_USER else "public"
    title = M.line(f"PS C:\\wpggLabs> Get-Languages   # {seen} repos, {scope}", 18, 40, 34)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Language breakdown">
<defs><clipPath id="l"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>
<g clip-path="url(#l)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <g fill="{DIM}">{title}</g>
  <rect x="{x0}" y="{barY}" width="{barw}" height="{barH}" fill="#1c1c1c"/>
  {''.join(segs)}
  {''.join(leg)}
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FAINT}" stroke-width="1"/>
</g>
</svg>'''


# ─────────────────────── readme sections ───────────────────────
ICON = {"blockmaxxing": "🛡️", "pdf2vid": "🎬", "muraldesk": "🖼️", "live-ratings": "⚡",
        "gitsule": "📚", "nothi": "🗒️", "is-a-dev": "🌐", "wpgglabs.is-a.dev": "🌐"}


def builds_md(d):
    rows = ["| | project | what it is | stack | live |",
            "|:--:|:--|:--|:--|:--:|"]
    for r in d["public"][:6]:
        name = r["name"]
        desc = (r.get("description") or "").strip()
        if desc.lower().startswith(name.lower()):          # drop redundant "Name — ..." prefix
            desc = desc[len(name):].lstrip(" —–-:·").strip()
        for sep in (" — ", " – ", ". "):                    # keep the first clause only
            if sep in desc:
                desc = desc.split(sep)[0].strip()
                break
        desc = desc or "—"
        if len(desc) > 72:
            desc = desc[:69].rstrip() + "…"
        lang = r.get("language") or "—"
        home = r.get("homepage")
        live = f"[↗]({home})" if home else "—"
        icon = ICON.get(name, "▪️")
        rows.append(f"| {icon} | [`{name}`](https://github.com/{USER}/{name}) | {desc} | `{lang}` | {live} |")
    return "\n".join(rows)


def stack_md(d):
    order = [k for k, _ in d["topics"].most_common()]
    picked, seen = [], set()
    for key in order:
        if key in BADGE and key not in seen:
            picked.append(BADGE[key])
            seen.add(key)
    badges = []
    for label, logo in picked[:12]:
        lbl = label.replace(" ", "%20").replace("-", "--")
        badges.append(f'<img src="https://img.shields.io/badge/{lbl}-0c0c0c?style=flat-square&logo={logo}&logoColor=f2f2f2&labelColor=0c0c0c" alt="{label}" />')
    return "<p>\n  " + "\n  ".join(badges) + "\n</p>"


def stats_md(d):
    # NOTE: rendered inside a <p align="center"> HTML block, where GitHub does NOT
    # parse markdown — so emit HTML (<code>), never backticks/[links]().
    pub = len([r for r in d["repos"] if not r["private"] and r["name"] != USER])
    langs = len([l for l in d["lang_bytes"] if l not in MARKUP])
    star_word = "star" if d["stars"] == 1 else "stars"
    return (f"<code>{pub}</code> public repos &nbsp;·&nbsp; "
            f"<code>+{d['private']}</code> private builds &nbsp;·&nbsp; "
            f"<code>{d['stars']}</code> {star_word} &nbsp;·&nbsp; "
            f"<code>{langs}</code> languages in rotation")


def splice(md, key, content):
    a, b = f"<!--{key}:START-->", f"<!--{key}:END-->"
    i, j = md.find(a), md.find(b)
    if i == -1 or j == -1:
        print(f"  ! markers for {key} not found", file=sys.stderr)
        return md
    return md[:i + len(a)] + "\n" + content + "\n" + md[j:]


def main():
    print("· gathering live data" + (" (authenticated)" if TOKEN else " (public only)"))
    d = gather()
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    open(os.path.join(ROOT, "assets", "banner.svg"), "w", encoding="utf-8").write(banner(d))
    print("· wrote assets/banner.svg")

    rp = os.path.join(ROOT, "README.md")
    md = open(rp, encoding="utf-8").read()
    md = splice(md, "BUILDS", builds_md(d))
    md = splice(md, "STACK", stack_md(d))
    # The language chart + stat counts fold in PRIVATE repos, which only a user
    # token (GH_PAT) can see. Without it, preserve the committed private-inclusive
    # versions rather than downgrading them to public-only.
    if HAVE_USER:
        open(os.path.join(ROOT, "assets", "langs.svg"), "w", encoding="utf-8").write(langs_svg(d))
        md = splice(md, "STATS", stats_md(d))
        print("· refreshed language chart + stats (private included)")
    else:
        print("· no GH_PAT — kept committed language chart + stats (add secret to make them live)")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # also inside a <p> HTML block -> use <code> and <a>, not markdown
    md = splice(md, "UPDATED", f'<sub><code>last sync: {stamp}</code> — regenerated automatically by '
                               f'<a href=".github/workflows/profile.yml">profile.yml</a></sub>')
    open(rp, "w", encoding="utf-8").write(md)
    print("· README sections spliced. done.")


if __name__ == "__main__":
    main()
