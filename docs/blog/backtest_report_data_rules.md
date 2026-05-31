# Backtest Report Data Rules

이 문서는 백테스트 실행 결과를 블로그/문서 작성 에이전트에게 넘기기 위한 최소 데이터 규칙입니다.

목표는 백테스트 시스템 내부 기록을 그대로 노출하는 것이 아니라, `docs/blog/template.md`를 채우는 데 필요한 값만 작게 저장하는 것입니다.

## 1. 저장 단위

백테스트 1회 또는 비교 대상 1개 전략을 기준으로 하나의 payload를 저장합니다.

권장 이름:

```text
backtest_report_payload
```

권장 형식:

- JSON
- YAML
- DB JSON metadata

어떤 형식을 쓰더라도 필드 이름과 의미는 아래 규칙을 따릅니다.

## 2. 필드 이름 규칙

- `snake_case`를 사용합니다.
- 값이 없으면 빈 문자열보다 `null`을 사용합니다.
- 비율 값은 사람이 읽는 표시값과 계산값을 함께 저장할 수 있습니다.
- 금액 값은 통화 단위를 함께 저장합니다.
- 시간은 UTC ISO 문자열을 권장합니다.

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
    "market_summary": "[시장/심볼/타임프레임]",
    "period": "[기간]",
    "pr": "[PR 번호 또는 링크]"
  },
  "images": {
    "equity_curve": "[equity-curve.png]",
    "drawdown": "[drawdown.png 또는 null]"
  },
  "setup": {
    "exchange": "[거래소]",
    "symbol": "[심볼]",
    "market": "[Spot 등]",
    "timeframe": "[타임프레임]",
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
    "spread_total": "[총 스프레드 또는 null]"
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
      "time": "[시간]",
      "side": "[Long/Short]",
      "entry": "[진입가]",
      "exit": "[청산가]",
      "result": "[결과]",
      "reason": "[거래 이유]"
    },
    "worst_trade": {
      "time": "[시간]",
      "side": "[Long/Short]",
      "entry": "[진입가]",
      "exit": "[청산가]",
      "result": "[결과]",
      "reason": "[거래 이유]"
    },
    "typical_winner": {
      "summary": "[일반적인 수익 거래 요약]"
    },
    "typical_loser": {
      "summary": "[일반적인 손실 거래 요약]"
    }
  },
  "interpretation": {
    "result_interpretation": "[성과 해석]",
    "risk_interpretation": "[위험 및 한계 해석]",
    "final_conclusion": "[결론]"
  }
}
```

## 4. 선택 필드

필요할 때만 추가합니다.

```json
{
  "optional": {
    "drawdown_image": "[drawdown.png]",
    "side_metrics": {
      "long_return": "[Long 수익률]",
      "short_return": "[Short 수익률]"
    },
    "session_metrics": "[세션별 성과 요약]",
    "volatility_regime_metrics": "[변동성 구간별 성과 요약]",
    "no_cost_diagnostic": "[비용 제거 시 결과]",
    "top_three_removed_result": "[상위 3개 거래 제거 시 결과]"
  }
}
```

선택 필드는 보고서 품질을 높일 때만 씁니다. 매일 기록에는 필수 필드만 있어도 충분해야 합니다.

## 5. 이미지 참조 규칙

- 이미지 파일명만 payload에 넣습니다.
- 블로그 템플릿에서는 `./images/[filename].png` 형태로 사용합니다.
- 이미지가 없으면 `null`을 넣고, 작성 에이전트는 `[확인 필요]`로 남깁니다.
- 이미지 목록을 길게 저장하지 않습니다.

예시:

```json
{
  "images": {
    "equity_curve": "fvg-midpoint-equity-curve.png",
    "drawdown": null
  }
}
```

## 6. PR 저장 규칙

- `pr` 필드는 문자열 하나만 둡니다.
- 예시는 `#123`, `PR #123`, 또는 PR URL입니다.
- commit hash는 블로그 작성 payload에 넣지 않습니다.

예시:

```json
{
  "title": {
    "pr": "PR #123"
  }
}
```

## 7. 대표 거래 선택 규칙

대표 거래는 네 가지를 고릅니다.

- `best_trade`: 순손익 또는 R 기준 최고 수익 거래.
- `worst_trade`: 순손익 또는 R 기준 최대 손실 거래.
- `typical_winner`: 평균 수익 거래와 가장 가까운 수익 거래.
- `typical_loser`: 평균 손실 거래와 가장 가까운 손실 거래.

동률이면 다음 순서로 고릅니다.

1. 비용이 더 크게 반영된 거래.
2. 보유 시간이 더 일반적인 거래.
3. 시간상 먼저 발생한 거래.

대표 거래에는 가격만 넣지 말고, 왜 대표적인지 한 문장 요약을 같이 저장합니다.

## 8. 비용과 기대값 저장 규칙

비용은 가능하면 총액과 해석 문장을 함께 저장합니다.

필수:

- `fee_total`
- `slippage_total`
- `spread_total`
- `cost_assumptions`
- `expectancy`

권장:

- 비용 제거 결과.
- 2배 비용 stress 결과.
- 3배 비용 stress 결과.
- 비용 반영 전후 Expectancy 변화.

예시:

```json
{
  "metrics": {
    "expectancy": "+0.11R",
    "fee_total": "87,713.79 USDT",
    "slippage_total": "50,985.41 USDT",
    "spread_total": "26,314.14 USDT"
  },
  "illusion_checks": {
    "cost_sensitivity": "비용 반영 후 Expectancy가 +0.24R에서 +0.11R로 낮아졌습니다."
  }
}
```

## 9. 블로그 작성 payload에 넣지 않는 항목

다음 값은 내부 DB, 내부 로그, 실행 기록에만 남기고 블로그 작성 payload에는 넣지 않습니다.

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

내부 시스템이 run ID나 config를 필요로 할 수는 있습니다. 그런 값은 내부 추적용으로만 사용하고, 블로그 작성 에이전트에게 넘기는 payload와 최종 보고서에는 넣지 않습니다.

## 10. 누락값 처리

- 필수 값이 없으면 해당 필드는 `null`로 저장합니다.
- 작성 에이전트는 누락값을 임의로 채우지 않습니다.
- 최종 문서에는 `[확인 필요]`로 남깁니다.
- 계산 가능한 값이라도 payload에 없으면 새로 계산하지 않습니다.

예시:

```json
{
  "metrics": {
    "sharpe": null
  }
}
```

보고서 작성 시:

```markdown
* Sharpe: `[확인 필요]`
```

## 11. 문서 전용 규칙

이 규칙은 문서 작성 payload 규칙입니다. DB schema, 백테스트 엔진, 저장소 구조 변경을 요구하지 않습니다.

향후 자동 저장을 구현하려면 별도 task에서 다룹니다.
