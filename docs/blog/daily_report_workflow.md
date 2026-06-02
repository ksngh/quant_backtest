# Daily Report Workflow Rules

이 문서는 사용자가 특정 전략에 대해 daily report, report body, payload, 리포트용 이미지, 또는 블로그 리포트 HTML 생성을 요청했을 때 따라야 하는 워크플로우 규칙입니다.

목표는 요청이 들어올 때마다 같은 순서로 판단하고, 필요한 데이터가 있을 때만 `payload.json`, 리포트용 PNG 이미지, Tistory에 투고할 수 있는 한국어 HTML 리포트 `report-ko.html`을 생성하는 것입니다.

## 1. 적용되는 요청

다음과 같은 요청에 적용합니다.

- "`[전략명]`으로 daily report payload 만들어줘"
- "`[전략명]` daily report 작성해줘"
- "`[전략명]` 백테스트 리포트 만들어줘"
- "`[전략명]` 백테스트 결과 그래프 뽑아줘"
- "`[run id 또는 저장된 결과]`로 블로그용 payload와 이미지 만들어줘"
- "방금 돌린 백테스트 결과를 daily report 형식으로 저장해줘"
- "기존 payload/images 지우고 다시 생성해줘"
- "블로그에 올릴 HTML 리포트 만들어줘"

요청에 전략명, run id, 저장된 payload, 또는 방금 실행한 백테스트 결과가 포함되어 있으면 이 워크플로우를 사용합니다.

## 2. 기본 원칙

- payload 구조는 `docs/blog/backtest_report_data_rules.md`를 따릅니다.
- 이미지 생성 세부 규칙은 `docs/blog/image_generation_prompt.md`를 따릅니다.
- HTML 작성 에이전트용 프롬프트는 `docs/blog/agent_handoff_prompt.md`를 기준으로 합니다.
- `report-ko.html`을 작성할 때는 먼저 `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/DAILY_REPORT_STYLE.md`, `docs/blog/report_template.html`을 읽습니다.
- `docs/blog/DAILY_REPORT_TEMPLATE.md`는 HTML 섹션 구조와 이미지/표 배치 기준입니다.
- `docs/blog/DAILY_REPORT_STYLE.md`는 말투, 금지 표현, 내부 용어 변환, 해석 방식 기준입니다.
- `docs/blog/report_template.html`은 최종 HTML 레이아웃과 읽기 흐름 기준입니다.
- `report-ko.html`은 Tistory hELLO 스킨 게시용 standalone HTML입니다. 본문 컨테이너 기본 폭은 `1120px`이며, 좁은 Tistory 본문 폭과 모바일에서도 반응형으로 읽혀야 합니다.
- `report-ko.html`은 내부 CSS를 포함한 단일 HTML 파일이어야 하며 외부 CSS에 의존하지 않습니다.
- 최종 HTML은 `docs/blog/report_template.html`의 `.report-page` 컨테이너를 사용합니다. 기본 CSS는 `--page-max-width: 1120px`, `width: calc(100% - 32px)`, `margin: 0 auto`를 따릅니다.
- full report workflow의 기본 산출물은 `payload.json`, PNG 이미지, `report-ko.html`입니다.
- Markdown 파일은 기본 최종 산출물이 아닙니다. 명시적으로 요청된 경우에만 내부 scratch나 legacy export로 다룹니다.
- `report-en.html`, `report-en.md`, `image_plan.md`, `image_plan.json`은 기본 생성하지 않습니다.
- `images/` 하위 폴더를 만들지 않습니다.
- 모든 PNG 이미지는 `payload.json`과 같은 디렉터리에 둡니다.
- payload의 이미지 참조는 파일명만 사용합니다.
- `report-ko.html`에서 이미지 preview를 참조할 때는 같은 폴더 기준 `./[filename].png`를 사용합니다.
- Tistory 최종 게시 단계에서는 owner가 local `<img>`를 Tistory 업로드 토큰으로 다시 삽입할 수 있습니다. 이때 이미지는 `<div class="section-image">[##_Image|...|alignCenter|width="100%"|_##]</div>` 구조에 들어가야 하며, `...`는 실제 게시 시 교체되는 placeholder입니다.
- 제공되지 않은 값은 추정하지 않습니다.
- 누락된 필수 값은 `[확인 필요]`로 남깁니다.
- 새 백테스트 실행은 별도 task 또는 명시적 실행 지시가 있을 때만 합니다.
- 저장된 결과가 없으면 payload나 이미지를 꾸며서 만들지 않습니다.
- 내부 추적값은 payload, 이미지 파일명, chart title, HTML 본문에 쓰지 않습니다.
- task 번호, run id, 내부 candidate id는 report folder, 이미지 파일명, 그래프 제목, `report-ko.html` 본문에 쓰지 않습니다.
- live trading, private API, credential 사용은 하지 않습니다.
- 최종 리포트에는 standalone `가설`, `검증 가설`, `실험 가설`, `Hypothesis` 섹션을 만들지 않습니다. 실험 의도나 테스트한 전제는 `핵심 요약`, `백테스트 설정`, `전략에 포함된 가정과 이론적 배경`, 또는 `해석` 안에 녹입니다.
- 최종 리포트는 결론 섹션으로 닫지 않고, `해석` 섹션에서 실험 의도, 관찰 결과, 원인, 보완점을 연결합니다.
- `해석` 섹션은 테스트한 전략/버전의 결론과 전략군 전체에 대한 결론을 분리합니다.
- 결과가 나쁘면 "현재 버전은 이 조건에서 비용 반영 후 유효한 전략으로 보기 어렵다"는 범위의 결론은 쓸 수 있지만, 저장 근거가 그 폭을 검증하지 않았다면 전략군 전체를 기각하지 않습니다.
- 전략군 전체를 기각하기 이르다고 쓸 때는 구현 버전, 기간, 심볼, 타임프레임, 비용 가정, 파라미터 범위, 빠진 regime/유동성/확인 필터, OOS/WFO 또는 기준선 비교 부족 같은 저장 근거의 경계를 설명합니다.
- 결과가 좋아도 검증 범위가 좁으면 보편적으로 유효하다고 쓰지 않습니다.
- 없는 패턴/필터/이미지/타임프레임은 기본적으로 본문에 쓰지 않습니다. 의사결정에 필요하면 한계나 보완점에만 둡니다.
- report title은 전략명과 버전을 기본으로 합니다. 실험 세부 문구는 main title에 길게 붙이지 않습니다.
- subtitle과 첫 문단은 안정적인 전략 설명으로 시작합니다. 실험에서 바꾼 값은 `핵심 요약` 또는 `해석`에서 다룹니다.
- 전략 버전이나 핵심 메커니즘이 바뀌면 `핵심 요약`에서 이전/현재 차이를 짧게 설명합니다.
- full report 작성 전 관련 `docs/strategy/*.md`에 이론/경제적 근거와 레퍼런스가 있는지 확인합니다. 없으면 report 생성을 멈추고 전략 문서 보강을 먼저 요구합니다.

## 3. 요청을 받으면 먼저 분류합니다

### A. payload가 이미 제공된 경우

처리:

1. payload가 `docs/blog/backtest_report_data_rules.md` 구조에 맞는지 확인합니다.
2. 이미지 파일명이 filename-only인지 확인합니다.
3. 이미지가 이미 있으면 같은 폴더에 존재하는지 검증합니다.
4. 이미지가 필요하고 source data가 있으면 같은 폴더에 PNG를 생성합니다.
5. full report 요청이면 payload와 PNG를 사용해 `report-ko.html`을 생성합니다.
6. 새 백테스트를 실행하지 않습니다.

### B. 저장된 run id가 제공된 경우

처리:

1. 저장된 run 결과를 읽을 수 있는지 확인합니다.
2. run 결과에서 daily report payload를 만들 수 있는지 확인합니다.
3. report artifact folder를 정합니다.
4. 같은 목적의 기존 `payload.json`, `report-ko.html`, PNG가 있으면 삭제 후 재생성합니다.
5. 부족한 값은 `[확인 필요]`로 남깁니다.
6. `payload.json`을 저장합니다.
7. 생성 가능한 PNG를 `payload.json`과 같은 디렉터리에 저장합니다.
8. `docs/blog/agent_handoff_prompt.md`, `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/DAILY_REPORT_STYLE.md`, `docs/blog/report_template.html`을 기준으로 `report-ko.html`을 저장합니다.
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
5. 결과가 없으면 payload/image/HTML 생성을 멈추고 백테스트 실행 또는 payload 제공이 필요하다고 알립니다.
6. 관련 strategy 문서가 있는지 확인합니다.
7. strategy 문서에 stable strategy description, theory/rationale, success/failure conditions, cost/RR context, references가 있는지 확인합니다.
8. strategy 문서가 부족하면 full `report-ko.html` 생성을 멈추고 strategy 문서 보강 task 또는 현재 task 범위의 문서 보강을 먼저 수행합니다.

## 5. Artifact Folder 생성 순서

데이터가 준비되면 다음 구조를 만듭니다.

```text
reports/blog_payloads/[strategy-slug]/[strategy-version-slug]/[period-slug]/
  payload.json
  report-ko.html
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

규칙:

- `strategy-slug`와 `strategy-version-slug`는 실제 전략명과 버전에서 만듭니다.
- folder, payload, image filename에는 task 번호, run id, 내부 candidate id를 넣지 않습니다.
- `payload.json`은 `docs/blog/backtest_report_data_rules.md` 구조를 따릅니다.
- `report-ko.html`은 `docs/blog/report_template.html` 레이아웃, `docs/blog/DAILY_REPORT_TEMPLATE.md` 구조, `docs/blog/DAILY_REPORT_STYLE.md` 문체를 따르는 한국어 HTML 리포트입니다.
- 기존 artifact를 같은 목적으로 재생성할 때는 기존 `payload.json`, `report-ko.html`, PNG만 삭제합니다.
- unrelated reports, task reports, DB records는 삭제하지 않습니다.

## 6. 이미지 생성 순서

이미지는 항상 `payload.json`과 같은 디렉터리에 저장합니다.

이미지 생성 전에 `docs/blog/image_generation_prompt.md`를 읽고 stable visual contract를 적용합니다. 이미지 출력은 매번 같은 기준을 따릅니다.

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

공통 이미지 생성 규칙:

- 기본 canvas는 `summary_equity_curve.png`, `cost_impact.png`, `representative_win_trade.png`, `representative_loss_trade.png` 모두 `1800px x 1000px`로 둡니다. table-heavy optional chart는 `1800px x 1200px`를 사용합니다.
- target size를 맞추기 위해 crop하지 않습니다. target canvas를 직접 만들거나 aspect ratio를 유지한 뒤 padding으로 맞춥니다.
- square thumbnail, center crop, chart content crop 방식은 사용하지 않습니다.
- title, subtitle, axis label, tick label, legend, annotation, entry/exit marker, stop/target line이 이미지 경계에 닿지 않게 outer padding을 둡니다.
- 긴 수치 설명은 plot 안에 넣지 말고 별도 annotation band 또는 HTML 본문/표로 옮깁니다.
- label이 겹치면 낮은 우선순위 label을 생략하거나 numbered callout과 외부 legend를 사용합니다.
- 대표 거래 이미지는 `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png`처럼 주변 candle 시야와 하단 annotation band를 갖는 구도를 기준으로 합니다.
- 대표 거래 이미지는 entry-to-exit 구간만 보여주지 않습니다. candle data가 있으면 entry 전후와 exit 이후 context를 포함합니다.
- 대표 거래의 y-axis는 entry, exit, stop, target, local high/low를 모두 포함하고 padding을 둡니다.

## 7. HTML Report 생성 순서

PNG 생성 후 `report-ko.html`을 만듭니다.

규칙:

- `report-ko.html`은 `payload.json`과 같은 디렉터리에 저장합니다.
- `docs/blog/report_template.html`의 HTML 레이아웃을 사용합니다.
- `docs/blog/DAILY_REPORT_TEMPLATE.md`의 섹션 구조를 사용합니다.
- `docs/blog/DAILY_REPORT_STYLE.md`의 말투, 금지 표현, 내부 용어 변환, 해석 방식 규칙을 사용합니다.
- `docs/blog/agent_handoff_prompt.md`의 작성 원칙을 따릅니다.
- 존댓말로 씁니다.
- payload에 없는 값은 `[확인 필요]`로 남깁니다.
- 이미지 preview 참조는 HTML에서 `./[filename].png` 형식을 사용합니다.
- 모든 이미지는 `<figure class="report-figure"><div class="section-image">...</div><figcaption>...</figcaption></figure>`로 감쌉니다.
- Tistory 게시용으로 이미지를 다시 넣을 때는 `<div class="section-image">[##_Image|...|alignCenter|width="100%"|_##]</div>` 형태를 사용할 수 있게 HTML 구조를 유지합니다. owner가 실제 Tistory 이미지 토큰으로 교체합니다.
- `.section-image`와 내부 이미지/Tistory wrapper는 본문 폭 전체를 사용해야 하며, 작은 고정 폭이나 불필요한 좌우 padding을 두지 않습니다.
- 모든 표는 `<div class="table-scroll">`로 감쌉니다.
- 표는 목적이 분명할 때만 사용합니다. 너무 넓거나 의미가 섞인 표는 여러 개로 나누거나 핵심 열만 남깁니다.
- 표는 왼쪽 정렬을 기본으로 합니다. 숫자 컬럼은 필요한 경우에만 오른쪽 정렬합니다. 가운데 정렬은 기본으로 쓰지 않습니다.
- standalone 가설 section은 만들지 않습니다. 보완점은 `<ul><li>`로 작성하고, bullet marker가 보이는 템플릿 스타일을 유지합니다.
- title은 `strategy_label` 또는 전략명+버전만 사용합니다. `낮은 진입 기준 비교` 같은 실험 세부 문구를 main title에 넣지 않습니다.
- subtitle은 strategy 문서의 stable strategy description을 사용합니다.
- version이나 메커니즘이 바뀐 경우 `핵심 요약`에 이전/현재 차이를 짧게 넣습니다.
- 첫 문단은 전략을 plain language로 설명합니다.
- 첫 문단을 시장/심볼/기간 요약으로 시작하지 않습니다.
- 어색한 `기본값` 비교 라벨, 영어식 micro-heading, 별도 주의사항 기본 섹션을 만들지 않습니다.
- 최종 해석 섹션 제목은 `해석`입니다.
- task 번호, run id, 내부 candidate id, source file path, DB dump, config dump, git commit은 쓰지 않습니다.
- 실패한 전략은 실전 적용 가능하다고 쓰지 않습니다.
- `report-en.html`은 명시 요청이 없으면 만들지 않습니다.
- 전략 소개 문장에 시장/심볼을 반복하지 않습니다. 시장/심볼은 테스트 개요에서 다룹니다.
- 패턴이나 필터가 없으면 빈 표 행을 만들지 않고 prose로 신호와 진입 방향을 설명합니다.
- `전략 규칙`은 별도 기본 섹션으로 만들지 않고 `전략에 포함된 가정과 이론적 배경`에 편입합니다.
- 이론적 배경에는 strategy 문서의 경제적/행동적/시장구조적 근거와 레퍼런스를 반영합니다.
- `5m`처럼 local closed candle coverage가 없어 빠진 비교는 핵심 요약이나 리드 문장이 아니라 한계 또는 보완점에 씁니다.
- 대표 수익/손실 거래는 가능한 근거만 사용해 당시 거래량, 캔들 range/body, 보유 시간, 비용 비중, 진입 후 추세 지속/반전 여부, equity curve/drawdown 맥락을 설명합니다.
- 보완점은 무엇을 바꿀지와 왜 이번 결과가 그 보완을 요구하는지를 함께 설명합니다.
- `그것은`은 최종 리포트 문장에 쓰지 않습니다.
- 이미지가 제공되면 `.section-image` 안에서 본문 폭 전체를 사용하도록 둡니다. HTML에서 작은 고정 폭으로 줄이지 않습니다.

## 8. 최종 검증

artifact 완료 전에 아래를 확인합니다.

- `payload.json` exists.
- `report-ko.html` exists.
- `summary_equity_curve.png` exists.
- `cost_impact.png` exists.
- `representative_win_trade.png` exists.
- `representative_loss_trade.png` exists.
- 모든 필수 PNG는 `payload.json`과 같은 디렉터리에 있습니다.
- `images/` 하위 폴더가 없습니다.
- `report-en.html`, `report-en.md`, `image_plan.md`, `image_plan.json` 파일이 없습니다.
- 모든 equity curve image는 drawdown을 같은 이미지 안에 포함합니다.
- 별도의 `drawdown_curve.png`는 명시 요청이 없으면 생성하지 않습니다.
- payload의 모든 이미지 `filename`은 `/`가 없는 파일명입니다.
- `report-ko.html`의 local preview 이미지 참조는 `./[filename].png` 형식이며, Tistory 게시 전 owner-side image token 교체가 가능하도록 `.section-image` wrapper를 유지합니다.
- `report-ko.html`에는 task 번호, run id, 내부 candidate id가 없습니다.
- cost impact chart title이나 label에 `cost stress`라는 표현이 없습니다.
- main title이 전략명/버전 중심이고 실험 세부 문구로 길어지지 않았습니다.
- subtitle이 전략 자체를 설명합니다.
- `전략 규칙`이 별도 기본 섹션으로 분리되지 않았습니다.
- standalone `가설`/hypothesis 섹션이 없고, 보완점 bullet이 보입니다.
- 표가 목적별로 읽히고, 너무 넓은 경우 스크롤 또는 분할 처리되었습니다.
- 표가 왼쪽 정렬 중심으로 읽히고 숫자 컬럼만 필요 시 오른쪽 정렬됩니다.
- HTML 컨테이너가 hELLO 스킨용 `.report-page`, `--page-max-width: 1120px`, `width: calc(100% - 32px)`를 따릅니다.
- 이미지가 `.section-image img`와 `.report-figure img`에서 `width: 100%`, `max-width: 100%`, `height: auto`로 본문 폭에 맞게 표시됩니다.
- 모든 PNG가 의도한 canvas dimensions를 충족하고, crop으로 잘린 부분이 없습니다.
- 대표 거래 이미지는 주변 candle context가 보이며, entry/exit/stop/target label과 annotation이 서로 겹치지 않습니다.
- strategy 문서의 이론/근거/레퍼런스가 반영되었습니다.
- `그것은` 표현이 없습니다.
- 실패한 버전의 결과를 전략군 전체 기각으로 확대하지 않았습니다.
- 성공한 버전의 결과를 보편적 유효성으로 과장하지 않았습니다.

## 9. 새 백테스트가 필요한 경우

전략명은 있지만 저장된 결과가 없으면 새 백테스트가 필요합니다.

이때 흐름:

1. 백테스트 실행이 현재 task 범위에 포함되어 있는지 확인합니다.
2. 관련 `docs/strategy/*.md`가 있는지 확인합니다.
3. strategy 문서가 없으면 `docs/strategy/STRATEGY_TEMPLATE.md`를 기준으로 strategy 문서를 만들고 멈춥니다.
4. 백테스트 실행이 현재 task 범위에 포함되어 있지 않으면 새 task가 필요하다고 기록합니다.
5. 백테스트 task가 실행되어 결과가 저장된 뒤 payload, images, `report-ko.html`을 만듭니다.

daily report 요청만으로 새 전략 개발이나 새 백테스트를 자동 실행하지 않습니다.

## 10. 결과 저장 우선순위

백테스트 실행 후 daily report artifact 생성을 예상한다면 결과 저장 시 다음 값을 우선 저장합니다.

- 실제 리포트용 전략명.
- 전략 버전.
- 전략 라벨.
- stable strategy description.
- version change summary.
- theory references.
- table purpose notes.
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
- 보완점.

필드 이름과 구조는 `docs/blog/backtest_report_data_rules.md`를 따릅니다.

## 11. 작성 에이전트로 넘길 때

payload와 PNG가 준비된 뒤 `report-ko.html`을 작성할 때 `docs/blog/agent_handoff_prompt.md`를 사용합니다.

이때 작성 에이전트는 같은 폴더 기준 `./[filename].png` preview를 `.section-image` 안에 넣습니다. Tistory 게시 직전 owner가 해당 local image tag를 Tistory `[##_Image|...|alignCenter|width="100%"|_##]` 토큰으로 교체할 수 있어야 합니다.

full report workflow에서는 `report-ko.html`을 저장합니다.

payload/image-only 요청이 명시된 경우에만 `report-ko.html` 생성을 생략할 수 있습니다.
