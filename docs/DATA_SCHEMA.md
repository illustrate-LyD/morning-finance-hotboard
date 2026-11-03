# Daily JSON Schema · 晨间财经热榜

每日一份快照，北京时间约 07:00 由流水线写入 `data/YYYY-MM-DD.json`，并更新 `data/latest.json`。  
`build.py` 只读本地 JSON，生成静态 `index.html`（运行时不发起网络请求）。

## Root object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | yes | Calendar date of the brief, `YYYY-MM-DD` (Asia/Shanghai). |
| `timezone` | string | yes | Always `"Asia/Shanghai"`. |
| `updated_at` | string | yes | ISO 8601 datetime when the snapshot was finalized (prefer offset `+08:00`). |
| `columns` | array | yes | Exactly 7 column objects (order = display order). |
| `footer` | array | yes | External link cards (typically 4). |

## `columns[]`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Stable id: `us_stocks`, `x_ai`, `a_shares`, `central_banks`, `commodities`, `geopolitics`, `polymarket`. |
| `title` | string | yes | Display title (e.g. `美股`, `X · AI`). |
| `status` | string | yes | `"ok"` \| `"empty"` \| `"error"`. |
| `items` | array | yes | Ranked stories; length 0–10. When `status != "ok"` or `items` is empty, UI shows「暂无更新」. |

## `columns[].items[]`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rank` | integer | yes | 1–10, unique within the column, ascending. |
| `title` | string | yes | Headline shown as clickable text. |
| `href` | string | yes | Absolute `https://` URL. |
| `note` | string | no | One-line subtitle / context (may be `""`). |

## `footer[]`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Link label (e.g. `华尔街见闻`). |
| `sub` | string | yes | Short subtitle (e.g. `快讯 / 热门`). |
| `href` | string | yes | Absolute `https://` URL. |

## Example (truncated)

```json
{
  "date": "2026-11-02",
  "timezone": "Asia/Shanghai",
  "updated_at": "2026-11-02T07:00:00+08:00",
  "columns": [
    {
      "id": "us_stocks",
      "title": "美股",
      "status": "ok",
      "items": [
        {
          "rank": 1,
          "title": "英特尔指引差砸盘，科技与半导体重挫",
          "href": "https://example.com/story",
          "note": "英特尔单日约跌31%"
        }
      ]
    }
  ],
  "footer": [
    {
      "name": "华尔街见闻",
      "sub": "快讯 / 热门",
      "href": "https://wallstreetcn.com/"
    }
  ]
}
```

## File layout

- `data/YYYY-MM-DD.json` — immutable daily snapshot
- `data/latest.json` — copy or symlink of the newest snapshot (what `build.py` reads by default)
