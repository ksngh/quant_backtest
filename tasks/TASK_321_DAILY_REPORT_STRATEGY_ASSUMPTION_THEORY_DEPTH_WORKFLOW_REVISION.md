# Task 321: DAILY_REPORT_STRATEGY_ASSUMPTION_THEORY_DEPTH_WORKFLOW_REVISION

# Goal

Revise the reusable Korean daily-report workflow so every future `전략에 포함된 가정과 이론적 배경` section explains the strategy thesis more concretely, including mechanisms, assumptions, limitations, and optional math formulas instead of merely naming academic references.

# Source Requirement

Owner request on 2026-06-02:

> 전략에 포함된 가정과 이론적 배경에도 조금 더 구체적인 내용이 필요해.
> 필요시 수학식을 적어줘도 좋고, 가령,
> Jegadeesh and Titman(1993)의 가격 모멘텀 연구와 Moskowitz, Ooi, and Pedersen(2012)의 시계열 모멘텀 연구는 최근 수익률이 이후 수익률과 연결될 수 있다는 넓은 배경을 제공합니다.
>
> 라고 했는데 위 가격 모멘텀 연구들에는 어떤 이유때문에 모멘텀이 발생했는지 써주잖아.
>
> 행동재무학적 해석 ... underreaction ...
> 리스크 프리미엄 해석 ... tail risk ...
> 투자자 제약과 느린 포지션 조정 ...
> 헤저와 투기자의 구조 ... speculators가 time series momentum에서 이익을 얻고, 그 이익이 hedgers의 비용으로 발생 ...
>
> 레퍼런스만 가져오는게 아니라 위의 원론적인 내용을 반영할 수 있도록 작성해야해.

Interpreted as: create a bounded future documentation/workflow task. The implementation should update reusable report-generation guidance so theory/background sections explain why a strategy might work, why it might fail, and what assumptions the test is making. References should be used as anchors, not as a substitute for mechanism-level explanation.

# Extracted Roles

- Owner role:
  - Requests deeper theoretical explanation in report strategy-background sections.
  - Wants mechanisms such as underreaction, risk-premium/tail-risk, slow institutional adjustment, and hedger/speculator structure reflected where relevant.
- Supporting roles:
  - Daily-report workflow maintainer: update reusable `docs/blog` workflow/template/style/handoff/data-rule documents.
  - Quant research explainer: provide mechanism-level guidance and optional math notation for strategy assumptions.
  - Verification role: confirm docs require concrete mechanisms and limitations, not reference-name dropping.
- Forbidden roles:
  - Backtest runner.
  - Parameter tuner/searcher.
  - Strategy/code implementer.
  - Existing report artifact regenerator.
  - Current report narrative editor unless a separate current-artifact task is assigned.
  - Academic literature scraper beyond what is needed for reusable guidance.
  - Database mutator.
  - Candle backfill runner.
  - Frontend/backend/API implementer.
  - Live trader or real Binance order executor.

# Context

The current report workflow already includes a section for `전략에 포함된 가정과 이론적 배경`, but the owner wants it to move beyond broad references. For momentum reports, mentioning Jegadeesh and Titman (1993) or Moskowitz, Ooi, and Pedersen (2012) should be accompanied by an explanation of candidate mechanisms:

- behavioral underreaction to new information;
- gradual information diffusion and delayed buying/selling pressure;
- risk-premium interpretations and crash/tail-risk exposure;
- institutional constraints and slow position adjustment;
- hedger/speculator demand imbalance in futures-like markets where applicable.

This task should update reusable workflow guidance only. It must not claim any theory is proven by the current Bitcoin backtest unless saved evidence supports that claim.

# Scope

- Read required state files and this task before implementation.
- Read current reusable daily-report docs/template before editing:
  - `docs/blog/daily_report_workflow.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/DAILY_REPORT_TEMPLATE.md`
  - `docs/blog/DAILY_REPORT_STYLE.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/report_template.html` only if section-structure wording needs a small update.
- Update reusable report workflow guidance so future `전략에 포함된 가정과 이론적 배경` sections include:
  - the strategy's core assumption in plain Korean;
  - a mechanism-level explanation for why that assumption might hold;
  - at least one plausible failure mechanism or adverse regime;
  - optional math notation when it clarifies the assumption;
  - a clear boundary between literature-backed intuition and evidence from the current backtest.
- For momentum-family reports, add reusable guidance to cover relevant mechanisms when appropriate:
  - underreaction / delayed information incorporation;
  - continuation from slow capital reallocation or institutional constraints;
  - risk-premium and tail-risk interpretation;
  - hedger/speculator pressure for markets where that structure is relevant;
  - limits of applying equity/futures momentum literature directly to spot Bitcoin.
- Add example formulas only as explanatory templates, such as:

```text
r_t^{(L)} = P_t / P_{t-L} - 1
signal_t = sign(r_t^{(L)})
```

and, where useful:

```text
E[r_{t+1} | r_t^{(L)} > \theta] > E[r_{t+1} | r_t^{(L)} \le \theta]
```

- Require reports to avoid overclaiming causality from a backtest result. A report may say a result is consistent or inconsistent with a mechanism, but must not say the mechanism is proven without separate evidence.
- Update state files after execution.

# Out of Scope

- Editing existing `reports/**/report-ko.html`, `reports/**/report-ko.md`, `reports/**/payload.json`, or PNG artifacts.
- Regenerating current report images.
- Running, changing, or tuning any backtest.
- Strategy logic changes.
- Strategy document changes unless a separate assigned strategy task requires them.
- Formal literature review or exhaustive citation database creation.
- Database mutation.
- Candle backfill.
- Frontend/backend/API changes.
- Dashboard, FastAPI, Streamlit, scheduler, Docker, machine learning, futures, leverage, or portfolio optimization work.
- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, private endpoints.
- Secrets or `.env` changes.

# Requirements

- Future reports must not rely on sentence patterns that only list papers or named effects without explaining the underlying mechanism.
- The workflow must require each theory/background section to answer, in integrated prose:
  - What assumption does the strategy make about future price behavior?
  - What market behavior could cause that assumption to hold?
  - What risk or market regime could break the assumption?
  - What does the current backtest actually test, and what does it not test?
- For momentum reports, the workflow should include reusable Korean explanation patterns for:
  - behavioral underreaction: new information is initially underpriced and gradually incorporated;
  - risk-premium/tail-risk: momentum may earn compensation for bearing reversal/crash risk;
  - slow position adjustment: institutions and large participants rebalance gradually because of liquidity, risk limits, benchmark constraints, approvals, hedging needs, or regulation;
  - hedger/speculator structure: speculators may earn returns by taking the other side of hedgers' risk-transfer demand, where the tested market/instrument makes that analogy appropriate.
- The workflow must require caveats when applying equity/futures academic mechanisms to spot Bitcoin.
- Any math should be optional, short, and explained in words immediately after the formula.
- The workflow must preserve research-only framing and must not imply live-trading readiness or guaranteed profitability.

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

- Reusable daily-report docs require future theory/background sections to explain mechanisms, assumptions, failure modes, and evidence boundaries.
- Momentum-specific workflow guidance includes underreaction, risk-premium/tail-risk, slow position adjustment, and hedger/speculator structure where relevant.
- The docs require caveats when importing equity/futures literature into Bitcoin spot backtest interpretation.
- The docs permit concise math formulas and require plain-language explanations of those formulas.
- Existing report artifacts, payloads, images, backtests, strategy/code, database records, live trading behavior, exchange endpoints, secrets, and `.env` files remain unchanged.

# Required Tests

## Unit Tests

- Not required; this is a reusable documentation/workflow task.

## Integration Tests

- Not required unless implementation changes executable code, which is out of scope.

## Contract Tests

Run documentation checks:

```bash
rg -n "전략에 포함된 가정|이론적 배경|underreaction|과소반응|리스크 프리미엄|tail risk|헤저|투기자|모멘텀|수학식" docs/blog
```

Run diff validation:

```bash
git diff --name-only
git diff --check
```

## Safety Tests

Run:

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_321_DAILY_REPORT_STRATEGY_ASSUMPTION_THEORY_DEPTH_WORKFLOW_REVISION.md
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
- Theory explanations do not overclaim causality or live-trading readiness.

# Verification

Default:

```bash
rg -n "전략에 포함된 가정|이론적 배경|underreaction|과소반응|리스크 프리미엄|tail risk|헤저|투기자|모멘텀|수학식" docs/blog
git diff --name-only
git diff --check
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\.env" docs/blog STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_321_DAILY_REPORT_STRATEGY_ASSUMPTION_THEORY_DEPTH_WORKFLOW_REVISION.md
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
