# Task 289: Daily Backtest Blog Template And Agent Handoff

# Goal

Create a concise Korean markdown template and supporting handoff documents for daily quant backtest write-ups.

The template must be short enough to use every day, but it must still preserve the essential research narrative:

- strategy hypothesis.
- economic meaning.
- mathematical expectancy.
- backtest setup.
- results.
- possible misleading effects.
- representative trades.
- interpretation.
- conclusion.

The task must also define how a backtest runner should save the data needed for this template and how another agent should receive that data to write the blog-style report.

# Source Requirement

Owner request:

```text
아래 요구사항을 기반으로 `template.md` 파일을 작성해줘.

목표는 퀀트 백테스트 결과를 매일 기록하기 위한 블로그/문서용 템플릿을 만드는 것이다.

이 템플릿은 너무 길면 안 된다. 매일 작성할 수 있을 정도로 간결해야 한다.
다만 전략의 가설, 경제적 의미, 수학적 기대값, 백테스트 설정, 결과, 착시 가능성, 대표 거래, 해석, 결론은 빠지면 안 된다.

문서 톤은 존댓말로 작성한다.
AI가 쓴 티가 나는 표현은 피한다.
불필요한 메타 설명은 넣지 않는다.
“단순히”라는 표현은 쓰지 않는다.
“질문에서 출발한다” 같은 표현은 쓰지 않는다.
가설은 “~할 것이다” 형태로 작성한다.

아래 항목은 넣지 않는다.

* 실험 ID
* 데이터 버전
* 실험 config
* 산출물 경로
* git commit
* 산출 파일
* 체크리스트
* 부록
* 다음 실험 내용
* “다음 조건을 만족해야 한다” 같은 과한 조건 나열

git commit 대신 PR 항목만 남긴다.

각 섹션에는 반드시 작성 예시를 포함한다.
예시는 실제 작성자가 나중에 내용을 바꿔 넣을 수 있도록 `[ ]` placeholder와 실제 문장 예시를 함께 제공한다.

... 블로그에 글을 작성할건데, 너가 이제 백테스트를 한 번 돌리고 그 결과를 저장시킨다음에 그 결과를 agents에 전달시킬거거든? 저기 내용에 들어가야할 데이터들을 저장하는 규칙과 프롬프트를 생성해서 어디다가 저장해놔봐.
```

Clean requirement:

- Create a daily backtest blog/report template named `template.md`.
- Keep the template concise and usable for daily writing.
- Include all owner-required sections and examples.
- Write in Korean honorific style.
- Avoid AI-like phrasing and the explicitly forbidden expressions.
- Exclude the explicitly forbidden metadata sections.
- Keep `PR` and do not include `git commit`.
- Add data-saving rules for the fields that must be passed from a backtest run to the writing agent.
- Add an agent handoff prompt that can turn the saved payload into a completed blog/report draft.
- Do not run backtests or implement new strategy behavior in this task.

Owner clarification after initial completion:

```text
ㄴㄴ 내가 어떤 전략으로 daily report 써달라고하면 그 워크플로우를 탈 수 있도록 규칙을 정의해줘.
```

Additional clean requirement:

- Define the operational workflow rules for future owner requests like "`[전략명]으로 daily report 써줘`".
- Clarify how Codex should route the request depending on whether a backtest payload already exists, whether a saved DB run exists, or whether a new backtest must be run first.
- Store the workflow rules in a dedicated document under `docs/blog/`.
- Do not run a backtest, generate a report, or change application code in this clarification step.

# Extracted Roles

- Owner role:
  - Wants a reusable daily report template for quant backtest results.
  - Wants a clean handoff path from saved backtest result data to another agent that writes the report.
- Supporting roles:
  - Documentation designer: create the final markdown template.
  - Quant report editor: keep the sections concise while preserving hypothesis, economics, expectancy, results, and interpretation.
  - Data contract writer: define the fields a backtest result payload must store for this template.
  - Agent prompt writer: write a reusable prompt for a future agent that receives the saved payload and fills the template.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No strategy implementation.
  - No backtest execution.
  - No DB schema migration unless a later implementation task explicitly assigns it.
  - No frontend/backend/API/dashboard changes.
  - No live trading.
  - No exchange order/account/private endpoints.
  - No API keys, secrets, or `.env` changes.

# Context

The project has been running repeated BTCUSDT 1m backtests and saving research results. The owner now wants a daily writing workflow:

1. Run a backtest.
2. Save the result data needed for a human-readable blog/report.
3. Pass that saved payload to an agent.
4. Have the agent write a concise Korean report using a stable template.

Existing research reports under `reports/` are detailed validation documents. This task is different: it creates a shorter daily blog/report format and a data handoff convention.

Suggested document location:

- `docs/blog/template.md`
- `docs/blog/backtest_report_data_rules.md`
- `docs/blog/agent_handoff_prompt.md`
- `docs/blog/daily_report_workflow.md`

The implementation may create `docs/blog/` if it does not exist.

# Scope

- Create:
  - `docs/blog/template.md`
  - `docs/blog/backtest_report_data_rules.md`
  - `docs/blog/agent_handoff_prompt.md`
  - `docs/blog/daily_report_workflow.md`
- The template must follow the owner-provided structure and include:
  - `# [전략명] 백테스트 리포트`
  - `## 1. 핵심 요약`
  - `## 2. 가설`
  - `## 3. 전략에 포함된 가정과 이론적 배경`
  - `## 4. 전략 규칙`
  - `## 5. 백테스트 설정`
  - `## 6. 결과`
  - `## 7. 착시 가능성`
  - `## 8. 대표 거래`
  - `## 9. 해석`
  - `## 10. 결론`
- Each section must include:
  - placeholder format using `[ ]`.
  - at least one realistic example sentence.
- The data rules document must define:
  - required fields.
  - optional fields.
  - field naming convention.
  - data type expectations.
  - what must not be included.
  - how graph/image references should be provided without turning them into a metadata-heavy artifact section.
  - how PR should be stored.
  - how representative trades should be selected.
  - how cost, slippage, and expectancy fields should be captured.
- The agent handoff prompt must define:
  - input payload shape.
  - writing constraints.
  - banned expressions.
  - required sections.
  - output format.
  - instruction to keep the report concise.
  - instruction not to invent missing data.
- The daily report workflow document must define:
  - owner request patterns.
  - required routing decisions.
  - when to use an existing payload.
  - when to create a payload from an existing saved run.
  - when a new backtest task is required before report writing.
  - what Codex may and may not do automatically.
  - the exact handoff order from strategy request to final markdown report.

# Out of Scope

- No backtest execution.
- No strategy development.
- No Task 288 implementation.
- No database migration.
- No code changes to backtest persistence.
- No frontend/backend/API/dashboard changes.
- No automatic blog publishing.
- No image generation.
- No live trading.
- No exchange order/account/private endpoints.
- No API keys, secrets, or `.env` changes.

# Requirements

## Template Requirements

- File path: `docs/blog/template.md`.
- The template must be written in Korean.
- Tone must be polite Korean, using 존댓말.
- The writing must feel like a human research note, not a generic AI answer.
- Keep the template concise enough for daily use.
- Do not include unnecessary meta explanations.
- Do not include these sections or labels:
  - `실험 ID`
  - `데이터 버전`
  - `실험 config`
  - `산출물 경로`
  - `git commit`
  - `산출 파일`
  - `체크리스트`
  - `부록`
  - `다음 실험 내용`
- Do not include the expression `단순히`.
- Do not include the expression `질문에서 출발한다`.
- Do not include wording like `다음 조건을 만족해야 한다` in the final template.
- Include `PR` instead of `git commit`.
- Hypotheses must use the `~할 것이다` form.
- The first line under `## 1. 핵심 요약` must follow:

```text
[총 거래 수] trades. [승률]% win rate. [핵심 성과 한 줄].
```

- The next sentence must follow:

```text
[전략명]은 [시장/심볼/타임프레임]에서 [핵심 조건]을 기준으로 테스트했을 때, [핵심 결과]를 보였습니다.
```

- Include a graph image line:

```markdown
![백테스트 결과 그래프](./images/[graph-name].png)
```

- Include these subsections in `## 1. 핵심 요약`:
  - `The setup:`
  - `The numbers:`
  - `The kicker:`

## Required Template Content

The final template must include, in concise form:

- 핵심 요약.
- two hypotheses only.
- strategy assumptions.
- economic meaning.
- mathematical expectancy formula:

```text
E[R] = P(win) × AvgWin - P(loss) × AvgLoss - Cost
```

- short definitions for:
  - `P(win)`
  - `AvgWin`
  - `P(loss)`
  - `AvgLoss`
  - `Cost`
- strategy rules:
  - patterns and indicators.
  - long entry conditions.
  - short entry conditions.
  - exit conditions.
  - cost assumptions.
- backtest settings.
- OHLCV execution assumption.
- result metrics.
- possible misleading effects or illusions:
  - cost illusion.
  - outlier trade dependence.
  - window dependence.
  - low trade count.
  - long/short side concentration.
  - intrabar ambiguity.
- representative trades:
  - best trade.
  - worst trade.
  - typical winning trade.
  - typical losing trade.
- interpretation.
- conclusion.

## Data-Saving Rules Requirements

File path: `docs/blog/backtest_report_data_rules.md`.

The data rules must define a compact payload that can be saved after a backtest and passed to an agent.

The payload must include fields for:

- report title fields:
  - strategy name.
  - market/symbol/timeframe.
  - period.
  - PR.
- graph references:
  - equity curve image filename.
  - optional drawdown image filename.
- setup:
  - exchange.
  - symbol.
  - market.
  - timeframe.
  - initial capital.
  - position sizing.
  - entry conditions summary.
  - exit conditions summary.
  - cost assumptions.
- hypothesis and theory:
  - two hypotheses.
  - assumptions.
  - economic meaning.
  - expectancy components.
- metrics:
  - total trades.
  - win rate.
  - total return.
  - final equity.
  - max drawdown.
  - profit factor.
  - expectancy.
  - Sharpe.
  - Sortino.
  - average win.
  - average loss.
  - fee total.
  - slippage total.
  - spread total if available.
- illusion checks:
  - cost sensitivity.
  - outlier dependence.
  - window dependence.
  - trade count quality.
  - side concentration.
  - same-candle ambiguity.
- representative trades:
  - best trade.
  - worst trade.
  - typical winner.
  - typical loser.
- interpretation:
  - one-paragraph result interpretation.
  - one-paragraph risk/limitation interpretation.
  - final conclusion.

The data rules must explicitly say not to store or pass these fields for the blog-writing payload:

- experiment ID.
- data version.
- full experiment config.
- artifact path.
- git commit.
- generated output file list.
- checklist.
- appendix.
- next experiment content.
- secrets or credentials.

If the underlying system needs run IDs or config internally, those may stay in DB or internal logs, but they must not be included in the blog-writing payload or final report template.

## Agent Handoff Prompt Requirements

File path: `docs/blog/agent_handoff_prompt.md`.

The prompt must instruct a future agent to:

- Read a saved backtest-report payload.
- Fill `docs/blog/template.md`.
- Keep the writing concise.
- Use Korean honorific style.
- Use the exact supplied data.
- Do not invent missing metrics.
- Use `[확인 필요]` for missing required content.
- Avoid AI-like generic expressions.
- Avoid the banned expressions:
  - `단순히`
  - `질문에서 출발한다`
- Keep hypotheses in `~할 것이다` form.
- Exclude forbidden metadata sections.
- Include `PR` and not `git commit`.
- Preserve graph markdown if image filename is present.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read this task file.
- [x] Confirm Task 289 is the assigned documentation task before creating `docs/blog/` files.
- [x] Confirm no implementation/backtest/live-trading/API/frontend scope is needed.
- [x] Record assumptions, blockers, or unclear status items before editing docs.

## After Implementation

- [x] Update `STATUS.md` with Task 289 outcome and next task.
- [x] Append Task 289 completion or blocker summary to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark Task 289 completed, blocked, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `docs/blog/template.md` exists.
- `docs/blog/backtest_report_data_rules.md` exists.
- `docs/blog/agent_handoff_prompt.md` exists.
- `docs/blog/daily_report_workflow.md` exists.
- The template includes all required sections and examples.
- Every section in the template includes both `[ ]` placeholders and realistic example sentences.
- The template is concise enough for daily use.
- The template is written in Korean honorific style.
- The template does not include the forbidden metadata sections.
- The template does not include `git commit`; it includes `PR`.
- The template does not include the banned expressions.
- Hypotheses use the `~할 것이다` form.
- The data rules document defines a compact handoff payload and excludes forbidden fields.
- The agent prompt can be copied and used by another agent without extra project context.
- The workflow document defines how future owner requests for strategy-specific daily reports should route through payload lookup, optional payload creation, and report generation without silently running new backtests.
- No strategy implementation, backtest execution, live trading, exchange endpoint, secret, frontend, backend, or DB schema behavior is added.

# Required Tests

## Unit Tests

- No code unit tests are required for this documentation-only task.

## Integration Tests

- No integration tests are required for this documentation-only task.

## Contract Tests

- Manually verify the data-rules document does not imply DB schema changes.
- Manually verify the handoff prompt excludes forbidden metadata from final output.
- Manually verify the workflow document does not authorize unassigned backtest execution.

## Safety Tests

- Verify no live trading, exchange order/account/private endpoint, API key, secret, or `.env` instruction is added.
- Verify the prompt tells agents not to invent missing data.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract remains documentation-only.
- No hardcoded secrets.
- No real order execution.
- No backend/frontend/API scope creep.
- No unnecessary abstractions.
- Template is concise.
- Template includes all owner-required sections.
- Examples are usable and easy to replace.
- Forbidden expressions and forbidden metadata sections are absent from the final template.

# Verification

Default documentation verification:

```bash
test -f docs/blog/template.md
test -f docs/blog/backtest_report_data_rules.md
test -f docs/blog/agent_handoff_prompt.md
test -f docs/blog/daily_report_workflow.md
rg -n "git commit|실험 ID|데이터 버전|실험 config|산출물 경로|산출 파일|체크리스트|부록|다음 실험 내용|단순히|질문에서 출발한다|다음 조건을 만족해야 한다" docs/blog/template.md
git diff --check
```

The `rg` command above should return no matches for `docs/blog/template.md`.

# Execution Summary

- Created `docs/blog/template.md`.
- Created `docs/blog/backtest_report_data_rules.md`.
- Created `docs/blog/agent_handoff_prompt.md`.
- Created `docs/blog/daily_report_workflow.md` after owner clarification.
- The template includes all required daily report sections, `[ ]` placeholders, and realistic examples.
- The template keeps `PR` and omits the forbidden metadata sections.
- The template includes strategy hypotheses, economic meaning, expectancy formula, backtest setup, results, possible misleading effects, representative trades, interpretation, and conclusion.
- The data rules document defines a compact handoff payload for saved backtest results without requiring a DB schema change.
- The handoff prompt instructs a future writing agent to use only supplied payload values, keep Korean honorific tone, avoid banned expressions, and mark missing data as `[확인 필요]`.
- The workflow document defines request routing for future owner prompts such as "`[전략명]으로 daily report 써줘`", including existing-payload, existing-run, and no-run cases.
- No backtest execution, strategy implementation, DB migration, frontend/backend/API change, live trading, exchange endpoint, secret, or `.env` behavior was added.

# Verification Results

```bash
test -f docs/blog/template.md
test -f docs/blog/backtest_report_data_rules.md
test -f docs/blog/agent_handoff_prompt.md
test -f docs/blog/daily_report_workflow.md
# passed

rg -n "git commit|실험 ID|데이터 버전|실험 config|산출물 경로|산출 파일|체크리스트|부록|다음 실험 내용|단순히|질문에서 출발한다|다음 조건을 만족해야 한다" docs/blog/template.md
# no matches

rg -n "# \[전략명\] 백테스트 리포트|## 1\. 핵심 요약|## 2\. 가설|## 3\. 전략에 포함된 가정과 이론적 배경|## 4\. 전략 규칙|## 5\. 백테스트 설정|## 6\. 결과|## 7\. 착시 가능성|## 8\. 대표 거래|## 9\. 해석|## 10\. 결론|The setup:|The numbers:|The kicker:|PR:" docs/blog/template.md
# passed

git diff --check
# passed
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
