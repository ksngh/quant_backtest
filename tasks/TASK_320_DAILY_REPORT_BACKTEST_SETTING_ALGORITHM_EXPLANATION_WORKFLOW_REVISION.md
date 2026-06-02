# Task 320: DAILY_REPORT_BACKTEST_SETTING_ALGORITHM_EXPLANATION_WORKFLOW_REVISION

# Goal

Revise the reusable Korean daily-report workflow so every future `백테스트 설정` section explains how each tested rule actually works, including concise code-like pseudocode or Python-style snippets for entry/exit logic and indicator calculations such as lookback-return momentum and ATR.

# Source Requirement

Owner request on 2026-06-02:

> 백테스트 설정에는 해당하는 로직이 어떻게 작동하는지를 써줘야해.
> 가령, 최근 완료봉 구간 수익률이 기준 이상이면 같은 방향으로 진입이라고 하는데, 이거에 대한 알고리즘이 어떻게 작동하는지 코드로 작성을 해줘.
> ATR같은 지표들도 어떻게 산출하는지 코드로 작성을 해줘.

Interpreted as: create a bounded future documentation/workflow task. The implementation should update reusable report-generation guidance so the `백테스트 설정` section includes readable algorithm descriptions and compact code snippets for the strategy rules and indicators used in the report. It must not change strategy code or run backtests.

# Extracted Roles

- Owner role:
  - Requests a more concrete `백테스트 설정` section that explains rule mechanics, not only parameter names.
  - Wants examples such as lookback-return threshold entry and ATR calculation to be expressed in code-like form.
- Supporting roles:
  - Daily-report workflow maintainer: update reusable `docs/blog` workflow/template/style/handoff/data-rule documents.
  - Quant explanation writer: translate strategy/backtest rules into safe, readable Korean explanations and pseudocode.
  - Verification role: confirm docs require code-like snippets for rule mechanics while preserving research-only boundaries.
- Forbidden roles:
  - Backtest runner.
  - Parameter tuner/searcher.
  - Strategy/code implementer.
  - Indicator implementation modifier.
  - Existing report artifact regenerator.
  - Current report narrative editor unless a separate current-artifact task is assigned.
  - Database mutator.
  - Candle backfill runner.
  - Frontend/backend/API implementer.
  - Live trader or real Binance order executor.

# Context

Recent report workflow tasks improved Tistory layout and interpretation language, but the owner now wants the `백테스트 설정` section to explain the actual mechanics behind labels such as `최근 완료봉 구간 수익률이 기준 이상이면 같은 방향으로 진입` and indicators such as `ATR`.

This task should only create the future workflow change. If implemented later, it should make report writers include algorithmic explanations derived from saved run metadata, strategy docs, and source code where available. It must not invent logic that is absent from the tested strategy.

# Scope

- Read required state files and this task before implementation.
- Read current reusable daily-report docs/template before editing:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/report_template.html` only if code-block styling guidance needs a small update.
- Update reusable report workflow guidance so future `백테스트 설정` sections include:
  - plain-language rule summary;
  - the specific parameters used in the saved run;
  - concise code-like pseudocode or Python-style snippets showing how the rule is evaluated;
  - an explanation of candle indexing and no-lookahead assumptions, especially the use of recently completed candles rather than future candles;
  - indicator calculation snippets when indicators drive entry, exit, sizing, cost guard, or filtering decisions.
- Include a reusable example for lookback-return momentum entry logic, using a generic pattern such as:

```python
lookback_return = close[t - 1] / close[t - 1 - lookback_bars] - 1

if lookback_return >= min_return_threshold:
    signal = "long"
elif allow_short and lookback_return <= -min_return_threshold:
    signal = "short"
else:
    signal = "flat"
```

- Include reusable ATR calculation guidance, using a generic pattern such as:

```python
true_range = max(
    high[t] - low[t],
    abs(high[t] - close[t - 1]),
    abs(low[t] - close[t - 1]),
)
atr = rolling_mean(true_range, window=atr_period)
```

- Require code snippets to be labeled as explanatory pseudocode unless copied exactly from source.
- Require source-code citations or file references in generated reports when the snippet is meant to mirror implemented behavior.
- Update state files after execution.

# Out of Scope

- Editing existing `reports/**/report-ko.html`, `reports/**/report-ko.md`, `reports/**/payload.json`, or PNG artifacts.
- Regenerating current report images.
- Running, changing, or tuning any backtest.
- Strategy logic changes.
- Indicator implementation changes.
- Backtest engine changes.
- Strategy document changes unless a separate assigned strategy task requires them.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Dashboard, FastAPI, Streamlit, scheduler, Docker, machine learning, futures, leverage, or portfolio optimization work.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- Future reports must not leave `백테스트 설정` as only a table of parameter names and values when those parameters define important logic.
- The workflow must require code-like snippets for:
  - entry trigger logic;
  - exit trigger logic if rule-based exits are present;
  - indicator calculations that materially influence entries/exits/filters;
  - transaction-cost or cost-feasibility guards when they are central to the tested result.
- Snippets must be short enough for a blog reader and must not expose implementation internals unrelated to the report.
- The workflow must distinguish exact source-derived code from explanatory pseudocode.
- The workflow must require no-lookahead clarity:
  - which candle is the current decision candle;
  - which candle range is used for the lookback calculation;
  - when the entry is assumed filled;
  - how intrabar stop/target ambiguity is handled if relevant and available.
- The workflow must require indicator snippets to define inputs, windows, and edge cases such as insufficient warm-up bars.
- The workflow must preserve the research-only boundary and must not frame algorithm snippets as live-trading instructions.

# Status Tracking

## Before Implementation

- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md`.
- [ ] Read `STATUS.md`.
- [ ] Read this task.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm this is documentation/workflow work only, not strategy/backtest implementation.
- [ ] Record assumptions, blockers, or unclear status items before editing.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append completion progress to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Reusable daily-report docs require future `백테스트 설정` sections to explain how tested rules work, not merely list parameter values.
- The docs require concise code-like snippets or pseudocode for entry logic, exit logic when relevant, and material indicators such as ATR.
- The docs include no-lookahead/candle-indexing guidance for lookback-return calculations.
- The docs include warm-up/input/window guidance for indicators such as ATR.
- The docs distinguish explanatory pseudocode from exact implementation code.
- Existing report artifacts, payloads, images, backtests, strategy/code, database records, live trading behavior, exchange endpoints, secrets, and `.env` files remain unchanged.

# Required Tests

## Unit Tests

- Not required; this is a reusable documentation/workflow task.

## Integration Tests

- Not required unless implementation changes executable code, which is out of scope.

## Contract Tests

Run documentation checks:

```bash
rg -n "백테스트 설정|lookback_return|ATR|true_range|pseudocode|의사코드|완료봉|진입|청산" docs/blog
```

Run diff validation:

```bash
git diff --name-only
git diff --check
```

## Safety Tests

Run:

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_320_DAILY_REPORT_BACKTEST_SETTING_ALGORITHM_EXPLANATION_WORKFLOW_REVISION.md
```

Expected: no unsafe live-trading/order/secret behavior is introduced; declarative safety text in task/state files is acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Code snippets are explanatory and bounded to report mechanics.

# Verification

Default:

```bash
rg -n "백테스트 설정|lookback_return|ATR|true_range|pseudocode|의사코드|완료봉|진입|청산" docs/blog
git diff --name-only
git diff --check
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_320_DAILY_REPORT_BACKTEST_SETTING_ALGORITHM_EXPLANATION_WORKFLOW_REVISION.md
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
