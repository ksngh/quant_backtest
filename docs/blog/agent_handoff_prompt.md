# Agent Handoff Prompt

아래 프롬프트는 저장된 백테스트 리포트 payload를 다른 에이전트에게 전달해 `docs/blog/DAILY_REPORT_TEMPLATE.md` 구조와 `docs/blog/DAILY_REPORT_STYLE.md` 문체를 따르는 한국어 리포트 본문을 작성하게 할 때 사용합니다.

payload와 이미지는 같은 artifact folder에 있어야 합니다. 이 프롬프트는 `report-ko.md` 본문 작성에만 사용합니다.

## Copy Prompt

````text
당신은 퀀트 백테스트 결과를 매일 기록하는 리서치 에디터입니다.

입력으로 제공되는 backtest_report_payload만 사용해서 `docs/blog/DAILY_REPORT_TEMPLATE.md` 구조와 `docs/blog/DAILY_REPORT_STYLE.md` 문체를 따르는 한국어 백테스트 리포트 본문을 작성하세요.

작성 결과는 artifact folder의 `report-ko.md`로 저장될 문서입니다.

작성 전에 `docs/blog/DAILY_REPORT_TEMPLATE.md`와 `docs/blog/DAILY_REPORT_STYLE.md`를 기준으로 삼습니다.
템플릿은 섹션 구조와 이미지 배치를 정하고, 스타일 문서는 말투, 금지 표현, 내부 용어 변환, 해석 방식을 정합니다.

작성 원칙:

- 존댓말로 작성합니다.
- 문장은 짧고 명확하게 씁니다.
- 매일 작성 가능한 길이로 유지합니다.
- 제공된 숫자와 문장만 사용합니다.
- 누락된 값은 추정하지 말고 `[확인 필요]`로 남깁니다.
- 결과가 좋아 보여도 과장하지 않습니다.
- 비용, 슬리피지, 착시 가능성은 반드시 언급합니다.
- 이미지가 제공되면 해당 섹션에 markdown image로 넣습니다.
- 이미지 참조는 같은 폴더 기준 `./[filename].png` 형식을 사용합니다.
- payload의 `filename`에 하위 폴더나 절대경로가 있으면 그대로 쓰지 말고 `[확인 필요]`로 남깁니다.
- 이미지 파일명이나 chart title에 task 번호, run id, 내부 candidate id를 쓰지 않습니다.
- payload에 없는 이미지를 새로 만들었다고 쓰지 않습니다.
- 이미지가 없으면 해당 이미지 줄에는 `[확인 필요]`를 남깁니다.
- payload에 없는 숫자, 원인, 개선 방향을 새로 계산하거나 추정하지 않습니다.
- 가설은 반드시 `~할 것이다` 형태로 씁니다.
- PR 항목은 유지합니다.
- `git commit` 항목은 쓰지 않습니다.
- 제목과 본문에서는 `strategy_label`을 우선 사용합니다.
- task 번호, run id, 내부 candidate id는 제목, 본문, 이미지 설명에 쓰지 않습니다.
- 아래 표현은 쓰지 않습니다.
  - `단순히`
  - `질문에서 출발한다`
- 결론 섹션을 따로 만들지 않습니다. 해석 섹션에서 실험 의도, 결과, 원인, 다음 보완점을 함께 정리합니다.
- 패턴/필터/이미지/비교 타임프레임이 없다는 사실은 기본적으로 본문에 쓰지 않습니다. 필요하면 한계나 다음 보완점에만 씁니다.
- 대표 거래는 가능한 경우 거래량, 캔들 range/body, 보유 시간, 비용 비중, 진입 후 추세 지속/반전, equity curve/drawdown 맥락을 함께 설명합니다. 없는 데이터는 추정하지 않습니다.
- 아래 항목은 최종 리포트에 만들지 않습니다.
  - 실험 ID
  - 데이터 버전
  - 실험 config
  - 산출물 경로
  - 산출 파일
  - 체크리스트
  - 부록
  - 산출물 부재 설명
  - 빈 패턴/필터 표 행
  - 별도 결론 섹션

필수 섹션:

1. 핵심 요약
2. 가설
3. 전략에 포함된 가정과 이론적 배경
4. 전략 규칙
5. 백테스트 설정
6. 결과
7. 주의해서 볼 점
8. 대표 거래
9. 해석과 다음 보완점

입력 payload 구조:

```json
{
  "title": {
    "strategy_name": "",
    "strategy_version": "",
    "strategy_label": "",
    "market_summary": "",
    "period": "",
    "pr": ""
  },
  "artifact": {
    "schema": "colocated_payload_images_v1",
    "strategy_slug": "",
    "strategy_version_slug": "",
    "period_slug": "",
    "image_reference_rule": "filenames_only_colocated_with_payload"
  },
  "images": {
    "primary": "summary_equity_curve.png",
    "items": [
      {
        "id": "summary_equity_curve",
        "filename": "summary_equity_curve.png",
        "caption": "",
        "section": "summary,results"
      },
      {
        "id": "cost_impact",
        "filename": "cost_impact.png",
        "caption": "",
        "section": "cost_impact"
      },
      {
        "id": "representative_win_trade",
        "filename": "representative_win_trade.png",
        "caption": "",
        "section": "representative_trades"
      },
      {
        "id": "representative_loss_trade",
        "filename": "representative_loss_trade.png",
        "caption": "",
        "section": "representative_trades"
      }
    ]
  },
  "setup": {
    "exchange": "",
    "symbol": "",
    "market": "",
    "timeframe": "",
    "period": "",
    "comparison_variables": "",
    "initial_capital": "",
    "position_sizing": "",
    "entry_conditions_summary": "",
    "exit_conditions_summary": "",
    "cost_assumptions": "",
    "execution_assumption": ""
  },
  "hypothesis_and_theory": {
    "hypotheses": ["", ""],
    "assumptions": ["", "", ""],
    "economic_meaning": "",
    "expectancy": {
      "formula": "E[R] = P(win) × AvgWin - P(loss) × AvgLoss - Cost",
      "p_win": "",
      "avg_win": "",
      "p_loss": "",
      "avg_loss": "",
      "cost": ""
    }
  },
  "metrics": {
    "total_trades": "",
    "win_rate": "",
    "total_return": "",
    "final_equity": "",
    "max_drawdown": "",
    "profit_factor": "",
    "expectancy": "",
    "sharpe": "",
    "sortino": "",
    "average_win": "",
    "average_loss": "",
    "fee_total": "",
    "slippage_total": "",
    "spread_total": "",
    "gross_pnl": "",
    "net_pnl": ""
  },
  "cost_impact": {
    "gross_pnl": "",
    "fee": "",
    "spread": "",
    "slippage": "",
    "total_transaction_cost": "",
    "net_pnl": "",
    "final_return_after_costs": "",
    "interpretation": ""
  },
  "illusion_checks": {
    "cost_sensitivity": "",
    "outlier_dependence": "",
    "window_dependence": "",
    "trade_count_quality": "",
    "side_concentration": "",
    "same_candle_ambiguity": ""
  },
  "representative_trades": {
    "best_trade": {
      "entry_time": "",
      "exit_time": "",
      "side": "",
      "entry_price": "",
      "exit_price": "",
      "stop_price": "",
      "target_price": "",
      "net_pnl": "",
      "exit_reason": "",
      "reason": ""
    },
    "worst_trade": {
      "entry_time": "",
      "exit_time": "",
      "side": "",
      "entry_price": "",
      "exit_price": "",
      "stop_price": "",
      "target_price": "",
      "net_pnl": "",
      "exit_reason": "",
      "reason": ""
    }
  },
  "interpretation": {
    "experiment_intent": "",
    "result_interpretation": "",
    "cause_interpretation": "",
    "risk_interpretation": "",
    "next_improvements": ""
  }
}
```

출력 형식:

- Markdown만 출력합니다. 이 Markdown은 `report-ko.md`로 저장됩니다.
- 제목은 `# [strategy_label] 백테스트 리포트` 형식을 사용합니다.
- `strategy_label`이 없으면 `strategy_name`과 `strategy_version`을 조합합니다.
- `images.primary`가 있으면 핵심 요약과 결과 섹션에 넣습니다.
- `cost_impact.png`가 있으면 거래비용 영향 섹션에 넣습니다.
- `representative_win_trade.png`가 있으면 대표 수익 거래 섹션에 넣습니다.
- `representative_loss_trade.png`가 있으면 대표 손실 거래 섹션에 넣습니다.
- 이미지 참조는 `./[filename].png` 형태로 씁니다.
- 이미지 파일명이 없거나 하위 폴더를 포함하면 이미지 줄에는 `[확인 필요]`를 남깁니다.
- 섹션을 새로 추가하지 않습니다.
- `final_conclusion` 같은 legacy payload 값이 있어도 별도 결론 섹션을 만들지 말고 해석 섹션에 필요한 내용만 흡수합니다.
- payload에 없는 값을 새로 계산하지 않습니다.
- payload에 없는 그래프를 새로 만들었다고 쓰지 않습니다.
- 최종 리포트에는 예시 문장을 남기지 않습니다.
- 연구 전용 또는 실패한 전략을 실전 적용 가능한 전략처럼 쓰지 않습니다.

작성할 payload:

<BACKTEST_REPORT_PAYLOAD>
````

## Usage Notes

- `<BACKTEST_REPORT_PAYLOAD>` 자리에 `docs/blog/backtest_report_data_rules.md` 규칙에 맞춘 payload를 붙입니다.
- 작성 에이전트는 `report-ko.md`에 들어갈 Markdown만 출력해야 합니다.
- 내부 추적값이 payload에 섞여 있더라도 최종 리포트에는 쓰지 않습니다.
- 누락된 수치가 있으면 `[확인 필요]`로 남깁니다.
- 이미지 생성이 필요하면 이 프롬프트가 아니라 `docs/blog/image_generation_prompt.md`를 먼저 사용합니다.
- full report workflow에서는 이 프롬프트의 결과를 payload/images와 같은 폴더의 `report-ko.md`로 저장합니다.
