# [Strategy Name] [Version] Strategy Document

## 1. Strategy Identity

- Strategy name:
- Strategy version:
- Strategy slug:
- Stable strategy description:
- Owner task:
- Status: `research_only`
- Last updated:

## 2. Market and Data Scope

- Exchange:
- Market:
- Symbol:
- Primary timeframe:
- Higher timeframes:
- Intended test period:
- Required data:
- Known data limitations:

## 3. Market Phenomenon

Describe the price behavior this strategy tries to capture.

- Phenomenon:
- Why it may appear in BTC:
- Economic or microstructure rationale:
- Behavioral rationale:
- Expected market regime:
- Regimes where this should not work:
- Report-ready summary:

## 3.1 Theory and References

This section is required before generating a full daily/Tistory report for this strategy.

- Why this strategy might have an edge:
- What market mechanism it assumes:
- What participant behavior it assumes:
- Why the chosen timeframe can expose the mechanism:
- When the theory should fail:
- References:
  - `[reference id]`:
    - Title:
    - Author/source:
    - Year/date:
    - Link or local path:
    - Why it matters for this strategy:

## 4. Hypothesis

Write the hypothesis in testable form.

- Primary hypothesis: `[...할 것이다.]`
- Secondary hypothesis: `[...할 것이다.]`

## 5. Factors and Indicators

List only factors that are needed to observe the phenomenon.

| Factor | Formula / Definition | Required Data | Expected Direction | Confounders |
|---|---|---|---|---|
|  |  |  |  |  |

## 6. Pattern or Signal Logic

- Pattern name:
- Long signal interpretation:
- Short signal interpretation:
- Confirmation condition:
- Invalid setup condition:
- Look-ahead prevention rule:
- Report-facing rule summary:

## 7. Entry Logic

Long entry:

-

Short entry:

-

Execution timing:

- Signal candle:
- Execution candle:
- Market/limit assumption:
- Same-candle entry/exit rule:

## 8. Exit Logic

- Stop loss:
- Take profit:
- Time exit:
- Early exit:
- Opposite signal handling:
- Stop/target same-candle priority:

## 9. Risk and Position Sizing

- Position sizing:
- Risk per trade:
- Max concurrent positions:
- Long/short constraints:
- Cash/margin assumptions:
- Research-only constraints:

## 10. Cost and Execution Assumptions

- Entry fee:
- Exit fee:
- Round-trip fee:
- Spread:
- Slippage:
- Minimum slippage:
- Volatility slippage:
- Fee-adjusted break-even:
- Slippage-adjusted break-even:

## 11. Expected Value

```text
E[R] = P(win) x AvgWin - P(loss) x AvgLoss - Cost
```

- Expected win rate:
- Expected average win:
- Expected average loss:
- Expected R multiple:
- Required break-even win rate:
- Minimum acceptable trade count:
- Cost and reward/risk explanation for reports:

## 12. Validation Plan

- In-sample window:
- Out-of-sample window:
- Walk-forward windows:
- Multi-timeframe checks:
- Fee stress:
- Slippage stress:
- Outlier removal:
- Random/baseline comparison:
- Buy-and-hold comparison:
- Long-only and short-only attribution:
- Regime/session attribution:

## 13. Failure Modes

- Cost-dominated failure:
- Low trade-count failure:
- Side concentration:
- Outlier dependence:
- Choppy regime:
- Trend regime:
- High-volatility execution distortion:
- Same-candle ambiguity:

## 14. Required Artifacts

- Saved backtest runs:
- Trade log:
- Equity curve:
- Cost breakdown:
- Representative win/loss trades:
- Daily report payload:
- Daily report images:
- Draft report:

## 15. Implementation Notes

- Files/modules expected to change:
- Reusable components:
- Tests required:
- Backward compatibility concerns:
- Data persistence notes:

## 16. Safety Boundary

- This strategy is research-only unless a later task explicitly changes that status.
- This strategy must not call exchange order/account/private endpoints.
- This strategy must not require secrets, API keys, or `.env` changes.
- This strategy must not place real orders.
- Live trading remains out of scope.

## 17. Change Log

-
