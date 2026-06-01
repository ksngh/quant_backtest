# Task 303: Daily Report Interpretation Style Workflow Revision

# Goal

Revise the daily-report prompt, workflow, and style documentation so future Korean daily reports use the owner's preferred interpretation-centered structure and wording.

The desired output is not just a one-off edit to the existing Lookback Return Momentum report. It is a reusable rule update: future report writers must avoid awkward setup/result/conclusion phrasing, remove unnecessary mentions of absent artifacts or unavailable data from the main narrative, and make the interpretation section synthesize what was tested, what happened, and what can be improved next.

# Source Requirement

Owner request, summarized from Korean feedback on the existing `Lookback Return Momentum V1` daily report:

```text
지금 데일리 리포트 형식과 말투를 수정하고자 해. 넌 하위 내용을 담은 task를 만들어줘.

Lookback Return Momentum V1은 Binance BTCUSDT에서 최근 완료봉 수익률이 기준을 넘으면 같은 방향으로 진입하는 기초 모멘텀 전략입니다.
-> Remove the exchange/symbol from this sentence when the surrounding report context already identifies it.

수익 곡선은 두 타임프레임 모두 아래로 이동했습니다.
-> Prefer natural Korean such as "수익 곡선은 두 타임프레임 모두 하락세를 보였습니다."

핵심은 거래비용입니다.
-> Avoid over-dramatic standalone framing when the next sentence can explain the cost result directly.

사용 지표와 패턴 ... 패턴 없음 ... 필터 조건 없음
-> Do not include pattern/filter rows when they are absent. Do not use the title "사용 지표와 패턴" for this case. Explain it in prose instead:
   "지표는 최근 N개 완료봉의 close-to-close 수익률을 사용했고, 진입 방향은 Long / Short 입니다."

별도 변인별 이미지는 만들지 않았습니다.
-> Do not mention artifacts that were not created unless the absence itself is decision-relevant.

거래 수가 많았고 비용 누적이 순손실 대부분을 차지했습니다.
-> For the 1m row, keep the key point tighter: "비용 누적이 순손실 대부분을 차지했습니다."

거래 수는 줄었지만 비용 반영 후 기대값이 음수였습니다.
-> For the 15m row, prefer: "비용 반영 후 기대값은 여전히 음수였습니다."

이 구조에서는 신호가 조금 맞아도 비용을 넘기 어렵습니다.
-> "조금 맞다" is awkward; replace with more specific language about gross edge, signal quality, turnover, threshold, hold window, and cost burden.

이번 구간은 첫 진단 구간이며, 5분봉은 local closed candles가 없어 비교하지 못했습니다.
-> "진단 구간" is awkward. Remove the local-candle explanation from the main narrative. If needed, move 5m coverage to a later improvement item, e.g. add 5m and compare once local closed candles are available.

대표 수익 거래와 손실 거래에는 당시 상황을 더 묘사하는게 좋을 거 같아. 뭐 거래량이 어쨌고, 그런 요인까지 추가해야 다음 실험에 더 잘 써먹을 듯.

해석에서는 결론을 빼고, 이번 실험은 어떤걸 실험하려고 했고, 결과가 어땠고, 어떤걸 추가하거나 제거해서 보완할 수 있을 거 같다라는 말이 필요하다. 위의 모든 내용이 다 해석에서 정리가 되어야한다.

여러 문서와 workflow를 확인하고 이렇게 결과가 나올 수 있도록 프롬프트와 워크플로와 문서들을 수정해줘.
```

Clean requirement:

- Create and later implement a bounded documentation/workflow update for daily-report format and tone.
- Update the prompt/workflow/style/template docs that guide Korean daily-report creation.
- Make reports interpretation-centered: all setup, metric, chart, trade-example, and follow-up sections should support the final interpretation instead of ending with a generic conclusion.
- Avoid mentioning absent patterns, filters, images, or missing intervals unless they matter for the reader's decision; if they matter, place them in limitations or improvements rather than the lead narrative.
- Make representative win/loss trade writeups more contextual by including available market-state evidence such as volume, candle range/body, volatility, nearby drawdown/equity context, entry/exit timing, hold duration, cost share, and whether the move followed through or faded.

# Extracted Roles

- Owner role:
  - Defines preferred Korean daily-report voice, structure, and interpretation depth.
  - Wants the reusable report-generation workflow changed, not only the existing report patched.
- Supporting roles:
  - Documentation workflow role: update daily-report workflow docs and handoff prompts.
  - Style-guide role: encode preferred Korean phrasing and forbidden/avoid rules.
  - Template role: adjust report section guidance so interpretation synthesizes experiment intent, result, causes, and next improvements.
  - Data-rule role: clarify which contextual trade fields should be captured when available.
  - Status-tracking role: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` after execution.
- Forbidden roles:
  - No new backtest execution.
  - No parameter tuning/search.
  - No strategy/model implementation.
  - No candle backfill.
  - No saved-run DB mutation.
  - No image generation unless a future implementation task explicitly requires regenerating examples.
  - No report artifact rewrite unless explicitly kept within this task scope during implementation.
  - No frontend/backend/API changes.
  - No live trading behavior.
  - No exchange order/account/private endpoints.
  - No secrets or `.env` changes.

# Context

- Task 289 created the initial daily-report workflow docs.
- Tasks 290-295 evolved payload/image/report artifact rules.
- Task 300 wired `docs/blog/DAILY_REPORT_TEMPLATE.md` and `docs/blog/DAILY_REPORT_STYLE.md` into the daily-report flow.
- Task 301 generated the first `Lookback Return Momentum V1` report artifact.
- Task 302 improved readability of that report but did not fully encode the owner's newer interpretation/tone requirements into the reusable workflow.
- The owner now wants the report rules, prompts, and workflow changed so future reports naturally produce the requested style.

# Scope

Read required project state first, then inspect the relevant report and documentation context:

- `AGENTS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `STATUS.md`
- this task file
- `docs/blog/DAILY_REPORT_TEMPLATE.md`
- `docs/blog/DAILY_REPORT_STYLE.md`
- `docs/blog/daily_report_workflow.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/image_generation_prompt.md`
- `docs/10_CODEX_COMMAND_GUIDE.md` if command routing or owner prompt handling is touched
- `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/report-ko.md` as the concrete reference example
- `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json` only as needed to understand currently available context fields

Allowed documentation changes:

- Update `docs/blog/DAILY_REPORT_STYLE.md` with owner-preferred Korean copy rules, including examples of wording to avoid and replacements to prefer.
- Update `docs/blog/DAILY_REPORT_TEMPLATE.md` so report sections emphasize interpretation and follow-up learning rather than a generic conclusion.
- Update `docs/blog/daily_report_workflow.md` so the report writer checks for absent-pattern/filter/artifact wording, trade-context depth, and interpretation synthesis before finalizing.
- Update `docs/blog/agent_handoff_prompt.md` so future handoffs instruct the writing agent to produce the revised tone and structure.
- Update `docs/blog/backtest_report_data_rules.md` if additional optional contextual fields are needed for representative trade descriptions.
- Update `docs/blog/image_generation_prompt.md` only if the representative trade chart caption/annotation instructions need to support richer trade context.
- Optionally update `docs/10_CODEX_COMMAND_GUIDE.md` if the owner-command routing needs an explicit reference to the revised daily-report writing rules.
- Update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` after execution.

# Out of Scope

- Do not run a backtest.
- Do not tune, search, validate, or modify a strategy/model.
- Do not backfill candles or mutate saved run data.
- Do not regenerate PNG images.
- Do not create a new daily report artifact unless the implementation task explicitly includes a bounded example update.
- Do not rewrite unrelated reports.
- Do not change source code unless a later assigned task explicitly requests automation or schema support.
- Do not change frontend/backend/API areas.
- Do not add live trading controls or behavior.
- Do not call exchange order/account/private endpoints.
- Do not add secrets or `.env` files.

# Requirements

## Report voice and phrasing rules

- Prefer concise, natural Korean over literal translations or awkward research jargon.
- Avoid over-explaining already-known context in the lead sentence. For example, do not repeat `Binance BTCUSDT` inside the strategy definition when the report metadata/context already identifies the market.
- Prefer natural performance wording:
  - Use "수익 곡선은 ... 하락세를 보였습니다" instead of "아래로 이동했습니다".
  - Use "마쳤습니다" where it reads more naturally than "끝났습니다".
- Avoid dramatic standalone pivots such as "핵심은 거래비용입니다" when a direct metric sentence can explain the same point.
- Avoid vague or awkward expressions such as:
  - "신호가 조금 맞아도"
  - "진단 구간"
  - "이번 결과를 전략 우위로 일반화하기는 어렵습니다" when it functions as a generic conclusion rather than a concrete interpretation.
- Remove the generic final "결론" section unless the template has a specific owner-requested decision section. Prefer an "해석" section that already includes experiment intent, observed result, likely cause, and next improvements.

## Absent pattern/filter/artifact rules

- Do not render table rows for absent concepts such as:
  - `패턴: 없음`
  - `필터 조건: 없음`
- Do not use the heading "사용 지표와 패턴" when no pattern exists.
- For indicator-only strategies, state the setup in prose, for example:
  - "지표는 최근 N개 완료봉의 close-to-close 수익률을 사용했고, 진입 방향은 Long / Short 입니다."
- Do not mention images or variant artifacts that were not created, unless their absence affects interpretation.
- Do not place missing local candle coverage in the lead narrative. If relevant, record it under limitations or next improvements, such as adding `5m` once local closed candles are available.

## Metric/table wording rules

- Timeframe comparison rows should be short and interpretation-focused.
- For the `1m` momentum example, prefer wording equivalent to:
  - "비용 누적이 순손실 대부분을 차지했습니다."
- For the `15m` momentum example, prefer wording equivalent to:
  - "비용 반영 후 기대값은 여전히 음수였습니다."
- Keep metric tables readable and avoid repeating the same numbers across multiple sections unless the repetition supports a new interpretation.

## Representative trade context rules

- Representative win/loss trade descriptions should describe the market situation when the data is available.
- The workflow should ask the report writer to look for and include useful context such as:
  - entry/exit timestamp and side,
  - hold duration,
  - gross PnL versus fee/spread/slippage share,
  - candle body/range or realized movement near entry,
  - recent volume compared with local baseline,
  - whether the move continued, reversed, or chopped after entry,
  - nearby drawdown/equity-curve state,
  - why the trade is representative of the strategy's behavior.
- If volume or other context is unavailable, do not invent it. State only what is present or omit the unavailable factor.

## Interpretation section rules

- The interpretation section must synthesize the full report rather than repeat a generic conclusion.
- It should clearly answer:
  1. What did this experiment try to test?
  2. What happened in the saved results?
  3. Why does the result appear to have happened, using concrete metrics and trade examples?
  4. What should be added, removed, or changed in the next experiment?
- For cost-dominated momentum reports, discuss possible improvements in concrete terms, such as:
  - reducing turnover,
  - increasing the return threshold,
  - changing hold windows,
  - adding liquidity/volume or volatility filters,
  - adding `5m` comparison once local closed candles are available,
  - excluding conditions where gross edge is too small relative to costs.
- Keep the research/live-trading boundary, but avoid a boilerplate final conclusion that sounds detached from the preceding analysis.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md`.
- [ ] Read `STATUS.md`.
- [ ] Confirm Task 303 is the assigned task.
- [ ] Read this task file before implementation.
- [ ] Read the relevant daily-report docs.
- [ ] Read the current `Lookback Return Momentum V1` report as a concrete reference example.
- [ ] Record assumptions, blockers, or unclear status items before editing docs.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append a concise Task 303 completion note to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md`.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Daily-report documentation now encodes the owner's revised Korean tone and interpretation-centered structure.
- The docs tell future report writers not to include absent pattern/filter rows or absent-artifact mentions by default.
- The docs tell future report writers to treat missing `5m`/local-candle coverage as a limitation or next-improvement item rather than lead narrative copy.
- The docs tell future report writers to enrich representative win/loss trade descriptions with available market context and not invent unavailable context.
- The docs tell future report writers to replace generic final conclusions with an interpretation section that covers experiment intent, observed result, likely causes, and next improvements.
- The workflow/prompt docs remain consistent with the colocated `payload.json`/PNG/`report-ko.md` artifact contract.
- No backtest, parameter tuning/search, strategy/code change, candle backfill, DB mutation, image generation, frontend/backend/API change, live trading behavior, exchange order/account/private endpoint behavior, secret, or `.env` change is performed.
- State files are updated after execution.

# Required Tests

## Unit Tests

- Not applicable unless reusable helper code is introduced. Avoid helper code for this documentation-only task.

## Integration Tests

- Not applicable unless reusable report-generation code is introduced. Avoid new reusable code for this documentation-only task.

## Contract Tests

Recommended:

```bash
rg -n "사용 지표와 패턴|패턴: 없음|필터 조건: 없음|진단 구간|신호가 조금 맞|별도 변인별 이미지는 만들지 않았습니다|결론" docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/DAILY_REPORT_STYLE.md docs/blog/daily_report_workflow.md docs/blog/agent_handoff_prompt.md docs/blog/backtest_report_data_rules.md docs/blog/image_generation_prompt.md
rg -n "close-to-close|대표 수익 거래|대표 손실 거래|거래량|해석|보완|5m|local closed" docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/DAILY_REPORT_STYLE.md docs/blog/daily_report_workflow.md docs/blog/agent_handoff_prompt.md docs/blog/backtest_report_data_rules.md docs/blog/image_generation_prompt.md
```

The first command should be interpreted carefully: it may intentionally find forbidden examples inside a "do not use" list, but it must not find docs recommending those phrases as normal output.

## Safety Tests

Recommended:

```bash
! rg -n "api_key|secret|ENABLE_LIVE_TRADING|signed order|order endpoint|account endpoint|private endpoint" docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/DAILY_REPORT_STYLE.md docs/blog/daily_report_workflow.md docs/blog/agent_handoff_prompt.md docs/blog/backtest_report_data_rules.md docs/blog/image_generation_prompt.md
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Blog/data/image contract respected.
- No report data invented.
- No new backtest execution.
- No parameter tuning/search.
- No strategy/code change.
- No candle backfill or DB mutation.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.

# Verification

Default:

```bash
git diff --check -- docs/blog/DAILY_REPORT_TEMPLATE.md docs/blog/DAILY_REPORT_STYLE.md docs/blog/daily_report_workflow.md docs/blog/agent_handoff_prompt.md docs/blog/backtest_report_data_rules.md docs/blog/image_generation_prompt.md docs/10_CODEX_COMMAND_GUIDE.md STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_303_DAILY_REPORT_INTERPRETATION_STYLE_WORKFLOW_REVISION.md
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
