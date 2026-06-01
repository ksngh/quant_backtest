# Daily Report Workflow Rules

이 문서는 사용자가 특정 전략에 대해 daily report, report body, payload, 또는 리포트용 이미지 생성을 요청했을 때 따라야 하는 워크플로우 규칙입니다.

목표는 요청이 들어올 때마다 같은 순서로 판단하고, 필요한 데이터가 있을 때만 `payload.json`, 리포트용 PNG 이미지, 블로그에 투고할 수 있는 한국어 본문 `report-ko.md`를 생성하는 것입니다.

## 1. 적용되는 요청

다음과 같은 요청에 적용합니다.

- "`[전략명]`으로 daily report payload 만들어줘"
- "`[전략명]` daily report 작성해줘"
- "`[전략명]` 백테스트 리포트 만들어줘"
- "`[전략명]` 백테스트 결과 그래프 뽑아줘"
- "`[run id 또는 저장된 결과]`로 블로그용 payload와 이미지 만들어줘"
- "방금 돌린 백테스트 결과를 daily report 형식으로 저장해줘"
- "기존 payload/images 지우고 다시 생성해줘"

요청에 전략명, run id, 저장된 payload, 또는 방금 실행한 백테스트 결과가 포함되어 있으면 이 워크플로우를 사용합니다.

## 2. 기본 원칙

- payload 구조는 `docs/blog/backtest_report_data_rules.md`를 따릅니다.
- 이미지 생성 세부 규칙은 `docs/blog/image_generation_prompt.md`를 따릅니다.
- 작성 에이전트용 프롬프트는 `docs/blog/agent_handoff_prompt.md`를 기준으로 합니다.
- `report-ko.md`를 작성할 때는 먼저 `docs/blog/DAILY_REPORT_TEMPLATE.md`와 `docs/blog/DAILY_REPORT_STYLE.md`를 읽습니다.
- `docs/blog/DAILY_REPORT_TEMPLATE.md`는 섹션 구조와 이미지 배치 기준입니다.
- `docs/blog/DAILY_REPORT_STYLE.md`는 말투, 금지 표현, 내부 용어 변환, 해석 방식 기준입니다.
- full report workflow의 기본 산출물은 `payload.json`, PNG 이미지, `report-ko.md`입니다.
- `report-en.md`, `image_plan.md`, `image_plan.json`은 기본 생성하지 않습니다.
- `images/` 하위 폴더를 만들지 않습니다.
- 모든 PNG 이미지는 `payload.json`과 같은 디렉터리에 둡니다.
- payload의 이미지 참조는 파일명만 사용합니다.
- `report-ko.md`에서 이미지를 참조할 때는 같은 폴더 기준 `./[filename].png`를 사용합니다.
- 제공되지 않은 값은 추정하지 않습니다.
- 누락된 필수 값은 `[확인 필요]`로 남깁니다.
- 새 백테스트 실행은 별도 task 또는 명시적 실행 지시가 있을 때만 합니다.
- 저장된 결과가 없으면 payload나 이미지를 꾸며서 만들지 않습니다.
- 내부 추적값은 payload, 이미지 파일명, chart title에 쓰지 않습니다.
- task 번호, run id, 내부 candidate id는 report folder, 이미지 파일명, 그래프 제목, `report-ko.md` 본문에 쓰지 않습니다.
- live trading, 실제 주문, private endpoint, secret 사용은 하지 않습니다.

## 3. 요청을 받으면 먼저 분류합니다

### A. payload가 이미 제공된 경우

처리:

1. payload가 `docs/blog/backtest_report_data_rules.md` 구조에 맞는지 확인합니다.
2. 이미지 파일명이 filename-only인지 확인합니다.
3. 이미지가 이미 있으면 같은 폴더에 존재하는지 검증합니다.
4. 이미지가 필요하고 source data가 있으면 같은 폴더에 PNG를 생성합니다.
5. full report 요청이면 payload와 PNG를 사용해 `report-ko.md` 본문을 생성합니다.
6. 새 백테스트를 실행하지 않습니다.

### B. 저장된 run id가 제공된 경우

처리:

1. 저장된 run 결과를 읽을 수 있는지 확인합니다.
2. run 결과에서 daily report payload를 만들 수 있는지 확인합니다.
3. report artifact folder를 정합니다.
4. 같은 목적의 기존 `payload.json`과 PNG가 있으면 삭제 후 재생성합니다.
5. 부족한 값은 `[확인 필요]`로 남깁니다.
6. `payload.json`을 저장합니다.
7. 생성 가능한 PNG를 `payload.json`과 같은 디렉터리에 저장합니다.
8. `docs/blog/agent_handoff_prompt.md`, `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/DAILY_REPORT_STYLE.md`를 기준으로 `report-ko.md` 본문을 저장합니다.
9. 최종 검증을 통과한 뒤 경로와 생성 파일을 기록합니다.

주의:

- run id 자체는 최종 블로그 문서나 report-facing payload에 쓰지 않습니다.
- 내부 추적용으로만 사용합니다.
- 저장된 run에서 필요한 값이 부족하면 새로 만들어내지 않습니다.

### C. 전략명만 제공된 경우

처리:

1. 같은 전략명의 최신 saved payload가 있는지 찾습니다.
2. payload가 있으면 A 흐름으로 진행합니다.
3. payload는 없지만 저장된 backtest run이 있으면 B 흐름으로 진행합니다.
4. 저장된 결과가 없으면 리포트 artifact 생성 전에 백테스트 실행 task와 관련 `docs/strategy/*.md`가 필요하다고 기록합니다.

이 경우 전략명만으로 새 백테스트를 자동 실행하지 않습니다.

### D. "방금 돌린 결과"가 문맥에 있는 경우

처리:

1. 현재 대화 또는 직전 작업에서 생성된 payload나 saved run을 확인합니다.
2. 확인 가능한 payload가 있으면 A 흐름으로 진행합니다.
3. 확인 가능한 saved run이 있으면 B 흐름으로 진행합니다.
4. 확인 가능한 결과가 없으면 어떤 결과를 사용할지 요청합니다.

## 4. 데이터 확인 순서

리포트 artifact 생성 전 아래 순서로 확인합니다.

1. `backtest_report_payload`가 직접 제공되었는지 확인합니다.
2. 제공된 run id나 저장된 결과 참조가 있는지 확인합니다.
3. 전략명으로 매칭 가능한 최신 saved payload가 있는지 확인합니다.
4. 전략명으로 매칭 가능한 최신 saved run이 있는지 확인합니다.
5. 결과가 없으면 payload/image 생성을 멈추고 백테스트 실행 또는 payload 제공이 필요하다고 알립니다.

## 5. Artifact Folder 생성 순서

데이터가 준비되면 다음 구조를 만듭니다.

```text
reports/blog_payloads/[strategy-slug]/[strategy-version-slug]/[period-slug]/
  payload.json
  report-ko.md
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

규칙:

- `strategy-slug`와 `strategy-version-slug`는 실제 전략명과 버전에서 만듭니다.
- folder, payload, image filename에는 task 번호, run id, 내부 candidate id를 넣지 않습니다.
- `payload.json`은 `docs/blog/backtest_report_data_rules.md` 구조를 따릅니다.
- `report-ko.md`는 `docs/blog/DAILY_REPORT_TEMPLATE.md` 구조와 `docs/blog/DAILY_REPORT_STYLE.md` 문체를 따르는 한국어 리포트 본문입니다.
- 기존 artifact를 같은 목적으로 재생성할 때는 기존 `payload.json`, `report-ko.md`, PNG만 삭제합니다.
- unrelated reports, task reports, DB records는 삭제하지 않습니다.

## 6. 이미지 생성 순서

이미지는 항상 `payload.json`과 같은 디렉터리에 저장합니다.

필수 fixed images:

```text
summary_equity_curve.png
cost_impact.png
representative_win_trade.png
representative_loss_trade.png
```

선택 이미지:

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

`summary_equity_curve.png`는 equity curve와 drawdown을 한 이미지 안에 함께 표시합니다.

`cost_impact.png`는 비용 미반영, 수수료, 스프레드, 슬리피지 반영 효과를 비교합니다. 비용 단계별 equity curve가 없으면 aggregate cost bar chart를 사용합니다.

`representative_win_trade.png`와 `representative_loss_trade.png`는 가능한 경우 candlestick chart로 만들고, candle-window data가 없으면 사용 가능한 trade metadata 기반 fallback chart를 만들며 payload에 그 한계를 남깁니다.

## 7. Report Body 생성 순서

PNG 생성 후 `report-ko.md`를 만듭니다.

규칙:

- `report-ko.md`는 `payload.json`과 같은 디렉터리에 저장합니다.
- `docs/blog/DAILY_REPORT_TEMPLATE.md`의 섹션 구조를 사용합니다.
- `docs/blog/DAILY_REPORT_STYLE.md`의 말투, 금지 표현, 내부 용어 변환, 해석 방식 규칙을 사용합니다.
- `docs/blog/agent_handoff_prompt.md`의 작성 원칙을 따릅니다.
- 존댓말로 씁니다.
- payload에 없는 값은 `[확인 필요]`로 남깁니다.
- 이미지 참조는 `./[filename].png` 형식만 사용합니다.
- task 번호, run id, 내부 candidate id, source file path, DB dump, config dump, git commit은 쓰지 않습니다.
- 연구 전용 또는 실패 전략은 실전 적용 가능하다고 쓰지 않습니다.
- `report-en.md`는 명시 요청이 없으면 만들지 않습니다.

## 8. 최종 검증

artifact 완료 전에 아래를 확인합니다.

- `payload.json` exists.
- `report-ko.md` exists.
- `summary_equity_curve.png` exists.
- `cost_impact.png` exists.
- `representative_win_trade.png` exists.
- `representative_loss_trade.png` exists.
- 모든 필수 PNG는 `payload.json`과 같은 디렉터리에 있습니다.
- `images/` 하위 폴더가 없습니다.
- `report-en.md`, `image_plan.md`, `image_plan.json` 파일이 없습니다.
- 모든 equity curve image는 drawdown을 같은 이미지 안에 포함합니다.
- 별도의 `drawdown_curve.png`는 명시 요청이 없으면 생성하지 않습니다.
- payload의 모든 이미지 `filename`은 `/`가 없는 파일명입니다.
- `report-ko.md`의 모든 이미지 참조는 `./[filename].png` 형식입니다.
- cost impact chart title이나 label에 `cost stress`라는 표현이 없습니다.

## 9. 새 백테스트가 필요한 경우

전략명은 있지만 저장된 결과가 없으면 새 백테스트가 필요합니다.

이때 흐름:

1. 백테스트 실행이 현재 task 범위에 포함되어 있는지 확인합니다.
2. 관련 `docs/strategy/*.md`가 있는지 확인합니다.
3. strategy 문서가 없으면 `docs/strategy/STRATEGY_TEMPLATE.md`를 기준으로 strategy 문서를 만들고 멈춥니다.
4. 백테스트 실행이 현재 task 범위에 포함되어 있지 않으면 새 task가 필요하다고 기록합니다.
5. 백테스트 task가 실행되어 결과가 저장된 뒤 payload, images, `report-ko.md` 본문을 만듭니다.

daily report 요청만으로 새 전략 개발이나 새 백테스트를 자동 실행하지 않습니다.

## 10. 결과 저장 우선순위

백테스트 실행 후 daily report artifact 생성을 예상한다면 결과 저장 시 다음 값을 우선 저장합니다.

- 실제 리포트용 전략명.
- 전략 버전.
- 전략 라벨.
- 시장/심볼/타임프레임.
- 기간.
- PR.
- artifact folder.
- fixed image filenames.
- optional image filenames.
- 진입 조건 요약.
- 청산 조건 요약.
- 비용 조건.
- 총 거래 수.
- 승률.
- 총 수익률.
- 최종 자본.
- 최대 낙폭.
- Profit Factor.
- Expectancy.
- Sharpe.
- Sortino.
- 평균 이익.
- 평균 손실.
- 수수료 총액.
- 슬리피지 총액.
- 스프레드 총액.
- 비용 민감도.
- 아웃라이어 의존도.
- 구간 의존도.
- 거래 수 해석.
- Long/Short 편중.
- 동일 캔들 처리 영향.
- 대표 수익 거래.
- 대표 손실 거래.
- 결과 해석.
- 위험 해석.
- 결론.

필드 이름과 구조는 `docs/blog/backtest_report_data_rules.md`를 따릅니다.

## 11. 작성 에이전트로 넘길 때

payload와 PNG가 준비된 뒤 `report-ko.md` 본문을 작성할 때 `docs/blog/agent_handoff_prompt.md`를 사용합니다.

이때 작성 에이전트는 같은 폴더 기준 `./[filename].png`로 이미지를 참조합니다.

full report workflow에서는 `report-ko.md`를 저장합니다.

payload/image-only 요청이 명시된 경우에만 `report-ko.md` 생성을 생략할 수 있습니다.
