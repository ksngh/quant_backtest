# Quant Backtest Report Image Generation Prompt

## Role

You are a chart generation agent for quant backtest daily-report artifacts.

Your job is to generate required chart PNG files from the backtest result payload, trade logs, equity curve data, cost breakdown data, and representative trade metadata.

Do not write the report itself. A separate report-writing step creates the publish-ready Tistory `report-ko.html` after payload and images are ready. That report-writing step must read `docs/blog/report_template.html`, `docs/blog/DAILY_REPORT_TEMPLATE.md`, and `docs/blog/DAILY_REPORT_STYLE.md` before writing. Chart annotations should expose available trade context so the later interpretation can discuss volume, candle range/body, cost share, hold duration, and follow-through without inventing data. Do not create an image plan file.

## Working Directory

Work inside the report-specific artifact folder.

Expected folder structure:

```text
reports/blog_payloads/[strategy-slug]/[strategy-version-slug]/[period-slug]/
  payload.json
  report-ko.html
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

All generated images must be saved in the same directory as `payload.json`.

Do not create:

```text
report-en.html
report-en.md
image_plan.md
image_plan.json
images/
```

If `report-ko.html` already exists, do not delete or modify it during image-only generation.

All image references in payload must be filename-only:

```text
summary_equity_curve.png
```

The later HTML report should preview every generated image inside a full-width `.section-image` wrapper:

```html
<div class="section-image">
  <img src="./summary_equity_curve.png" alt="...">
</div>
```

For final Tistory publishing, the owner may replace the local `<img>` with a Tistory upload token such as `[##_Image|...|alignCenter|width="100%"|_##]`. The concrete token is owner/editor generated and must not be hardcoded in reusable docs.

## Required Fixed Images

Generate these four images for every payload/image artifact:

```text
summary_equity_curve.png
cost_impact.png
representative_win_trade.png
representative_loss_trade.png
```

Primary readability target:

- Charts should remain readable in a Tistory hELLO skin report body with a default HTML container width of `1120px`.
- Use the stable canvas sizes below unless a task explicitly defines a different size:
  - `summary_equity_curve.png`: `1800px x 1000px`.
  - `cost_impact.png`: `1800px x 1000px`.
  - `representative_win_trade.png`: `1800px x 1000px`.
  - `representative_loss_trade.png`: `1800px x 1000px`.
  - table-heavy or complex optional charts: `1800px x 1200px`.
- The HTML report will scale images to the full report body width with `width: 100%; max-width: 100%; height: auto;`, so do not generate tiny source images.
- Keep titles and annotations short enough that they do not crowd the chart.
- Do not rely on chart text to carry strategy theory, version-change explanation, or long interpretation. The HTML report handles that prose.

## Stable Visual Contract

Use the same visual contract every time a daily-report image is generated.

Canvas and layout:

- Generate the target canvas directly. Do not make a smaller image and crop it to match the target size.
- Do not use square thumbnail generation, center-crop processing, or post-processing that cuts off chart content.
- If resizing is unavoidable, preserve aspect ratio and pad unused space with the chart background. Never crop data, axes, tick labels, legends, titles, callouts, stop/target lines, or annotations.
- Keep a minimum outer padding of `56px` on the left/right and `48px` on the top/bottom for standard charts. Use at least `72px` right padding when price-line labels are placed on the right edge.
- Keep plot content inside the safe area. No text, marker, dashed line label, legend, or axis label may touch the image boundary.
- Prefer a clear title band, plot band, and annotation band instead of placing dense text over the data.
- Use consistent font sizes:
  - title: `30px` to `38px`;
  - subtitle: `18px` to `24px`;
  - axis/tick labels: `16px` to `20px`;
  - annotations and legends: `16px` to `22px`.
- Use `tabular` or monospaced numerals where the renderer supports it.

Color semantics:

- Equity: blue.
- Drawdown: red or muted red.
- Gross PnL: muted blue or gray-blue.
- Net PnL: green when positive and red when negative.
- Cost: orange or amber.
- Winning trade marker: green.
- Losing trade marker: red.
- Entry marker/line: blue.
- Exit marker/line: green for profitable exit, red for losing exit, gray for neutral/time exit.
- Stop line: red dashed line.
- Target line: green dashed line.
- Avoid one-note palettes. Do not make every chart a variation of the same hue.

Annotation and overlap rules:

- Long annotations belong in a reserved annotation band below or beside the plot, not over candles or equity curves.
- Keep chart titles short. Use the HTML report for long interpretation.
- Put legends outside the plotting area when they compete with data.
- If entry, exit, stop, and target labels would overlap, keep the colored lines and markers, then move the detailed values into a compact annotation band.
- If right-edge labels overlap, offset them vertically, abbreviate them, or omit lower-priority labels. Do not allow text to stack on top of other text.
- If a chart needs many labels, use numbered callouts on the plot and a small legend outside the plot.
- Before finishing, inspect every generated image for clipped text, hidden axes, overlapping labels, and cramped titles.

No-crop QA:

- Confirm the final PNG dimensions match the intended canvas.
- Confirm no plot element is cut off at the image edge.
- Confirm all axis labels and tick labels are visible.
- Confirm stop/target/entry/exit labels, when shown, remain inside the safe area.
- Confirm padding was added rather than cropping when aspect ratio conversion was needed.

## Image 1: summary_equity_curve.png

Create:

```text
summary_equity_curve.png
```

Purpose:

This is the main performance chart for the report summary and result sections.

Requirements:

- Show equity curve and drawdown in the same image.
- Do not create a separate `drawdown_curve.png` unless explicitly requested.
- Use a two-panel layout.
- Upper panel: equity curve.
- Lower panel: drawdown or underwater curve.
- Use the main run selected for the report.
- Annotate the chart with strategy name, market/symbol, timeframe, period, total return, max drawdown, total trades, win rate, and expectancy if available.
- Keep the chart readable in a blog post.

Chart title format:

```text
[Strategy Name] Equity Curve - [Symbol] [Timeframe], [Period]
```

## Image 2: cost_impact.png

Create:

```text
cost_impact.png
```

Purpose:

This image shows how transaction costs affected performance.

Preferred chart type:

- Use a line chart if equity curves by cost level are available.
- Use a bar chart if only aggregate PnL/cost totals are available.

If equity curves are available, plot:

```text
no cost equity
fee only equity
fee + spread equity
fee + spread + slippage equity
```

If only aggregate values are available, plot:

```text
gross PnL
fee
spread
slippage
net PnL
```

Required annotations:

- total fee.
- total spread.
- total slippage.
- total transaction cost.
- gross PnL.
- net PnL.
- final return after costs.

Chart title format:

```text
Transaction Cost Impact - [Strategy Name], [Symbol] [Timeframe]
```

Do not use the phrase `cost stress` in chart titles or labels.

## Image 3: representative_win_trade.png

Create:

```text
representative_win_trade.png
```

Purpose:

This image shows one representative winning trade.

Chart type:

- Candlestick chart when candle-window data is available.
- Clear fallback trade-metadata chart when candle-window data is unavailable.

Required elements when available:

- candles around the trade window with enough surrounding context.
- entry marker.
- exit marker.
- stop line.
- target line.
- pattern or signal zone.
- side: Long or Short.
- entry price.
- exit price.
- entry time.
- exit time.
- hold duration.
- gross PnL, transaction cost, and net PnL.
- local volume context.
- candle body/range or realized movement near entry.
- whether price followed through, reversed, or chopped after entry.
- nearby drawdown or equity state if available.
- exit reason.

Representative trade viewport contract:

- Use `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png` as the reference style for representative trade charts: surrounding candles are visible, entry/exit lines are clear, and dense trade metrics sit in a separate lower annotation band instead of covering candles.
- Do not zoom only to the entry and exit candles.
- Include pre-entry and post-exit context so the reader can see the setup, follow-through, reversal, or chop.
- Minimum context window:
  - include the full entry-to-exit span;
  - add at least `10` candles before entry and `10` candles after exit when available;
  - if the trade lasts longer than `20` candles, use at least `30%` of the trade length before entry and after exit, capped at a readable window;
  - if fewer candles are available, use all available surrounding candles and record the limitation in the payload narrative, not in the chart title.
- The y-axis must include local high/low plus entry, exit, stop, and target prices with padding. Do not cut off stop or target lines just to make the candles look larger.
- If the full context window makes candles too dense, keep the context and reduce x-axis tick density instead of cropping the window.

Trade selection priority:

1. Use the explicitly provided `representative_trades.best_trade`.
2. If unavailable, select a winning trade that is easy to explain.
3. Do not select a trade only because it has the largest profit if it is not representative of the strategy logic.
4. Prefer a trade where the pattern, entry, and exit are visually clear.

Title format:

```text
Representative Winning Trade - [Side], [Entry Time]
```

## Image 4: representative_loss_trade.png

Create:

```text
representative_loss_trade.png
```

Purpose:

This image shows one representative losing trade.

Chart type:

- Candlestick chart when candle-window data is available.
- Clear fallback trade-metadata chart when candle-window data is unavailable.

Required elements when available:

- candles around the trade window with enough surrounding context.
- entry marker.
- exit marker.
- stop line.
- target line.
- failed pattern or signal zone.
- side: Long or Short.
- entry price.
- exit price.
- entry time.
- exit time.
- hold duration.
- gross PnL, transaction cost, and net PnL.
- local volume context.
- candle body/range or realized movement near entry.
- whether price followed through, reversed, or chopped after entry.
- nearby drawdown or equity state if available.
- exit reason.

Representative trade viewport contract:

- Use the same viewport, padding, annotation-band, and no-crop rules as `representative_win_trade.png`.
- Do not zoom only to the losing entry and stop/exit candles.
- Include pre-entry and post-exit candles so the reader can see whether the loss came from false signal, immediate reversal, slow chop, time exit, or cost drag.
- The y-axis must include local high/low plus entry, exit, stop, and target prices with padding.
- If labels overlap, keep the price lines and markers but move detailed values into the annotation band.

Trade selection priority:

1. Use the explicitly provided `representative_trades.worst_trade`.
2. If unavailable, select a losing trade that explains the main weakness of the strategy.
3. Prefer a trade that shows false signal, immediate reversal, weak higher-timeframe alignment, stop hit before target, high transaction cost, time exit loss, or short-side concentration.
4. Do not select a visually confusing trade unless it is the only available loss example.

Title format:

```text
Representative Losing Trade - [Side], [Entry Time]
```

## Optional Images

Create these only when they improve report usefulness and source data is available:

```text
price_with_trades.png
trade_pnl_distribution.png
side_attribution.png
exit_reason_attribution.png
10_equity_curve_[number]_[timeframe]_[period-slug]_[variant-slug].png
20_cost_impact_[number]_[timeframe]_[period-slug]_[variant-slug].png
30_win_trade_[number]_[timeframe]_[period-slug]_[variant-slug].png
40_loss_trade_[number]_[timeframe]_[period-slug]_[variant-slug].png
```

Rules:

- Optional images are colocated with `payload.json`.
- Payload image references must be filename-only.
- Variant number must be two digits, such as `01`.
- Timeframe slug examples: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`.
- Period slug uses `YYYYMMDD_YYYYMMDD`.
- Variant slug uses lowercase letters, numbers, and underscores only.

## Final Checks

Before finishing image generation:

- Confirm `payload.json` exists.
- Confirm `summary_equity_curve.png` exists.
- Confirm `cost_impact.png` exists.
- Confirm `representative_win_trade.png` exists.
- Confirm `representative_loss_trade.png` exists.
- Confirm every required PNG is in the same directory as `payload.json`.
- Confirm no `images/` subdirectory was generated.
- Confirm no `report-en.html`, `report-en.md`, `image_plan.md`, or `image_plan.json` was generated.
- Confirm `report-ko.html`, if present, was not modified by the image generation step.
- Confirm every equity curve image includes drawdown in the same image.
- Confirm no separate `drawdown_curve.png` was generated unless explicitly requested.
- Confirm every payload image path is filename-only.
- Confirm the HTML report can later reference every generated image as `./[filename].png`.
- Confirm every generated PNG matches its intended canvas dimensions.
- Confirm no resize/crop operation cut off titles, axes, tick labels, legends, stop/target lines, entry/exit markers, or annotations.
- Confirm representative trade charts include pre-entry and post-exit candle context when candle data exists.
- Confirm representative trade y-axis ranges include entry, exit, stop, target, and local high/low with padding.
- Confirm labels do not overlap. If overlap remains, regenerate with a larger annotation band, fewer labels, external legend, or compact numbered callouts.
- Confirm dense metrics are in an annotation band rather than placed over candles.
