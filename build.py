#!/usr/bin/env python3
"""Build static index.html from a daily JSON snapshot. No network I/O."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT = ROOT / "index.html"

RAIL_LABELS = {
    "us_stocks": "美股",
    "x_ai": "AI",
    "a_shares": "A股",
    "central_banks": "央行",
    "commodities": "商品",
    "geopolitics": "地缘",
    "polymarket": "Polymarket",
}


def load_data(date: str | None) -> dict[str, Any]:
    if date:
        path = DATA_DIR / f"{date}.json"
    else:
        path = DATA_DIR / "latest.json"
    if not path.exists():
        raise SystemExit(f"data file not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def format_beijing_chip(data: dict[str, Any]) -> str:
    """Prefer updated_at; fall back to date + 07:00."""
    raw = data.get("updated_at") or ""
    try:
        # Support Z and +08:00
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        # Display in Asia/Shanghai wall time without requiring zoneinfo if offset present
        local = dt.astimezone() if dt.tzinfo else dt
        # If offset is already +08:00, astimezone() uses box local (also +08)
        stamp = local.strftime("%Y-%m-%d %H:%M")
        return f"北京时间 {stamp} 更新"
    except Exception:
        date = data.get("date") or "—"
        return f"北京时间 {date} 约 07:00 更新"


def render_items(col: dict[str, Any]) -> str:
    status = (col.get("status") or "ok").lower()
    items = col.get("items") or []
    if status != "ok" or not items:
        return '<p class="empty">暂无更新</p>'

    parts: list[str] = ["<ol>"]
    for it in sorted(items, key=lambda x: int(x.get("rank") or 0))[:10]:
        rank = int(it.get("rank") or 0)
        title = html.escape(str(it.get("title") or ""))
        href = html.escape(str(it.get("href") or "#"), quote=True)
        note = html.escape(str(it.get("note") or ""))
        top = " top" if rank <= 3 else ""
        note_html = f"<p>{note}</p>" if note else ""
        parts.append(
            f"""      <li>
        <a class="row-link" href="{href}" target="_blank" rel="noopener noreferrer">
          <span class="rank{top}">{rank}</span>
          <div class="body">
            <span class="item-title">{title}</span>
            {note_html}
          </div>
        </a>
      </li>"""
        )
    parts.append("      </ol>")
    return "\n".join(parts)


def render_columns(columns: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for col in columns:
        cid = html.escape(str(col.get("id") or ""), quote=True)
        title = html.escape(str(col.get("title") or col.get("id") or "—"))
        id_attr = f' id="{cid}"' if cid else ""
        body = render_items(col)
        blocks.append(
            f"""    <section class="card"{id_attr}>
      <div class="card-head">
        <h2>{title}</h2>
        <span class="badge">TOP 10</span>
      </div>
{body}
    </section>"""
        )
    return "\n".join(blocks)


def render_source_rail(columns: list[dict[str, Any]]) -> str:
    links: list[str] = []
    for col in columns:
        cid = str(col.get("id") or "")
        if not cid:
            continue
        label = RAIL_LABELS.get(cid) or str(col.get("title") or cid)
        href = html.escape(cid, quote=True)
        text = html.escape(label)
        links.append(f'    <a href="#{href}">{text}</a>')
    inner = "\n".join(links)
    return (
        '  <nav class="source-rail" aria-label="七个来源">\n'
        + inner
        + "\n  </nav>"
    )


def render_footer_links(footer: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for link in footer:
        name = html.escape(str(link.get("name") or ""))
        sub = html.escape(str(link.get("sub") or ""))
        href = html.escape(str(link.get("href") or "#"), quote=True)
        parts.append(
            f"""      <a class="ext" href="{href}" target="_blank" rel="noopener noreferrer">
        <span class="ext-name">{name}</span>
        <span class="ext-sub">{sub}</span>
      </a>"""
        )
    return "\n".join(parts)


CSS = """
  :root {
    --bg0: #07090f;
    --bg1: #0c101a;
    --card: rgba(22, 28, 42, 0.82);
    --card-border: rgba(120, 140, 180, 0.16);
    --text: #eef2ff;
    --muted: #9aa6bf;
    --accent: #8ab4ff;
    --accent2: #6ee7c5;
    --rank: #6b7794;
    --rank-top: #ffb454;
    --glow: rgba(90, 130, 255, 0.22);
    --page-pad-x: 16px;
    --rail-height: 56px;
    --sticky-offset: calc(var(--rail-height) + env(safe-area-inset-top, 0px));
  }
  * { box-sizing: border-box; }
  html {
    -webkit-text-size-adjust: 100%;
    color-scheme: dark;
    background-color: var(--bg0);
  }
  body {
    margin: 0;
    min-height: 100vh;
    min-height: 100dvh;
    font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
    color: var(--text);
    background-color: var(--bg0);
    background-image:
      radial-gradient(1200px 600px at 12% -10%, rgba(90,130,255,0.18), transparent 55%),
      radial-gradient(900px 500px at 90% 0%, rgba(110,231,197,0.10), transparent 50%),
      linear-gradient(180deg, var(--bg1), var(--bg0));
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }
  header {
    max-width: 1280px;
    margin: 0 auto;
    padding: 24px max(var(--page-pad-x), env(safe-area-inset-right, 0px)) 12px max(var(--page-pad-x), env(safe-area-inset-left, 0px));
  }
  .eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 10px;
    border-radius: 999px;
    border: 1px solid rgba(138,180,255,0.28);
    background: rgba(138,180,255,0.08);
    color: var(--accent);
    font-size: 12px;
    letter-spacing: 0.04em;
  }
  h1 {
    margin: 14px 0 8px;
    font-size: 1.375rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  .sub {
    margin: 0;
    color: var(--muted);
    font-size: 0.875rem;
    font-weight: 400;
  }
  .sub-scroll { display: none; }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 16px;
  }
  .chip {
    padding: 6px 11px;
    border-radius: 10px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--card-border);
    color: var(--muted);
    font-size: 12.5px;
    font-weight: 400;
  }
  .chip b { color: var(--text); font-weight: 600; }
  .chip-sources { display: none; }
  .source-rail {
    position: sticky;
    top: env(safe-area-inset-top, 0px);
    z-index: 20;
    display: flex;
    flex-wrap: nowrap;
    align-items: center;
    gap: 8px;
    width: 100%;
    max-width: 100vw;
    min-width: 0;
    height: var(--rail-height);
    padding-left: max(var(--page-pad-x), env(safe-area-inset-left, 0px));
    padding-right: max(var(--page-pad-x), env(safe-area-inset-right, 0px));
    background: rgba(12, 16, 26, 0.94);
    backdrop-filter: blur(10px);
    overflow-x: auto;
    overflow-y: hidden;
    scroll-snap-type: x proximity;
    overscroll-behavior-x: contain;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .source-rail::-webkit-scrollbar { display: none; }
  .source-rail a {
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 44px;
    padding: 0 12px;
    border-radius: 999px;
    color: var(--text);
    text-decoration: none;
    font-size: 0.8125rem;
    font-weight: 600;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--card-border);
    scroll-snap-align: start;
    touch-action: manipulation;
    -webkit-tap-highlight-color: rgba(138,180,255,0.22);
  }
  .source-rail a:active { background: rgba(255,255,255,0.08); }
  .source-rail a:focus-visible,
  .row-link:focus-visible,
  .ext:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  main {
    max-width: 1280px;
    margin: 0 auto;
    padding: 8px max(var(--page-pad-x), env(safe-area-inset-right, 0px)) 28px max(var(--page-pad-x), env(safe-area-inset-left, 0px));
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 18px;
    padding: 14px 14px 10px;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 40px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.04);
    display: flex;
    flex-direction: column;
    height: auto;
    min-width: 0;
    scroll-margin-top: calc(var(--rail-height) + env(safe-area-inset-top, 0px) + 8px);
  }
  .card:target {
    box-shadow:
      0 0 0 1px rgba(138,180,255,0.45),
      0 10px 40px rgba(0,0,0,0.25),
      inset 0 1px 0 rgba(255,255,255,0.04);
  }
  .card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 8px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    flex-shrink: 0;
  }
  .card-head h2 {
    margin: 0;
    font-size: 1.0625rem;
    font-weight: 600;
    color: var(--text);
  }
  .badge {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: var(--accent2);
    background: rgba(110,231,197,0.1);
    border: 1px solid rgba(110,231,197,0.25);
    border-radius: 999px;
    padding: 3px 8px;
  }
  ol {
    list-style: none;
    margin: 0;
    padding: 0;
    overflow: visible;
    flex: none;
    min-height: 0;
  }
  ol::-webkit-scrollbar { width: 8px; }
  ol::-webkit-scrollbar-thumb {
    background: rgba(150,165,195,0.4);
    border-radius: 8px;
  }
  ol::-webkit-scrollbar-track { background: transparent; }
  li { margin: 0; padding: 0; }
  li, .row-link, .body, .item-title { min-width: 0; }
  .body { overflow: hidden; }
  .row-link {
    display: grid;
    grid-template-columns: 28px 1fr;
    gap: 10px;
    align-items: start;
    padding: 10px 8px;
    border-radius: 10px;
    min-height: 48px;
    width: 100%;
    text-decoration: none;
    color: inherit;
    touch-action: manipulation;
    -webkit-tap-highlight-color: rgba(138,180,255,0.22);
  }
  .row-link:active { background: rgba(255,255,255,0.05); }
  .rank {
    width: 26px; height: 26px;
    border-radius: 8px;
    display: grid; place-items: center;
    font-size: 12px; font-weight: 700;
    color: var(--rank);
    background: rgba(255,255,255,0.04);
    margin-top: 1px;
  }
  .rank.top {
    color: #1a1206;
    background: linear-gradient(135deg, #ffd089, #ffb454);
    box-shadow: 0 0 0 1px rgba(255,180,84,0.35), 0 6px 16px rgba(255,180,84,0.18);
  }
  .item-title {
    color: var(--text);
    font-size: 0.9375rem;
    font-weight: 600;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    overflow-wrap: break-word;
  }
  .body p {
    margin: 2px 0 0;
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 400;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .empty {
    margin: 24px 8px;
    color: var(--muted);
    font-size: 0.92rem;
    font-weight: 400;
    text-align: center;
  }
  .links {
    max-width: 1280px;
    margin: 0 auto;
    padding: 4px max(var(--page-pad-x), env(safe-area-inset-right, 0px)) 40px max(var(--page-pad-x), env(safe-area-inset-left, 0px));
  }
  .links h3 {
    margin: 0 0 12px;
    font-size: 1rem;
    font-weight: 600;
  }
  .link-row {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .ext {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    text-decoration: none;
    padding: 16px 16px;
    min-height: 48px;
    border-radius: 14px;
    background: linear-gradient(180deg, rgba(30,38,58,0.9), rgba(18,24,38,0.9));
    border: 1px solid var(--card-border);
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    transition: border-color .15s ease, transform .15s ease;
    touch-action: manipulation;
    -webkit-tap-highlight-color: rgba(138,180,255,0.22);
  }
  .ext-name { color: var(--text); font-weight: 600; }
  .ext-sub { color: var(--muted); font-size: 0.8rem; font-weight: 400; }
  footer {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 max(var(--page-pad-x), env(safe-area-inset-right, 0px)) max(48px, env(safe-area-inset-bottom, 0px)) max(var(--page-pad-x), env(safe-area-inset-left, 0px));
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 400;
  }

  @media (min-width: 640px) {
    :root { --page-pad-x: 24px; }
    header { padding-top: 28px; padding-bottom: 16px; }
    h1 { font-size: 1.5rem; }
    .sub { font-size: 0.9375rem; }
    .sub-scroll { display: inline; }
    .chip-sources { display: inline; }
    main {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .card {
      height: 372px;
    }
    .card-head h2 { font-size: 1.0625rem; }
    ol {
      padding: 0 4px 4px 0;
      overflow-x: hidden;
      overflow-y: auto;
      flex: 1;
      scrollbar-width: thin;
      scrollbar-color: rgba(150,165,195,0.45) transparent;
      overscroll-behavior: contain;
      -webkit-overflow-scrolling: touch;
    }
    .item-title { font-size: 0.875rem; }
    .link-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    footer { font-size: 0.8rem; }
  }

  @media (min-width: 1024px) {
    header { padding-top: 36px; padding-bottom: 18px; }
    h1 { font-size: clamp(1.6rem, 2.4vw, 2.1rem); }
    .sub { font-size: 0.95rem; }
    .source-rail { display: none; }
    main { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .card-head h2 { font-size: 1.02rem; }
    .item-title { font-size: 0.88rem; }
    .body p { font-size: 0.74rem; }
    .link-row { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  }

  @media (max-width: 1023.98px) and (max-height: 500px) and (orientation: landscape) {
    .eyebrow, .sub { display: none; }
    header {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 8px 16px;
      padding-top: 8px;
      padding-bottom: 8px;
    }
    h1 { margin: 0; font-size: 1.125rem; }
    .meta { margin-top: 0; }
    .card {
      height: 372px;
      height: min(372px, calc(100vh - var(--sticky-offset) - env(safe-area-inset-bottom, 0px) - 24px));
      height: min(372px, calc(100dvh - var(--sticky-offset) - env(safe-area-inset-bottom, 0px) - 24px));
    }
    ol {
      padding: 0 4px 4px 0;
      overflow-x: hidden;
      overflow-y: auto;
      flex: 1;
      min-height: 0;
      overscroll-behavior: contain;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: thin;
      scrollbar-color: rgba(150,165,195,0.45) transparent;
    }
  }

  @media (hover: hover) and (pointer: fine) {
    .row-link:hover { background: rgba(255,255,255,0.03); }
    .row-link:hover .item-title {
      color: var(--accent);
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .ext:hover {
      border-color: rgba(138,180,255,0.45);
      transform: translateY(-1px);
    }
    .source-rail a:hover { background: rgba(255,255,255,0.08); }
  }

  @media (prefers-reduced-motion: reduce) {
    .ext { transition: none; }
    .ext:hover { transform: none; }
  }
"""


def render_html(data: dict[str, Any]) -> str:
    date = html.escape(str(data.get("date") or ""))
    update_chip = html.escape(format_beijing_chip(data))
    columns = data.get("columns") or []
    columns_html = render_columns(columns)
    rail_html = render_source_rail(columns)
    footer_html = render_footer_links(data.get("footer") or [])
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="#07090f" />
<meta name="color-scheme" content="dark" />
<title>晨间财经热榜 · {date}</title>
<style>
{CSS}
</style>
</head>
<body>
  <header>
    <div class="eyebrow">DAILY · BEIJING 07:00</div>
    <h1>晨间财经热榜</h1>
    <p class="sub">每个源 Top 10，点标题看原文<span class="sub-scroll"> · 框内滚动默认 1–5</span> · 非实时</p>
    <div class="meta">
      <span class="chip chip-sources"><b>七源</b> 美股 / AI / A股 / 央行 / 商品 / 地缘 / Polymarket</span>
      <span class="chip"><b>更新</b> {update_chip}</span>
    </div>
  </header>
{rail_html}
  <main>
{columns_html}
  </main>
  <div class="links">
    <h3>外链热榜 / 快讯</h3>
    <div class="link-row">
{footer_html}
    </div>
  </div>
  <footer>公开信息整理，仅供参考，不构成投资建议。价格、赔率与链接目标页可能变动。</footer>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build hotboard index.html from JSON")
    parser.add_argument(
        "--date",
        help="YYYY-MM-DD to load from data/<date>.json (default: data/latest.json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=OUT,
        help=f"output HTML path (default: {OUT})",
    )
    args = parser.parse_args()
    data = load_data(args.date)
    html_out = render_html(data)
    args.output.write_text(html_out, encoding="utf-8")
    print(f"wrote {args.output} ({len(html_out)} bytes) from date={data.get('date')}")


if __name__ == "__main__":
    main()
