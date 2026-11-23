# 晨间财经热榜 · 手机端响应式设计说明

日期：2026-11-23  
状态：交给 Nibble 落地（静态 GitHub Pages，不是独立 App）  
线上对照：https://illustrate-LyD.github.io/morning-finance-hotboard/  
仓库：`illustrate-LyD/morning-finance-hotboard`  
改动入口：`build.py` 里的 HTML 模板与 `CSS` 常量（每日重建会覆盖 `index.html`）

本文只改**布局与触控适配**。不改深色主题色板、不改七源数据结构、不改桌面（≥1024px）的三栏外观。

---

## 1. 目标与非目标

**目标**：在 Android Chrome 与 iOS Safari 上，用同一份静态页把现有七栏热榜读顺、点准。覆盖竖屏与横屏。

**非目标**：独立 App / PWA 安装、实时刷新、登录、改配色、改 JSON 契约、按设备做两套页面。

**已核对的线上现状**（2026-11-23 07:15 新加坡时间上线稿，etag `6b0377a0`；本地 `/workspace/hotboard/index.html` 与线上字节一致）：

- 已有 `viewport width=device-width, initial-scale=1`，但 **CSS 里没有任何 `@media`**。
- 主栅格是 `repeat(auto-fill, minmax(340px, 1fr))`，左右各 24px 内边距。宽度 < 约 388px（常见 360 宽 Android）时，340 + 48 超出视口，**右侧留白被吃掉，卡片贴边**。
- 卡片固定高度 `372px`，列表在卡内滚动。窄屏上第 6 条往往被卡底裁切，必须「页滚 + 框滚」两套手势，iOS 上容易抢滚动。
- 副标题「框内滚动默认 1–5」在 360 宽会从「默 / 认」中间折行。
- 「七源」这枚长 chip 会折成两行；横屏时页头占用过多纵高，每卡大约只能看到 2 条。
- 只有标题 `<a>` 可点，备注和整行空白不可点；`:hover` 未限制指针类型，iOS 点击后会残留悬停态。
- `body { min-height: 100vh }`，无 `dvh`、无 `safe-area-inset`、无 `viewport-fit=cover`、无 `color-scheme: dark`。
- 字重写了 `680 / 650 / 560`，系统中文黑体常没有这些档，iOS / Android 会各自假粗，观感不一致。
- 卡片没有使用 `columns[].id` 做锚点，窄屏无法快速跳到某一源。

对照截图（当前未改前）：`docs/_preview/mobile-current/`。

---

## 2. 信息架构：七栏在窄屏怎么排

**原则：时间线式「看板下拆」，不是改成一次只看一个源的 App 选项卡。** 七源仍按现有顺序同时存在于同一页，只是栅格从 3 列改为 2 列或 1 列。

| 方案 | 结论 |
|---|---|
| 竖屏单列堆叠 + 顶部粘性来源条跳转 | **采用**。保留「一页看完七源」的看板心智，避免卡内嵌套滚动。 |
| 横向滑页、一次只显示一源 | 不用。需要 JS，藏起另外六源，更像 App，不像响应式网页。 |
| 七卡横滑（单行横向滚动） | 不用。发现成本高，且与卡内纵向列表形成双向滚动。 |
| 手风琴（同时只展开一源） | 不用。多一次点按，早间扫榜变慢。 |

桌面现有的「卡内滚动看 6–10」只保留在中屏、横屏短视口和宽屏。

---

## 3. 断点

只按视口宽度（再加一条横屏短高的补充），不按 UA 判断机型。

| 档 | 宽度 | 典型设备 | 主栅格 | 卡片高度 |
|---|---|---|---|---|
| **S 窄屏竖屏** | `< 640px` | iPhone SE / 14 / 15、多数 Android 竖屏（360–430） | **1 列**，`grid-template-columns: 1fr` | **自适应，展开全部最多 10 条，取消卡内滚动** |
| **M 中屏** | `640px–1023px` | 手机横屏、小平板竖屏（如 768） | **2 列**，`repeat(2, minmax(0, 1fr))`；第 7 卡独自落在最后一行、左对齐，不拉宽铺满 | 默认保持 `372px` + 卡内滚动 |
| **L 宽屏** | `≥ 1024px` | 桌面、大平板横屏 | **保持现状三列**（建议写成 `repeat(3, minmax(0, 1fr))`，避免再出现 `minmax(340px)` 溢出），`max-width: 1280px` | 保持 `372px` + 卡内滚动 |

补充条件（叠在 M 上，不另开一档宽度）：

```css
@media (max-height: 500px) and (orientation: landscape) { /* 手机横屏 */ }
```

此时：页头改为紧凑态（见 §5）；卡片高度改为

`height: min(372px, calc(100dvh - var(--sticky-offset) - env(safe-area-inset-bottom, 0px) - 24px));`

并**保留卡内滚动**（横屏纵高不够展开 10 条）。

宽度断点用 `639.98px` / `1023.98px` 或 mobile-first 的 `min-width: 640px` 与 `min-width: 1024px`，不要在 `640px` 上写两套互相覆盖的 `max-width`/`min-width` 造成双击中。

---

## 4. 页面结构与组件

### 4.1 页头（`<header>`，不吸顶）

- 保留 eyebrow `DAILY · BEIJING 07:00`、`<h1>晨间财经热榜</h1>`、更新日期 chip。
- **S**：去掉「七源 美股 / AI / …」这枚长 chip（与来源条重复）；副标题改为不在「默认」中间折行的短句，例如：`每个源 Top 10，点标题看原文 · 非实时`。可用两个 `<span>`：`.sub-scroll` 仅在 M/L 显示「框内滚动默认 1–5」。
- **横屏短高**：隐藏 eyebrow 与副标题，标题缩小，更新日期与标题同一行或紧贴其下，把纵高让给卡片。

### 4.2 来源跳转条（新，仅 S/M）

宽屏已能同时看见多列，**L 不显示**。

- 标记：`<nav class="source-rail" aria-label="七个来源">`，放在 `<header>` 与 `<main>` 之间。
- 七个锚点链接，顺序与 `columns[]` 一致。标签用短名，避免条内折行：

  | `id` | 按钮文案 | 卡片 `h2`（不变） |
  |---|---|---|
  | `us_stocks` | 美股 | 美股 |
  | `x_ai` | AI | X · AI |
  | `a_shares` | A股 | A 股 |
  | `central_banks` | 央行 | 央行 · 财政 |
  | `commodities` | 商品 | 商品 · 期货 |
  | `geopolitics` | 地缘 | 地缘政治 |
  | `polymarket` | Polymarket | Polymarket |

- 卡片根节点必须带锚点：`<section class="card" id="us_stocks">`（用已有 `columns[].id`，不新增字段）。
- 表现：单行横向滑动（`flex` + `overflow-x: auto`），`scroll-snap-type: x proximity` 可选；**不折行**。隐藏或弱化滚动条。背景用实色半透明 `rgba(12, 16, 26, 0.94)`，`backdrop-filter` 仅作增强，不作为可读性前提（iOS 上 sticky + blur 偶发失效）。
- 粘性定位：`position: sticky; top: env(safe-area-inset-top, 0px); z-index: 20;`。
- 卡片设置 `scroll-margin-top: calc(var(--rail-height) + env(safe-area-inset-top, 0px) + 8px);`，避免跳转后标题藏在条下方。`--rail-height` 按实际含内边距高度写死（建议量完约 52–56px）。
- 焦点/当前态：`:focus-visible` 可见描边；`:target` 给对应卡片一圈浅描边即可。
- **不要求**滚动时自动高亮当前源（那需要 JS）。本站目前无运行时脚本，v1 用纯 CSS + 锚点即可。若 Nibble 愿意加极小脚本（`IntersectionObserver`）可作可选增强，但不是验收必过项。

### 4.3 来源卡与条目

- 圆角、边框、色板、TOP 10 徽章、1–3 名金色序号：**保持现有视觉**。
- **整行可点**：每一条用一个 `<a class="row-link">` 包住序号、标题和备注（仍 `target="_blank" rel="noopener noreferrer"`）。不要只让标题文字是热区。
- 标题仍最多 2 行（`-webkit-line-clamp: 2`）；备注仍 1 行省略号，避免 10 条被长注撑爆。给标题加 `overflow-wrap: break-word`，避免超长英文/数字撑出横向滚动。
- 空态「暂无更新」不变，且仍不得影响其他源。

### 4.4 底栏外链

- S：一行一张（`1fr`），热区高度 ≥ 48px。
- M：`repeat(2, minmax(0, 1fr))`。
- L：保持现有自动填列（或 `repeat(4, 1fr)`）。
- 声明文字留在 `<footer>`，底部加上 `safe-area-inset-bottom`，避免被 iOS 首页指示条挡住。

---

## 5. 字号、间距、触控热区

根字号保持浏览器默认（通常 16px），一律用 `rem`，方便系统字体缩放。不要写 `user-scalable=no` / `maximum-scale=1`。`html` 设 `-webkit-text-size-adjust: 100%;`，防止 iOS 自动撑大，但不禁止用户双指缩放。

| 元素 | S | M | L（基本保持现状） |
|---|---|---|---|
| 页边距 `--page-pad-x` | `16px`，且 `max(16px, env(safe-area-inset-*))` | `24px` + 安全区 | `24px` + 安全区（通常为 0） |
| 栅格间距 | `12px` | `16px` | `16px` |
| `h1` | `1.375rem`（22px） | `1.5rem` | 现有 `clamp(1.6rem, 2.4vw, 2.1rem)` |
| 副标题 | `0.875rem` | `0.9375rem` | `0.95rem` |
| 来源条按钮 | `0.8125rem`，字重 600 | 同左 | — |
| 卡片 `h2` | `1.0625rem`（17px） | `1.0625rem` | `1.02rem` 可保留 |
| 条目标题 | `0.9375rem`（15px） | `0.875rem` | `0.88rem` 可保留 |
| 条目备注 | `0.75rem`（12px） | `0.75rem` | `0.74rem` 可保留 |
| 页脚声明 | `0.75rem` | `0.8rem` | `0.8rem` |

**字重（全局统一，含桌面）**：标题 700，卡片标题与条目标题 600，备注与弱化文字 400。废除 `680 / 650 / 560`。这是为了中文系统字体在 iOS / Android 上不再假粗，桌面观感几乎不变。

**触控热区**（按较严的一边取：iOS 44pt、Material 48dp）：

- 条目标题行：`.row-link` 最小高度 **48px**，建议 `padding: 10px 8px`；相邻行不必再额外空出 8px 间隙（行高本身已隔开）。
- 来源条按钮：最小高度 **44px**，水平内边距 ≥ 12px，按钮间隙 8px。
- 外链卡：最小高度 **48px**，内边距不少于现在的 `16px`。
- 非按钮的 chip（更新日期）不必凑 44px。

按压缩反馈：`:active` 给行/按钮一层浅叠色。悬停样式只写在：

```css
@media (hover: hover) and (pointer: fine) { ... }
```

---

## 6. 横竖屏

**竖屏 S**：单列展开 10 条 + 粘性来源条。用户沿页面一直向下扫，或点来源条跳转。这是主路径。

**横屏（通常落入 M，且 `max-height: 500px`）**：

- 两列并排，卡片恢复内滚动，高度按 §3 的 `min(372px, 100dvh - …)` 收敛，使一排卡片大致落在一屏内。
- 页头紧凑（§4.1）。来源条仍吸顶。
- **左右安全区必须生效**（刘海 / 岛状摄像头在横屏会占左右，常见 44–47px）。内容（含来源条、卡片、外链）不得顶到屏幕圆角或被指示条挡住。

旋转后无需保存「当前源」状态（无选项卡状态）。锚点在 URL 里的话，旋转后仍应对准同一张卡。

---

## 7. iOS Safari 与 Android Chrome 差异（必须处理）

下列每条都要在 CSS / 页头 meta 里落到实处，而不是只在桌面 Chrome 模拟器里「看起来还行」。

### 7.1 视口与安全区

- viewport 改为：`width=device-width, initial-scale=1, viewport-fit=cover`。没有 `viewport-fit=cover` 时，iOS 上 `env(safe-area-inset-*)` 常常是 0。
- 页头、来源条、主区、外链、页脚的左右（及底）内边距一律：`max(设计间距, env(safe-area-inset-*, 0px))`。
- 来源条 `top`、卡片 `scroll-margin-top` 计入 `safe-area-inset-top`（尤其是横屏和「添加到主屏幕」时）。
- Android 手势条 / 挖孔屏在较新的 Chrome 里同样认 `env()`，用同一套规则即可，不必分平台写。

### 7.2 `100vh` 与动态工具栏

- iOS Safari 的经典 `100vh` 等于「工具栏收起后」的高度，容易让固定/计算高度的块被底栏挡住，或出现多余回弹空白。
- `body` 使用：`min-height: 100vh; min-height: 100dvh;`（旧浏览器走第一行）。
- 横屏卡片高度只准用 `100dvh`（可再写 `100vh` 作回退），不要只用 `100vh`。
- 不要用 `position: fixed` 铺满全屏。粘性条用 `sticky` 即可。

### 7.3 滚动与回弹

- `html, body` 先铺实色 `--bg0`（`#07090f`），并设 `color-scheme: dark`，再加现有径向渐变。避免 iOS 回弹或 Android 过度滚动时闪出白边。
- **S 竖屏取消卡内 `overflow-y: auto`**，只保留页面一级滚动，从根上避开 iOS 嵌套滚动抢手势。
- M/L（以及横屏短高）若仍有卡内滚动：`overscroll-behavior: contain;`，并保留 `-webkit-overflow-scrolling: touch;`。
- 来源条横向滚动同样加 `overscroll-behavior-x: contain`，减少滑到尽头时带动整页。
- 不要对 `body` 写 `overflow: hidden` 来「关掉回弹」，会破坏滚动和无障碍。

### 7.4 字体渲染

- 字体栈保持：`"SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif`（iOS 走苹方，Android 走 Noto / 系统黑体）。
- 深色背景加 `-webkit-font-smoothing: antialiased;`（已在用系统栈，可写在 `body`）。
- 只使用 400 / 600 / 700，见 §5。
- 已有 `lang="zh-Hans"`，保留。
- 可加 `<meta name="theme-color" content="#07090f">`，让 Android Chrome 顶栏与页底同色；`<meta name="color-scheme" content="dark">` 与 CSS `color-scheme: dark` 一起写。

### 7.5 点击与悬停

- 已有 `width=device-width`，不必再为 300ms 延迟打补丁。链接上可加 `touch-action: manipulation`，不可禁掉纵向滚动。
- `-webkit-tap-highlight-color` 用一层浅色半透明（不要 `transparent` 到完全没反馈，也不要用系统默认大块高光）。
- 悬停规则必须包在 `(hover: hover) and (pointer: fine)` 里，避免 iOS 点完一条后整行一直停在 hover 色。
- `prefers-reduced-motion: reduce` 时，去掉 `.ext:hover` 的 `transform` 以及其它位移。

### 7.6 其它不要做的事

- 不要为了「更像 App」关掉缩放。
- 不要依赖 `backdrop-filter` 才读得清来源条。
- 不要引入独立的 iOS / Android 两套样式表。

---

## 8. 给 Nibble 的落地要点（结构，不是最终补丁）

优先改 `build.py`，不要只手改生成后的 `index.html`。

1. `<html>` / `<head>`：`viewport-fit=cover`、`theme-color`、`color-scheme`。
2. `render_columns`：给 `<section class="card" id="...">` 写上 `columns[].id`。
3. 新增 `render_source_rail()`：七个短名锚点；L 用 CSS 隐藏，DOM 可保留。
4. `render_items`：整行一个 `.row-link`。
5. CSS：按 §3–§7 增加变量、安全区、断点、sticky、hover 媒体查询；全局改字重；S 取消卡内滚动；把 `minmax(340px, 1fr)` 换成不会溢出的 `1fr` / `repeat(2, …)` / `repeat(3, …)`，子项加 `min-width: 0`。
6. 副标题折行修复见 §4.1。
7. 色板变量（`--bg0 / --bg1 / --card / --accent / --rank-top` 等）**一行都不要改**。

不需要为这次适配改 `docs/DATA_SCHEMA.md` 或每日 JSON。

---

## 9. 验收标准

在下列视口各测一次（开发期可用 Chrome / Firefox 设备模式；**安全区、100dvh、回弹、字体**至少要在一台真机 iOS Safari 和一台 Android Chrome 上各过一遍）。建议视口：

- 360 × 800 竖屏（小屏 Android）
- 390 × 844 竖屏（iPhone 14 类）
- 430 × 932 竖屏（大屏 iPhone）
- 844 × 390 与 667 × 375 横屏
- 768 × 1024（平板竖屏，回归 M）
- 1280 × 800（桌面回归，外观应与改前一致）

### 必须通过

1. 七张来源卡都在，顺序不变；每源最多 10 条；失败源只显示「暂无更新」，不影响其它源。
2. **360 宽页面无横向滚动**；卡片左右都有可见留白（≥16px，安全区更大时取更大值），不再贴右缘。
3. **S 竖屏**：单列；每张卡一次性展开全部条目，卡内不能再滚；第 6–10 条只需继续滚页面就能看到。
4. **S/M** 可见粘性来源条；点「商品」「Polymarket」等，对应卡片标题出现在来源条下方，不被遮挡。
5. 每条的标题、备注、行内空白均可点，并在新标签打开 `https` 链接；热区高度 ≥ 48px。
6. 来源条按钮高度 ≥ 44px；外链卡高度 ≥ 48px。
7. 横屏：两列、页头紧凑、左右/底部尊重安全区；短视口下卡片可在卡内滚动，且不被工具栏或底部手势条裁切关键内容。
8. 桌面 1280：仍为三列、卡片约 372px、框内滚动可看到 6–10 条；色板与改前一致；「先读」路径未改（本页无该模块）。
9. 副标题在 360 宽不再从「默 / 认」中间断行。
10. 允许双指缩放；未设置 `user-scalable=no` / `maximum-scale=1`。
11. iOS 下拉回弹或 Android 过度滚动时，边缘不闪白；`color-scheme` 为 dark。
12. 点按一条后，该行不会一直停在悬停色（在真机 Safari / Chrome 上检查）。
13. 现有验收中与内容相关的条目仍成立：顶栏北京时间更新、底栏四个外链、深色主题、1–3 名视觉强调、同日 JSON 快照。

### 非必须（可后续再做）

- 滚动时自动高亮来源条当前项（需 JS）。
- 添加到主屏幕的图标 / 启动图。
- 平板横屏改四列。

### 未通过时

直接改 `build.py` 后重建并发布 Pages。设计侧如需改断点或「横屏是否坚持两列」，回我（UI-web）再定，不要悄悄改成单源滑页。

---

## 10. 建议实施顺序

1. 全局安全项：viewport、color-scheme、safe-area、dvh、底色、字重、hover 媒体查询（桌面几乎无感）。
2. HTML：卡片 `id`、来源条、整行链接、副标题结构。
3. 断点栅格与 S 展开列表、M 两列、横屏紧凑页头。
4. 按 §9 自测后发我复扫（请附 Pages 地址；若只改了 CSS/HTML 结构，用当天已有数据重建即可）。
