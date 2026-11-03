# 晨间财经热榜

静态深色热榜页：七源 × Top 10 + 底栏外链。**不实时**；北京时间每日约 07:00 换一份 JSON 再重建页面。

## Layout

```
hotboard/
  data/
    YYYY-MM-DD.json   # daily snapshot
    latest.json       # symlink/copy of newest day
  docs/
    DATA_SCHEMA.md    # JSON contract
    ACCEPTANCE.md     # acceptance checklist
  build.py            # JSON → index.html (no network)
  index.html          # generated static page
  README.md
```

## Build

```bash
cd /workspace/hotboard
python3 build.py              # reads data/latest.json → index.html
python3 build.py --date 2026-11-02
python3 build.py -o /tmp/hotboard.html
```

Open `index.html` in a browser (file:// or any static host). Runtime JS does **not** fetch remote APIs.

## Daily pipeline (intent)

1. Research / assemble the seven columns + footer links.
2. Write `data/YYYY-MM-DD.json` per `docs/DATA_SCHEMA.md`.
3. Point `data/latest.json` at that file (copy or symlink).
4. Run `python3 build.py`.
5. Publish the same brief in chat; the web page is the same snapshot, rendered.

Failed sources: set `status` to `"empty"` or `"error"` (or leave `items` empty) → card shows「暂无更新」without breaking other columns.
