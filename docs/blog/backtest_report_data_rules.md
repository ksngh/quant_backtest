# Backtest Report Data Rules

이 문서는 백테스트 결과를 daily report 본문 작성 또는 이미지 생성 에이전트에게 넘기기 위한 저장 규칙입니다.

목표는 백테스트 내부 기록을 그대로 노출하는 것이 아니라, `docs/blog/DAILY_REPORT_TEMPLATE.md`와 `docs/blog/DAILY_REPORT_STYLE.md`를 기준으로 한국어 리포트 본문과 리포트 이미지를 만들 수 있는 값만 작게 저장하는 것입니다.

## 1. 저장 단위

백테스트 1회 또는 비교 대상 전략 1개를 기준으로 하나의 report artifact folder를 만듭니다.

기본 폴더 구조:

```text
reports/blog_payloads/[strategy-slug]/[strategy-version-slug]/[period-slug]/
  payload.json
  report-ko.md
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

full report workflow에서는 `report-ko.md` 한국어 리포트 본문까지 생성합니다.

이 workflow에서는 `report-en.md`, `image_plan.md`, `image_plan.json`, `images/` 하위 폴더를 기본 생성하지 않습니다.

폴더 이름 규칙:

- `strategy-slug`: 실제 리포트용 전략명을 소문자 ASCII로 바꾸고 공백/특수문자는 `-`로 정리합니다.
- `strategy-version-slug`: 전략 버전을 소문자 ASCII로 정리합니다. 예: `v1`, `v2`.
- `period-slug`: 백테스트 기간이 있으면 `YYYYMMDD-YYYYMMDD`를 사용합니다.
- 기간을 알 수 없으면 리포트 작성일 `YYYYMMDD`를 사용합니다.
- 같은 전략/기간의 리포트를 다시 만들 때는 기존 `payload.json`, `report-ko.md`, PNG를 삭제한 뒤 같은 목적의 재생성인지 확인합니다.
- folder, payload, image filename에는 task 번호, run id, 내부 candidate id를 넣지 않습니다.

이미지 저장 규칙:

- 모든 생성 이미지는 `payload.json`과 같은 디렉터리에 저장합니다.
- payload 이미지 참조에는 파일명만 넣습니다.
- Markdown에서 이미지를 참조해야 할 때는 같은 폴더 기준 `./[filename].png`를 사용합니다.
- 이미지 참조에는 절대경로, `../`, 하위 `images/`, 외부 URL을 넣지 않습니다.

리포트 본문 저장 규칙:

- `report-ko.md`는 `payload.json`과 같은 디렉터리에 저장합니다.
- `report-ko.md` 작성 전 `docs/blog/DAILY_REPORT_TEMPLATE.md`와 `docs/blog/DAILY_REPORT_STYLE.md`를 읽습니다.
- `docs/blog/DAILY_REPORT_TEMPLATE.md`는 섹션 구조를 정하고, `docs/blog/DAILY_REPORT_STYLE.md`는 말투와 해석 방식을 정합니다.
- `report-ko.md`는 `payload.json`과 같은 디렉터리에 있는 PNG 파일만 참조합니다.
- Markdown 이미지 참조는 `./summary_equity_curve.png`처럼 같은 폴더 기준 상대 경로만 사용합니다.
- payload에 없는 값은 추정하지 않고 `[확인 필요]`로 남깁니다.
- 본문에는 task 번호, run id, 내부 candidate id, DB dump, 원본 CSV dump, source file path, git commit, credential, config dump를 쓰지 않습니다.
- research-only 또는 실패한 전략을 실전 적용 가능한 전략처럼 쓰지 않습니다.

## 2. 필드 이름 규칙

- `snake_case`를 사용합니다.
- 값이 없으면 빈 문자열보다 `null`을 사용합니다.
- 비율 값은 사람이 읽는 표시값과 계산값을 함께 저장할 수 있습니다.
- 금액 값은 통화 단위를 함께 저장합니다.
- 시간은 UTC ISO 문자열을 권장합니다.
- 최종 리포트에 노출하지 않을 내부 추적값은 payload에 넣지 않는 것을 원칙으로 합니다.

예시:

```json
{
  "strategy_name": "FVG midpoint",
  "symbol": "BTCUSDT",
  "timeframe": "1m",
  "period_start": "2026-05-20T00:00:00Z",
  "period_end": "2026-05-21T00:00:00Z"
}
```

## 3. 필수 payload 구조

```json
{
  "title": {
    "strategy_name": "[전략명]",
    "strategy_version": "[전략 버전]",
    "strategy_label": "[전략명 전략버전]",
    "market_summary": "[시장/심볼/타임프레임/기간]",
    "period": "[기간]",
    "pr": "[PR 번호 또는 링크]"
  },
  "artifact": {
    "schema": "colocated_payload_images_v1",
    "strategy_slug": "[strategy-slug]",
    "strategy_version_slug": "[strategy-version-slug]",
    "period_slug": "[period-slug]",
    "image_reference_rule": "filenames_only_colocated_with_payload"
  },
  "images": {
    "primary": "summary_equity_curve.png",
    "items": [
      {
        "id": "summary_equity_curve",
        "filename": "summary_equity_curve.png",
        "caption": "Equity curve와 drawdown을 함께 표시한 대표 성과 그래프입니다.",
        "section": "summary,results"
      },
      {
        "id": "cost_impact",
        "filename": "cost_impact.png",
        "caption": "거래비용 반영 전후의 성과 차이를 보여주는 그래프입니다.",
        "section": "cost_impact"
      },
      {
        "id": "representative_win_trade",
        "filename": "representative_win_trade.png",
        "caption": "대표 수익 거래 차트입니다.",
        "section": "representative_trades"
      },
      {
        "id": "representative_loss_trade",
        "filename": "representative_loss_trade.png",
        "caption": "대표 손실 거래 차트입니다.",
        "section": "representative_trades"
      }
    ]
  },
  "setup": {
    "exchange": "[거래소]",
    "symbol": "[심볼]",
    "market": "[Spot 등]",
    "timeframe": "[타임프레임]",
    "period": "[기간]",
    "comparison_variables": "[비교 변인 또는 null]",
    "initial_capital": "[초기 자본]",
    "position_sizing": "[사이징 방식]",
    "entry_conditions_summary": "[진입 조건 요약]",
    "exit_conditions_summary": "[청산 조건 요약]",
    "cost_assumptions": "[수수료/스프레드/슬리피지 가정]",
    "execution_assumption": "[OHLCV 체결 가정]"
  },
  "hypothesis_and_theory": {
    "hypotheses": [
      "[...할 것이다.]",
      "[...할 것이다.]"
    ],
    "assumptions": [
      "[가정 1]",
      "[가정 2]",
      "[가정 3]"
    ],
    "economic_meaning": "[경제적 의미]",
    "expectancy": {
      "formula": "E[R] = P(win) × AvgWin - P(loss) × AvgLoss - Cost",
      "p_win": "[승률 또는 확률]",
      "avg_win": "[평균 이익]",
      "p_loss": "[손실 확률]",
      "avg_loss": "[평균 손실]",
      "cost": "[거래 비용]"
    }
  },
  "metrics": {
    "total_trades": "[총 거래 수]",
    "win_rate": "[승률]",
    "total_return": "[총 수익률]",
    "final_equity": "[최종 자본]",
    "max_drawdown": "[최대 낙폭]",
    "profit_factor": "[Profit Factor]",
    "expectancy": "[Expectancy]",
    "sharpe": "[Sharpe]",
    "sortino": "[Sortino]",
    "average_win": "[평균 이익]",
    "average_loss": "[평균 손실]",
    "fee_total": "[총 수수료]",
    "slippage_total": "[총 슬리피지]",
    "spread_total": "[총 스프레드 또는 null]",
    "gross_pnl": "[비용 차감 전 손익]",
    "net_pnl": "[비용 차감 후 손익]"
  },
  "cost_impact": {
    "gross_pnl": "[비용 미반영 손익]",
    "fee": "[총 수수료]",
    "spread": "[총 스프레드]",
    "slippage": "[총 슬리피지]",
    "total_transaction_cost": "[총 거래비용]",
    "net_pnl": "[비용 반영 후 손익]",
    "final_return_after_costs": "[비용 반영 후 최종 수익률]",
    "interpretation": "[비용 영향 해석]"
  },
  "illusion_checks": {
    "cost_sensitivity": "[비용 민감도]",
    "outlier_dependence": "[상위 거래 의존도]",
    "window_dependence": "[구간 의존도]",
    "trade_count_quality": "[거래 수 해석]",
    "side_concentration": "[Long/Short 편중]",
    "same_candle_ambiguity": "[동일 캔들 처리 영향]"
  },
  "representative_trades": {
    "best_trade": {
      "entry_time": "[진입 시간]",
      "exit_time": "[청산 시간]",
      "side": "[Long/Short]",
      "entry_price": "[진입가]",
      "exit_price": "[청산가]",
      "stop_price": "[손절가 또는 null]",
      "target_price": "[익절가 또는 null]",
      "net_pnl": "[순손익]",
      "gross_pnl": "[비용 차감 전 손익 또는 null]",
      "transaction_cost": "[수수료/스프레드/슬리피지 합계 또는 null]",
      "hold_duration": "[보유 시간 또는 null]",
      "entry_candle_context": "[진입 전후 candle body/range/volatility 설명 또는 null]",
      "volume_context": "[local baseline 대비 거래량 설명 또는 null]",
      "follow_through_context": "[진입 후 추세 지속/반전/횡보 여부 또는 null]",
      "equity_context": "[근처 drawdown/equity curve 상태 또는 null]",
      "exit_reason": "[청산 이유]",
      "reason": "[대표 거래로 고른 이유]"
    },
    "worst_trade": {
      "entry_time": "[진입 시간]",
      "exit_time": "[청산 시간]",
      "side": "[Long/Short]",
      "entry_price": "[진입가]",
      "exit_price": "[청산가]",
      "stop_price": "[손절가 또는 null]",
      "target_price": "[익절가 또는 null]",
      "net_pnl": "[순손익]",
      "gross_pnl": "[비용 차감 전 손익 또는 null]",
      "transaction_cost": "[수수료/스프레드/슬리피지 합계 또는 null]",
      "hold_duration": "[보유 시간 또는 null]",
      "entry_candle_context": "[진입 전후 candle body/range/volatility 설명 또는 null]",
      "volume_context": "[local baseline 대비 거래량 설명 또는 null]",
      "follow_through_context": "[진입 후 추세 지속/반전/횡보 여부 또는 null]",
      "equity_context": "[근처 drawdown/equity curve 상태 또는 null]",
      "exit_reason": "[청산 이유]",
      "reason": "[대표 거래로 고른 이유]"
    }
  },
  "interpretation": {
    "experiment_intent": "[이번 실험이 확인하려는 것]",
    "result_interpretation": "[저장 결과에서 일어난 일]",
    "cause_interpretation": "[결과가 나온 원인 해석]",
    "risk_interpretation": "[위험 및 한계 해석]",
    "next_improvements": "[다음 실험에서 추가/제거/조정할 항목]"
  }
}
```

## 4. 리포트 해석 및 누락 항목 저장 규칙

`interpretation`은 별도 결론 문구를 저장하는 곳이 아닙니다. 아래 순서로 future report writer가 한 섹션 안에서 해석을 쓸 수 있도록 저장합니다.

- `experiment_intent`: 이번 실험이 확인하려는 것.
- `result_interpretation`: 저장 결과에서 실제로 일어난 일.
- `cause_interpretation`: 비용, gross edge, 신호 품질, turnover, threshold, hold window, 필터 부재 등 원인 후보.
- `risk_interpretation`: 연구 전용 경계, 비용/체결/구간 한계.
- `next_improvements`: 다음 실험에서 추가하거나 제거할 조건.

패턴, 필터, 이미지, 타임프레임 coverage가 없다는 사실은 기본 payload 설명문에 넣지 않습니다. 의사결정에 중요하면 `risk_interpretation` 또는 `next_improvements`에만 넣습니다. 예를 들어 `5m` local closed candle coverage가 없어 빠진 비교는 리드 문장이 아니라 `next_improvements`에 저장합니다.

대표 거래에는 데이터가 있을 때만 시장 상황 맥락을 저장합니다. 거래량, candle body/range, volatility, 보유 시간, 비용 비중, 진입 후 추세 지속/반전/횡보, 근처 drawdown/equity 상태가 없으면 null로 두고 리포트에서 만들지 않습니다.

## 5. 필수 고정 이미지

모든 payload/image artifact는 아래 네 이미지를 생성합니다.

```text
summary_equity_curve.png
cost_impact.png
representative_win_trade.png
representative_loss_trade.png
```

### summary_equity_curve.png

- 대표 성과 그래프입니다.
- equity curve와 drawdown을 같은 이미지 안에 함께 표시합니다.
- 2단 패널을 사용합니다.
- 상단: equity curve.
- 하단: drawdown 또는 underwater curve.
- 별도의 `drawdown_curve.png`는 기본으로 만들지 않습니다.
- 주석에는 strategy name, market/symbol, timeframe, period, total return, max drawdown, total trades, win rate, expectancy를 가능한 범위에서 넣습니다.

### cost_impact.png

- 거래비용 반영 전후를 비교하는 그래프입니다.
- 비용 단계별 equity curve가 있으면 line chart를 사용합니다.
- 비용 단계별 equity curve가 없고 aggregate 값만 있으면 bar chart를 사용합니다.
- line chart가 가능할 때는 no cost equity, fee only equity, fee + spread equity, fee + spread + slippage equity를 비교합니다.
- bar chart만 가능할 때는 gross PnL, fee, spread, slippage, net PnL을 비교합니다.
- 주석에는 total fee, total spread, total slippage, total transaction cost, gross PnL, net PnL, final return after costs를 가능한 범위에서 넣습니다.
- chart title이나 label에는 `cost stress`라는 표현을 쓰지 않습니다.

### representative_win_trade.png

- 대표 수익 거래 차트입니다.
- OHLC candle data가 있으면 candlestick chart로 만듭니다.
- 거래 전후 window의 candles, entry marker, exit marker, stop line, target line, pattern zone 또는 signal zone을 가능한 범위에서 표시합니다.
- side, entry price, exit price, entry time, exit time, net PnL, exit reason을 표시합니다.
- `representative_trades.best_trade`가 있으면 우선 사용합니다.
- 없으면 전략 논리를 설명하기 쉬운 수익 거래를 고릅니다.

### representative_loss_trade.png

- 대표 손실 거래 차트입니다.
- OHLC candle data가 있으면 candlestick chart로 만듭니다.
- 거래 전후 window의 candles, entry marker, exit marker, stop line, target line, 실패한 pattern zone 또는 signal zone을 가능한 범위에서 표시합니다.
- side, entry price, exit price, entry time, exit time, net PnL, exit reason을 표시합니다.
- `representative_trades.worst_trade`가 있으면 우선 사용합니다.
- 없으면 전략의 약점을 설명하기 쉬운 손실 거래를 고릅니다.

## 6. 선택 이미지

아래 이미지는 저장 데이터가 있고 리포트 해석에 도움이 될 때만 생성합니다.

- `price_with_trades.png`
- `trade_pnl_distribution.png`
- `side_attribution.png`
- `exit_reason_attribution.png`
- `10_equity_curve_[number]_[timeframe]_[period-slug]_[variant-slug].png`
- `20_cost_impact_[number]_[timeframe]_[period-slug]_[variant-slug].png`
- `30_win_trade_[number]_[timeframe]_[period-slug]_[variant-slug].png`
- `40_loss_trade_[number]_[timeframe]_[period-slug]_[variant-slug].png`

선택 이미지도 `payload.json`과 같은 디렉터리에 저장하고 payload에는 파일명만 넣습니다.

## 7. 최종 검증 규칙

full report artifact 생성 후 아래를 확인합니다.

- `payload.json` exists.
- `report-ko.md` exists.
- `summary_equity_curve.png` exists.
- `cost_impact.png` exists.
- `representative_win_trade.png` exists.
- `representative_loss_trade.png` exists.
- `images/` 하위 폴더가 없습니다.
- `report-en.md`, `image_plan.md`, `image_plan.json` 파일이 없습니다.
- 모든 equity curve 이미지는 drawdown을 같은 이미지 안에 포함합니다.
- 별도의 `drawdown_curve.png`는 명시 요청이 없으면 생성하지 않습니다.
- payload의 모든 이미지 참조는 `/`가 없는 파일명입니다.
- `report-ko.md`의 모든 이미지 참조는 같은 폴더 기준 `./[filename].png`입니다.
- `report-ko.md`에는 task 번호, run id, 내부 candidate id가 없습니다.
- 누락된 필수 값은 `[확인 필요]`로 남아 있습니다.

## 8. PR 저장 규칙

- `pr` 필드는 문자열 하나만 둡니다.
- 예시는 `#123`, `PR #123`, 또는 PR URL입니다.
- commit hash는 daily report payload에 넣지 않습니다.

예시:

```json
{
  "title": {
    "pr": "PR #123"
  }
}
```

## 9. 비용과 기대값 저장 규칙

비용은 가능한 범위에서 분리해 저장합니다.

- entry fee.
- exit fee.
- spread.
- slippage.
- total transaction cost.
- gross PnL.
- net PnL.
- fee-adjusted break-even.
- slippage-adjusted break-even.

기대값은 아래 수식의 항목을 채울 수 있어야 합니다.

```text
E[R] = P(win) × AvgWin - P(loss) × AvgLoss - Cost
```

수익률만 저장하지 말고, 승률, 평균 이익, 평균 손실, 손익비, 수수료, 슬리피지를 함께 저장합니다.

## 10. 금지 사항

- daily report 이미지에 task 번호, run id, 내부 candidate id를 노출하지 않습니다.
- 저장된 graph/equity/trade/cost 데이터가 없는데 임의 곡선을 만들지 않습니다.
- smoothing으로 성과 곡선을 보기 좋게 바꾸지 않습니다.
- live trading, 실제 주문, private API, credential 사용을 하지 않습니다.
- payload에는 `.env`, API key, DB dump, 원본 CSV dump를 넣지 않습니다.
