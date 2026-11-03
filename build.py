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
        <span class="rank{top}">{rank}</span>
        <div class="body">
          <a href="{href}" target="_blank" rel="noopener noreferrer">{title}</a>
          {note_html}
        </div>
      </li>"""
        )
    parts.append("      </ol>")
    return "\n".join(parts)


def render_columns(columns: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for col in columns:
        title = html.escape(str(col.get("title") or col.get("id") or "—"))
        body = render_items(col)
        blocks.append(
            f"""    <section class="card">
      <div class="card-head">
        <h2>{title}</h2>
        <span class="badge">TOP 10</span>
      </div>
{body}
    </section>"""
        )
    return "\n".join(blocks)


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
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
    color: var(--text);
    background:
      radial-gradient(1200px 600px at 12% -10%, rgba(90,130,255,0.18), transparent 55%),
      radial-gradient(900px 500px at 90% 0%, rgba(110,231,197,0.10), transparent 50%),
      linear-gradient(180deg, var(--bg1), var(--bg0));
    line-height: 1.5;
  }
  header {
    max-width: 1280px;
    margin: 0 auto;
    padding: 36px 24px 18px;
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
    font-size: clamp(1.6rem, 2.4vw, 2.1rem);
    font-weight: 680;
    letter-spacing: -0.02em;
  }
  .sub {
    margin: 0;
    color: var(--muted);
    font-size: 0.95rem;
  }
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
  }
  .chip b { color: var(--text); font-weight: 600; }
  main {
    max-width: 1280px;
    margin: 0 auto;
    padding: 8px 24px 28px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
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
    height: 372px;
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
    font-size: 1.02rem;
    font-weight: 650;
    color: var(--text);
  }
  .badge {
    font-size: 11px;
    font-weight: 650;
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
    padding: 0 4px 4px 0;
    overflow-y: auto;
    overflow-x: hidden;
    flex: 1;
    min-height: 0;
    max-height: none;
    scrollbar-width: thin;
    scrollbar-color: rgba(150,165,195,0.45) transparent;
  }
  ol::-webkit-scrollbar { width: 8px; }
  ol::-webkit-scrollbar-thumb {
    background: rgba(150,165,195,0.4);
    border-radius: 8px;
  }
  ol::-webkit-scrollbar-track { background: transparent; }
  li {
    display: grid;
    grid-template-columns: 28px 1fr;
    gap: 10px;
    padding: 7px 4px;
    border-radius: 10px;
    min-height: 52px;
  }
  li:hover { background: rgba(255,255,255,0.03); }
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
  .body a {
    color: var(--text);
    text-decoration: none;
    font-size: 0.88rem;
    font-weight: 560;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .body a:hover {
    color: var(--accent);
    text-decoration: underline;
    text-underline-offset: 3px;
  }
  .body p {
    margin: 2px 0 0;
    color: var(--muted);
    font-size: 0.74rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .empty {
    margin: 24px 8px;
    color: var(--muted);
    font-size: 0.92rem;
    text-align: center;
  }
  .links {
    max-width: 1280px;
    margin: 0 auto;
    padding: 4px 24px 40px;
  }
  .links h3 {
    margin: 0 0 12px;
    font-size: 1rem;
    font-weight: 620;
  }
  .link-row {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
  }
  .ext {
    display: flex;
    flex-direction: column;
    gap: 4px;
    text-decoration: none;
    padding: 16px 16px;
    border-radius: 14px;
    background: linear-gradient(180deg, rgba(30,38,58,0.9), rgba(18,24,38,0.9));
    border: 1px solid var(--card-border);
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    transition: border-color .15s ease, transform .15s ease;
  }
  .ext:hover {
    border-color: rgba(138,180,255,0.45);
    transform: translateY(-1px);
  }
  .ext-name { color: var(--text); font-weight: 620; }
  .ext-sub { color: var(--muted); font-size: 0.8rem; }
  footer {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 24px 48px;
    color: var(--muted);
    font-size: 0.8rem;
  }
"""


def render_html(data: dict[str, Any]) -> str:
    date = html.escape(str(data.get("date") or ""))
    update_chip = html.escape(format_beijing_chip(data))
    columns_html = render_columns(data.get("columns") or [])
    footer_html = render_footer_links(data.get("footer") or [])
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>晨间财经热榜 · {date}</title>
<style>
{CSS}
</style>
</head>
<body>
  <header>
    <div class="eyebrow">DAILY · BEIJING 07:00</div>
    <h1>晨间财经热榜</h1>
    <p class="sub">每个源 Top 10，标题可点跳转 · 框内滚动默认 1–5 · 非实时</p>
    <div class="meta">
      <span class="chip"><b>七源</b> 美股 / AI / A股 / 央行 / 商品 / 地缘 / Polymarket</span>
      <span class="chip"><b>更新</b> {update_chip}</span>
    </div>
  </header>
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
