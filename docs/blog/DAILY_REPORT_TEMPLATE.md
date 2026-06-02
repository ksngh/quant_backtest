# Daily Report HTML Template Guide

이 문서는 full daily report workflow에서 `report-ko.html`을 작성할 때 쓰는 섹션 구조와 배치 규칙입니다.

최종 산출물은 Markdown이 아니라 HTML입니다. `docs/blog/report_template.html`을 기본 레이아웃으로 사용하고, 본문은 `<article class="report-content">` 안에 작성합니다.
Tistory hELLO 스킨 글 본문에 바로 붙여 넣을 수 있는 standalone HTML을 기준으로 합니다. 본문 컨테이너 기본 폭은 `1120px`이며, 허용 범위는 `1100px ~ 1200px`입니다. 모바일과 좁은 Tistory 본문 폭에서도 표와 이미지가 깨지지 않아야 합니다.

## 0. HTML 산출물 규칙

최종 파일:

```text
report-ko.html
```

기본 artifact 구조:

```text
reports/blog_payloads/[strategy-slug]/[strategy-version-slug]/[period-slug]/
  payload.json
  report-ko.html
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

HTML 작성 규칙:

- `docs/blog/report_template.html`의 `<main class="report-page">`, `<header class="report-header">`, `<article class="report-content">` 구조를 사용합니다.
- `{{REPORT_TITLE}}`, `{{REPORT_TYPE}}`, `{{REPORT_SUBTITLE}}` placeholder를 실제 값으로 바꿉니다.
- 첫 문단은 `<p class="lead">`로 작성합니다.
- 이미지 preview는 `<figure class="report-figure"><div class="section-image"><img src="./[filename].png" ...></div><figcaption>...</figcaption></figure>` 구조를 사용합니다.
- Tistory 최종 게시 시 owner가 `<div class="section-image">[##_Image|...|alignCenter|width="100%"|_##]</div>` 형태로 이미지를 다시 삽입할 수 있게 구조를 유지합니다. `...`는 fake/generic placeholder이며 실제 `kage@...` 토큰을 문서에 고정하지 않습니다.
- 모든 표는 `<div class="table-scroll">`로 감쌉니다.
- 지나치게 넓은 표는 한 표에 억지로 넣지 말고 목적별로 나누거나, 핵심 수치만 표에 두고 보조 지표는 문장으로 설명합니다.
- 코드나 수식은 `<pre><code>...</code></pre>`를 사용합니다.
- `report-ko.html`은 `payload.json`과 같은 디렉터리에 있는 PNG만 참조합니다.
- 이미지 경로는 같은 폴더 기준 `./summary_equity_curve.png`처럼 씁니다.
- Markdown 이미지는 최종 리포트에 사용하지 않습니다.
- task 번호, run id, 내부 candidate id, DB dump, source file path, git commit, credential, config dump를 본문에 쓰지 않습니다.

Tistory hELLO 스킨 레이아웃 규칙:

- HTML은 내부 CSS를 포함한 단일 파일입니다. 외부 CSS 파일에 의존하지 않습니다.
- 기본 컨테이너는 `:root { --page-max-width: 1120px; }`와 `.report-page { max-width: var(--page-max-width); width: calc(100% - 32px); margin: 0 auto; }`를 따릅니다.
- 표는 왼쪽 정렬을 기본으로 합니다. 숫자 컬럼만 필요한 경우 오른쪽 정렬합니다.
- 이미지는 본문 폭 전체를 사용할 수 있게 둡니다. `.report-figure img`와 `.section-image img`는 `display: block; width: 100% !important; max-width: 100% !important; height: auto;`를 따릅니다.
- `.section-image`에는 불필요한 좌우 padding이나 고정 width를 넣지 않습니다. Tistory가 생성하는 image wrapper가 들어와도 본문 column을 꽉 채워야 합니다.
- 디자인보다 가독성, 폭, 정렬, 담백함을 우선합니다.

## 1. 헤더

헤더는 `docs/blog/report_template.html`의 기본 구조를 그대로 사용합니다.

```html
<header class="report-header">
  <p class="report-kicker">백테스트 리포트</p>
  <h1 class="report-title">[strategy_label]</h1>
  <p class="report-subtitle">[전략 자체를 설명하는 짧은 문장]</p>
</header>
```

규칙:

- 제목은 전략명과 버전을 우선 사용합니다. 예: `Lookback Return Momentum V1`.
- `낮은 진입 기준 비교`, `비용 민감도 확인`, `후보 증가 여부`처럼 실험 세부 문구를 main title에 붙이지 않습니다.
- 전략 메커니즘이 바뀌어 title에 구분이 필요할 때만 짧게 붙입니다. 예: `Lookback Return Momentum V1 ATR 기준 수정`.
- subtitle은 시장/심볼/기간 나열보다 전략 자체의 핵심 아이디어를 먼저 설명합니다.
- subtitle은 실험 행동을 설명하지 않습니다. `진입 기준을 낮췄을 때 raw 모멘텀 후보가 실제 진입으로 이어지는지 확인했습니다` 같은 문장은 subtitle이 아니라 필요 시 해석 섹션에서 다룹니다.
- Lookback Return Momentum subtitle 예시는 `과거 일정 구간의 수익률을 확인하는 모멘텀 전략`처럼 version이 바뀌어도 유지되는 전략 설명을 사용합니다.
- subtitle이나 첫 문단을 `Binance BTCUSDT ...` 같은 시장/타임프레임 요약으로 시작하지 않습니다.

## 2. 핵심 요약

첫 섹션은 전략 설명과 핵심 결과를 함께 보여줍니다.

```html
<h2>1. 핵심 요약</h2>
<p class="lead">
  [전략명]은 [핵심 신호]를 기준으로 [진입/청산 아이디어]를 검증하는 전략입니다.
  이번 결과에서는 [핵심 관찰 결과]가 나타났습니다.
</p>
```

규칙:

- 첫 문장은 전략이 무엇인지 plain Korean으로 설명합니다.
- version이나 핵심 메커니즘이 바뀐 리포트라면 핵심 요약 안에 짧은 변화 요약을 포함합니다.
- 변화 요약은 결과 해석과 분리합니다. 예: `이전 버전은 손익 기준을 고정 R로 두었고, 이번 버전은 ATR 기준으로 산정합니다.`
- 시장/심볼/기간은 첫 문장에 몰아넣지 말고 설정 표에서 다룹니다.
- 비교 변인은 `1m 설정`, `15m 설정`, `lookback 20 / hold 5`처럼 씁니다.
- 어색하게 `기본값`을 붙이지 않습니다. 정말 기본 파라미터 자체를 논의할 때만 씁니다.
- 영어식 setup/numbers/kicker 스타일 제목을 쓰지 않습니다.
- 핵심 포인트는 전략 결과를 설명해야 합니다. 총 비용 같은 좁은 숫자 하나만 반복하지 않습니다.

대표 이미지:

```html
<figure class="report-figure">
  <img src="./summary_equity_curve.png" alt="백테스트 수익 곡선과 낙폭" loading="lazy">
  <figcaption>수익 곡선과 drawdown을 함께 본 대표 성과 그래프입니다.</figcaption>
</figure>
```

요약 표 예시:

```html
<div class="table-scroll">
  <table>
    <thead>
      <tr>
        <th>항목</th>
        <th>내용</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>시장/심볼</td><td>Binance BTCUSDT</td></tr>
      <tr><td>기간</td><td>2026-05-20 00:00 UTC ~ 2026-05-28 08:15 UTC</td></tr>
      <tr><td>비교 대상</td><td>1m 설정과 15m 설정</td></tr>
      <tr><td>비용 조건</td><td>수수료, 스프레드, 슬리피지 반영</td></tr>
    </tbody>
  </table>
</div>
```

핵심 포인트 예시:

```html
<p>
  핵심은 비용만의 문제가 아니라는 점입니다. 비용 차감 전 손익이 이미 충분하지 않았고,
  비용을 반영하자 기대값이 더 낮아졌습니다.
</p>
```

## 3. 가설 섹션 생략 규칙

최종 daily report에는 standalone `가설`, `검증 가설`, `실험 가설`, `Hypothesis` 섹션을 기본으로 만들지 않습니다.
실험 의도나 테스트한 전제가 독자 이해에 필요하면 `핵심 요약`, `백테스트 설정`, `전략에 포함된 가정과 이론적 배경`, 또는 마지막 `해석` 안에 자연스럽게 녹입니다.

```html
<!-- 사용하지 않음: <h2>가설</h2> -->
```

## 4. 전략에 포함된 가정과 이론적 배경

```html
<h2>2. 전략에 포함된 가정과 이론적 배경</h2>
<p>[전략의 경제적 아이디어]</p>
<ul>
  <li>[우위가 생길 수 있는 이유]</li>
  <li>[성공 조건]</li>
  <li>[실패 조건]</li>
  <li>[비용과 손익비가 작동하는 방식]</li>
</ul>
```

이 섹션은 이론 배경과 전략 규칙을 함께 설명합니다. 별도의 기본 `전략 규칙` 또는 `전략규칙` 섹션을 만들지 않습니다. 진입 조건, 청산 조건, 비용 조건, 반대 신호 처리, 같은 캔들 처리, 시간 청산처럼 결과 해석에 필요한 규칙은 이 섹션의 bullet 또는 짧은 표 안에 포함합니다.

반드시 다룰 내용:

- 이 전략이 어떤 시장 현상을 이용하려는지.
- 왜 그 현상에서 우위가 생길 수 있는지.
- 어떤 경제적, 행동적, 시장구조적 메커니즘을 가정하는지.
- 어떤 시장 조건에서 잘 작동하는지.
- 어떤 시장 조건에서 실패하는지.
- 신호 속도, turnover, 비용, 손익비가 기대값에 어떻게 영향을 주는지.
- 전략 문서에 적힌 근거와 레퍼런스를 사용합니다.
- 전략 문서에 근거와 레퍼런스가 없으면 full report 생성을 멈추고 strategy 문서 보강을 먼저 요구합니다.
- 레퍼런스는 긴 인용문이 아니라 짧은 근거 연결로 씁니다. 예: `Jegadeesh and Titman(1993)의 가격 모멘텀 연구처럼, 정보 반영 지연과 추세 추종은 단기 방향 지속의 근거가 될 수 있습니다.`

모멘텀 전략 예시:

```html
<p>
  Lookback Return Momentum은 최근 수익률이 단기 주문 흐름과 참여자 반응을 일부 요약한다고 봅니다.
  가격이 모든 정보를 즉시 반영하지 않거나, 추세 추종 참여가 이어지면 최근 움직임이 다음 몇 개 봉까지 지속될 수 있습니다.
</p>
<p>
  하지만 빠른 신호는 거래 수를 늘리고 비용 부담을 키웁니다.
  따라서 방향이 일부 맞더라도 평균 후속 움직임이 비용과 손익비를 넘지 못하면 기대값은 낮아집니다.
</p>
```

기대값 수식:

```html
<pre><code>E[R] = P(win) x AvgWin - P(loss) x AvgLoss - Cost</code></pre>
```

## 5. 전략 규칙 편입 규칙

별도 기본 섹션으로 만들지 않습니다. 아래 내용은 `3. 전략에 포함된 가정과 이론적 배경` 안에 편입합니다.

```html
<p>
  지표는 최근 N개 완료봉의 close-to-close 수익률을 사용합니다.
  수익률이 기준 이상이면 Long, 기준 이하이면 Short로 진입합니다.
</p>
```

## 6. 백테스트 설정

```html
<h2>3. 백테스트 설정</h2>
```

포함할 항목:

- 거래소.
- 심볼.
- 시장.
- 기간.
- 타임프레임.
- 비교 대상.
- 초기 자본.
- 포지션 사이징.
- 비용 모델.
- 체결 가정.

규칙:

- 설정은 사실만 씁니다.
- 공개 리포트에서 당연한 backtest 고지를 길게 쓰지 않습니다.
- 실제 주문 여부를 설명하는 자명한 문구는 넣지 않습니다.
- 실패 전략도 실전 적용 가능한 전략처럼 쓰지 않습니다.

## 7. 결과

```html
<h2>4. 결과</h2>
```

기본 하위 섹션:

- `4.1 수익 곡선`
- `4.2 비교 결과`
- `4.3 거래비용 영향`
- `4.4 청산 구성` 또는 결과 해석에 필요한 다른 attribution

규칙:

- 비교 변인이 없으면 변인별 섹션은 생략합니다.
- 변인별 이미지가 없다는 사실은 본문에 일부러 쓰지 않습니다.
- 수치 표는 compact하게 작성합니다.
- 표마다 답하는 질문이 분명해야 합니다. 예: `타임프레임별 비용 반영 후 성과`, `청산 사유별 거래 수`.
- 한 표에 timeframe, 비용, 청산, 기대값, 대표 거래 설명을 모두 섞지 않습니다.
- 열이 많아 의미가 흐려지면 작은 표 여러 개나 짧은 문장으로 나눕니다.
- 넓은 표는 반드시 `<div class="table-scroll">`로 감쌉니다.

비용 영향 예시:

```html
<figure class="report-figure">
  <div class="section-image">
    <img src="./cost_impact.png" alt="거래비용 반영 전후 손익 비교" loading="lazy">
  </div>
  <figcaption>수수료, 스프레드, 슬리피지 반영 전후 손익 차이입니다.</figcaption>
</figure>
<p>
  비용 차감 전 손익이 이미 충분하지 않았고, 비용을 반영하자 순손익과 기대값이 더 낮아졌습니다.
</p>
```

## 8. 대표 거래

```html
<h2>5. 대표 거래</h2>
```

대표 수익 거래:

```html
<h3>대표 수익 거래</h3>
<figure class="report-figure">
  <div class="section-image">
    <img src="./representative_win_trade.png" alt="대표 수익 거래" loading="lazy">
  </div>
  <figcaption>전략이 기대한 구조가 나타난 거래입니다.</figcaption>
</figure>
```

대표 손실 거래:

```html
<h3>대표 손실 거래</h3>
<figure class="report-figure">
  <div class="section-image">
    <img src="./representative_loss_trade.png" alt="대표 손실 거래" loading="lazy">
  </div>
  <figcaption>전략의 약점이 드러난 거래입니다.</figcaption>
</figure>
```

규칙:

- 수익 거래 1개와 손실 거래 1개를 기본으로 씁니다.
- entry/exit timestamp, side, 보유 시간, gross PnL, 비용, net PnL, 진입 후 추세 지속/반전, equity 상태 같은 저장 근거만 사용합니다.
- 거래량, 캔들 body/range, 변동성, drawdown 맥락이 없으면 만들지 않습니다.
- 대표 거래 설명은 성공/실패 원인을 뒷받침해야 합니다.
- 대표 거래 이미지는 entry/exit candle만 확대하지 않고 주변 candle context를 보여줘야 합니다.
- `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png`처럼 trade chart와 하단 annotation band가 분리된 구도를 선호합니다.
- 이미지 자체가 crop되어 있거나 label이 겹쳐 있으면 HTML에서 조정하지 말고 이미지 생성 규칙에 따라 다시 만들어야 합니다.

## 9. 해석

```html
<h2>6. 해석</h2>
```

해석은 별도 결론이 아니라 실험 의도, 결과, 원인, 보완점을 한 섹션에서 연결하는 부분입니다.

반드시 답할 질문:

- 이번 실험은 무엇을 확인하려고 했나요?
- 저장된 결과에서는 어떤 일이 일어났나요?
- 성공했다면 어떤 조건이 성과를 만들었나요?
- 실패했다면 어떤 조건이 성과를 막았나요?
- 보완점은 무엇이고, 왜 필요한가요?

성과가 좋을 때:

- 비용 차감 전 우위가 충분했는지 설명합니다.
- 승률, 평균 이익, 평균 손실, 손익비, 목표가 도달 비중, drawdown을 함께 봅니다.
- 비용을 흡수한 이유를 저장된 수치로 설명합니다.

성과가 나쁠 때:

- gross-vs-net gap, turnover, exit mix, 비용 부담, threshold, hold window, reward/risk 구조를 저장된 수치로 설명합니다.
- 비용만 탓하지 않습니다. 비용 차감 전 손익과 신호 품질도 같이 봅니다.
- 저장 근거 없는 ATR, liquidation, delayed-exit, microstructure, behavior 설명을 만들지 않습니다.
- 테스트한 전략/버전의 실패와 전략군 전체의 실패를 구분합니다.
- 저장 근거가 특정 구현, 기간, 심볼, 타임프레임, 비용 가정, 파라미터 그리드에 묶여 있으면 전략군 전체를 기각하지 않습니다.
- 필요한 경우 아래 의미의 문장을 포함합니다.

```html
<p>
  현재 버전은 이 조건에서 비용 반영 후 유효한 전략으로 보기 어렵습니다.
  다만 이 결과만으로 전략군 전체를 기각하기는 이릅니다.
</p>
```

- 위 문장 뒤에는 왜 기각하기 이른지 구체적으로 설명합니다. 예: 하나의 V1 구현만 테스트했는지, 검증 구간과 심볼이 제한적인지, regime/유동성/상위 타임프레임/방향 지속 확인 필터가 없었는지, OOS/WFO와 기준선 비교가 부족한지.

성과가 좋을 때도 과장하지 않습니다.

- 현재 버전과 조건에서 무엇이 잘 작동했는지 설명합니다.
- 넓은 검증 없이 전략군 전체가 보편적으로 유효하다고 쓰지 않습니다.
- 전략군 전체로 판단 범위를 넓히려면 OOS/WFO, 기준선 비교, regime segmentation이 필요하다고 씁니다.

마무리 문장:

```html
<p>보완점은 다음과 같습니다.</p>
<ul>
  <li>[보완점 1]입니다. [이유]</li>
  <li>[보완점 2]입니다. [이유]</li>
  <li>[보완점 3]입니다. [이유]</li>
</ul>
```

규칙:

- `첫째`, `둘째`, `셋째`로 나열하지 않습니다.
- 보완점은 `-` bullet에 해당하는 `<ul><li>`로 씁니다.
- `다음 실험에서는`보다 `보완점은 다음과 같습니다` 같은 직접적인 표현을 우선합니다.
- 별도 결론 섹션을 만들지 않습니다.

## 10. 최종 검수

HTML 저장 전 아래를 확인합니다.

- 파일명이 `report-ko.html`인가?
- 헤더와 본문이 `docs/blog/report_template.html` 구조를 따르는가?
- 첫 문단이 전략 설명으로 시작하는가?
- 첫 문단이 시장/심볼/기간 나열로 시작하지 않는가?
- main title에 실험 세부 문구가 과하게 들어가지 않았는가?
- subtitle이 전략 자체를 설명하고, 실험 행동 설명으로 흐르지 않았는가?
- version 변경이 있으면 핵심 요약에 이전/현재 메커니즘 차이를 짧게 설명했는가?
- 비교 라벨에 어색한 `기본값`이 붙지 않았는가?
- 영어식 micro-heading을 쓰지 않았는가?
- 공개 리포트에 자명한 backtest 고지 문구를 넣지 않았는가?
- 결과 원인이 저장된 수치와 대표 거래 근거로 설명되는가?
- 이론적 배경이 전략의 경제적 가정, 성공 조건, 실패 조건, 비용/손익비, 레퍼런스를 함께 다루는가?
- `전략 규칙`이 별도 기본 섹션이 아니라 이론/배경 섹션 안에 들어갔는가?
- 표가 너무 크거나 목적이 모호하면 나누거나 줄였는가?
- standalone `가설`/hypothesis 섹션을 만들지 않았는가?
- 최종 섹션 제목이 `해석`인가?
- 별도 결론 섹션을 만들지 않았는가?
- 실패한 버전의 결과를 전략군 전체 기각으로 확대하지 않았는가?
- 성공한 버전의 결과를 보편적 유효성으로 과장하지 않았는가?
- `현재 버전`, `이 조건`, `전략군 전체를 기각하기는 이릅니다`처럼 증거 범위를 분리하는 문장이 필요한 경우 포함됐는가?
- 이미지가 `<figure class="report-figure">`로 들어갔는가?
- 표가 `<div class="table-scroll">`로 감싸졌는가?
- HTML이 hELLO 스킨용 `.report-page` 컨테이너와 `1120px` 기본 폭을 따르는가?
- 표가 왼쪽 정렬 중심으로 읽히는가?
- 이미지가 본문 폭에 맞춰 크게 보이는가?
- 내부 추적값, task 번호, run id, 내부 candidate id가 노출되지 않았는가?
