# Backtest Report Data Rules

이 문서는 백테스트 결과를 daily report HTML 작성 또는 이미지 생성 에이전트에게 넘기기 위한 저장 규칙입니다.

목표는 백테스트 내부 기록을 그대로 노출하는 것이 아니라, `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/DAILY_REPORT_STYLE.md`, `docs/blog/report_template.html`을 기준으로 Tistory용 한국어 HTML 리포트와 리포트 이미지를 만들 수 있는 값만 작게 저장하는 것입니다.

## 1. 저장 단위

백테스트 1회 또는 비교 대상 전략 1개를 기준으로 하나의 report artifact folder를 만듭니다.

기본 폴더 구조:

```text
reports/blog_payloads/[strategy-slug]/[strategy-version-slug]/[period-slug]/
  payload.json
  report-ko.html
  summary_equity_curve.png
  cost_impact.png
  representative_win_trade.png
  representative_loss_trade.png
```

full report workflow에서는 `report-ko.html` 한국어 HTML 리포트까지 생성합니다.

이 workflow에서는 `report-en.html`, `report-en.md`, `image_plan.md`, `image_plan.json`, `images/` 하위 폴더를 기본 생성하지 않습니다.

Markdown 파일은 기본 최종 산출물이 아닙니다. 명시적으로 요청된 경우에만 내부 scratch 또는 legacy export로 다룹니다.

폴더 이름 규칙:

- `strategy-slug`: 실제 리포트용 전략명을 소문자 ASCII로 바꾸고 공백/특수문자는 `-`로 정리합니다.
- `strategy-version-slug`: 전략 버전을 소문자 ASCII로 정리합니다. 예: `v1`, `v2`.
- `period-slug`: 백테스트 기간이 있으면 `YYYYMMDD-YYYYMMDD`를 사용합니다.
- 기간을 알 수 없으면 리포트 작성일 `YYYYMMDD`를 사용합니다.
- 같은 전략/기간의 리포트를 다시 만들 때는 기존 `payload.json`, `report-ko.html`, PNG를 삭제한 뒤 같은 목적의 재생성인지 확인합니다.
- folder, payload, image filename에는 task 번호, run id, 내부 candidate id를 넣지 않습니다.

이미지 저장 규칙:

- 모든 생성 이미지는 `payload.json`과 같은 디렉터리에 저장합니다.
- payload 이미지 참조에는 파일명만 넣습니다.
- HTML에서 이미지를 참조할 때는 같은 폴더 기준 `./[filename].png`를 사용합니다.
- 이미지 참조에는 절대경로, `../`, 하위 `images/`, 외부 URL을 넣지 않습니다.
- 이미지 생성 규칙은 `docs/blog/image_generation_prompt.md`의 stable visual contract를 따릅니다.
- 이미지 크기를 맞추기 위해 chart content를 crop하지 않습니다. target canvas를 직접 생성하거나, aspect ratio를 유지한 뒤 padding으로 맞춥니다.
- 대표 거래 이미지는 entry/exit 주변만 확대하지 않고 pre-entry와 post-exit candle context를 포함합니다.
- 라벨, legend, annotation이 겹치면 plot 위 글자를 줄이고 별도 annotation band나 외부 legend로 옮깁니다.

리포트 HTML 저장 규칙:

- `report-ko.html`은 `payload.json`과 같은 디렉터리에 저장합니다.
- `report-ko.html` 작성 전 `docs/blog/DAILY_REPORT_TEMPLATE.md`, `docs/blog/DAILY_REPORT_STYLE.md`, `docs/blog/report_template.html`을 읽습니다.
- `docs/blog/report_template.html`은 HTML 레이아웃과 읽기 흐름을 정합니다.
- Tistory hELLO 스킨 본문 폭을 기준으로 합니다. 기본 컨테이너 폭은 `1120px`이며, 모바일에서도 반응형으로 읽혀야 합니다.
- HTML은 내부 CSS를 포함한 단일 파일이어야 하며 외부 CSS 파일에 의존하지 않습니다.
- `docs/blog/DAILY_REPORT_TEMPLATE.md`는 섹션 구조를 정합니다.
- `docs/blog/DAILY_REPORT_STYLE.md`는 말투와 해석 방식을 정합니다.
- `report-ko.html`은 `payload.json`과 같은 디렉터리에 있는 PNG 파일만 참조합니다.
- 이미지 참조는 `<img src="./summary_equity_curve.png">`처럼 같은 폴더 기준 상대 경로만 사용합니다.
- 모든 이미지는 `<figure class="report-figure">`로 감쌉니다.
- 모든 표는 `<div class="table-scroll">`로 감쌉니다.
- main title은 전략명과 버전 중심으로 둡니다. 실험 세부 문구는 title이 아니라 요약/해석에 저장합니다.
- subtitle/lead에 쓸 stable strategy description은 strategy 문서에서 가져옵니다.
- payload에 없는 값은 추정하지 않고 `[확인 필요]`로 남깁니다.
- 본문에는 task 번호, run id, 내부 candidate id, DB dump, 원본 CSV dump, git commit, credential, config dump를 쓰지 않습니다.
- source file path는 기본적으로 쓰지 않습니다. 다만 `백테스트 설정`의 코드 블록을 정확 구현 인용으로 명시하는 별도 report task라면 짧은 source reference를 허용합니다.
- 실패한 전략을 실전 적용 가능한 전략처럼 쓰지 않습니다.

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
    "stable_strategy_description": "[전략 자체를 설명하는 짧은 문장]",
    "version_change_summary": "[이번 버전 또는 메커니즘 변경 요약 또는 null]",
    "title_policy": "strategy_name_and_version_only",
    "market_summary": "[시장/심볼/타임프레임/기간]",
    "period": "[기간]",
    "pr": "[PR 번호 또는 링크]"
  },
  "artifact": {
    "schema": "colocated_payload_images_html_report_v1",
    "strategy_slug": "[strategy-slug]",
    "strategy_version_slug": "[strategy-version-slug]",
    "period_slug": "[period-slug]",
    "report_filename": "report-ko.html",
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
    "execution_assumption": "[OHLCV 체결 가정]",
    "algorithm_explanation": {
      "plain_language_summary": "[전략 규칙이 어떻게 작동하는지 요약]",
      "entry_logic_pseudocode": "[설명용 의사코드 또는 null]",
      "exit_logic_pseudocode": "[설명용 의사코드 또는 null]",
      "indicator_calculations": [
        {
          "name": "[indicator name]",
          "pseudocode": "[설명용 의사코드]",
          "inputs": "[high/low/close 등 입력값]",
          "window": "[window/period]",
          "warmup_policy": "[warm-up 부족 시 처리]"
        }
      ],
      "no_lookahead_note": "[완료봉 기준과 미래 데이터 미사용 설명]",
      "fill_timing_note": "[진입/청산 체결 timing 설명]",
      "source_reference": "[정확 구현 인용일 때만 짧은 source reference 또는 null]"
    }
  },
  "hypothesis_and_theory": {
    "tested_assumptions": [
      "[이번 실험이 확인한 전제 1]",
      "[이번 실험이 확인한 전제 2]"
    ],
    "assumptions": [
      "[가정 1]",
      "[가정 2]",
      "[가정 3]"
    ],
    "economic_meaning": "[경제적 의미]",
    "edge_mechanism": "[전략이 우위를 가질 수 있는 이유]",
    "mechanism_detail": "[우위가 생길 수 있는 행동적/경제적/시장구조적 메커니즘]",
    "failure_mechanism": "[가정이 깨지는 원인 또는 불리한 regime]",
    "evidence_boundary": "[현재 백테스트가 실제로 검증한 범위와 검증하지 못한 범위]",
    "optional_formulas": [
      {
        "formula": "[짧은 수식]",
        "plain_language": "[수식의 의미]"
      }
    ],
    "momentum_mechanisms": {
      "underreaction": "[과소반응/정보 반영 지연 설명 또는 null]",
      "slow_position_adjustment": "[느린 포지션 조정 설명 또는 null]",
      "risk_premium_tail_risk": "[리스크 프리미엄/tail risk 설명 또는 null]",
      "hedger_speculator_structure": "[헤저/투기자 구조 설명 또는 null]",
      "bitcoin_spot_caveat": "[spot Bitcoin 적용 한계 또는 null]"
    },
    "success_conditions": "[작동하기 쉬운 시장 조건]",
    "failure_conditions": "[실패하기 쉬운 시장 조건]",
    "cost_and_rr_context": "[신호 속도, turnover, 비용, 손익비의 관계]",
    "rule_summary": "[진입/청산/비용/동일 캔들 등 결과 해석에 필요한 전략 규칙 요약]",
    "references": [
      {
        "id": "[짧은 식별자]",
        "title": "[문헌/자료 제목]",
        "reason": "[이 전략 설명에 필요한 이유]"
      }
    ],
    "expectancy": {
      "formula": "E[R] = P(win) x AvgWin - P(loss) x AvgLoss - Cost",
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
      "diagnostic_narrative_inputs": {
        "why_trade_happened": "[왜 이 거래가 발생했는지]",
        "entry_condition_check": "[진입 조건 정상 작동 근거 또는 null]",
        "exit_condition_check": "[청산 조건 정상 작동 근거 또는 null]",
        "pnl_source_interpretation": "[전략 논리 대 변동성/노이즈 해석 또는 null]",
        "performance_distortion_check": "[전체 성과 왜곡 여부 또는 null]",
        "recurrence_evidence": "[같은 유형 반복 여부 또는 null]",
        "engine_fill_sanity_check": "[백테스트 엔진/체결 로직 이상 신호 여부 또는 null]",
        "missing_evidence_note": "[판단 근거가 부족한 항목 또는 null]"
      },
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
      "diagnostic_narrative_inputs": {
        "why_trade_happened": "[왜 이 거래가 발생했는지]",
        "entry_condition_check": "[진입 조건 정상 작동 근거 또는 null]",
        "exit_condition_check": "[청산 조건 정상 작동 근거 또는 null]",
        "pnl_source_interpretation": "[전략 논리 대 변동성/노이즈 해석 또는 null]",
        "performance_distortion_check": "[전체 성과 왜곡 여부 또는 null]",
        "recurrence_evidence": "[같은 유형 반복 여부 또는 null]",
        "engine_fill_sanity_check": "[백테스트 엔진/체결 로직 이상 신호 여부 또는 null]",
        "missing_evidence_note": "[판단 근거가 부족한 항목 또는 null]"
      },
      "exit_reason": "[청산 이유]",
      "reason": "[대표 거래로 고른 이유]"
    }
  },
  "interpretation": {
    "experiment_intent": "[이번 실험이 확인하려는 것]",
    "result_interpretation": "[저장 결과에서 일어난 일]",
    "success_drivers": "[성과가 좋을 때 성공 원인]",
    "failure_drivers": "[성과가 좋지 않을 때 실패 원인]",
    "bounded_conclusion": "[현재 전략/버전/조건에서 말할 수 있는 결론]",
    "generalization_boundary": "[이 결과만으로 전략군 전체를 판단할 수 없는 이유]",
    "broader_claim_requirements": "[더 넓은 결론에 필요한 추가 검증]",
    "risk_interpretation": "[위험 및 한계 해석]",
    "next_improvements": "[보완점과 이유]"
  },
  "presentation_notes": {
    "table_purposes": [
      "[표 이름: 이 표가 답하는 질문]"
    ],
    "chart_purposes": [
      "[이미지 파일명: 이 이미지가 답하는 질문]"
    ],
    "required_interpretive_takeaways": [
      "[표/이미지/metric -> 해석에서 반드시 회수할 문장]"
    ],
    "logic_chain": {
      "strategy_idea": "[전략이 이용하려는 현상]",
      "version_or_experiment_change": "[이번 버전 또는 실험에서 바뀐 점]",
      "main_result": "[가장 중요한 결과]",
      "supporting_drivers": [
        "[결과를 만든 근거]"
      ],
      "limiting_evidence": [
        "[결과를 약하게 만들거나 일반화를 제한하는 근거]"
      ],
      "bounded_conclusion": "[현재 조건에서 말할 수 있는 결론]",
      "cannot_conclude": "[현재 결과만으로 말할 수 없는 결론]",
      "next_action_with_reason": "[다음 보완점과 그 이유]"
    },
    "wide_table_handling": "[split_tables_or_reduce_columns 또는 null]",
    "forbidden_copy_checks": [
      "그것은",
      "sentence-final 봅니다.",
      "라고 봅니다",
      "로 봅니다",
      "해 봅니다",
      "standalone 가설 section",
      "Hypothesis heading"
    ]
  }
}
```

## 4. 리포트 해석 및 누락 항목 저장 규칙

`interpretation`은 별도 결론 문구나 standalone 가설 섹션을 저장하는 곳이 아닙니다. 아래 순서로 future report writer가 `해석` 섹션 안에서 해석을 쓸 수 있도록 저장합니다.

- `experiment_intent`: 이번 실험이 확인하려는 것. 최종 리포트에서는 `가설` heading으로 분리하지 말고 `핵심 요약`, `백테스트 설정`, 또는 `해석`에 녹입니다.
- `result_interpretation`: 저장 결과에서 실제로 일어난 일.
- `success_drivers`: 결과가 좋을 때 성과를 만든 조건. gross edge, win/loss structure, cost absorption, holding-period behavior, drawdown, reward/risk 등을 저장 근거로 씁니다.
- `failure_drivers`: 결과가 나쁠 때 성과를 막은 조건. gross-vs-net gap, churn, exit mix, cost drag, insufficient edge, reward/risk geometry 등을 저장 근거로 씁니다.
- `bounded_conclusion`: 현재 전략명, 버전, 조건, 기간, 비용 가정 안에서 말할 수 있는 결론을 저장합니다.
- `generalization_boundary`: 이 결과만으로 전략군 전체를 기각하거나 보편적 성공을 주장할 수 없는 이유를 저장합니다.
- `broader_claim_requirements`: 전략군 전체로 판단 범위를 넓히려면 필요한 검증을 저장합니다. 예: OOS/WFO, 기준선 비교, regime segmentation, 다른 심볼/기간/타임프레임, 다른 신호 정의.
- `risk_interpretation`: 비용, 체결, 구간, 데이터 한계.
- `next_improvements`: 보완점과 그 이유.

해석 경계 저장 규칙:

- 실패 결과라면 `bounded_conclusion`에는 `현재 버전은 이 조건에서 비용 반영 후 유효한 전략으로 보기 어렵다`에 해당하는 결론을 저장할 수 있습니다.
- 실패 결과라도 `generalization_boundary`에는 왜 전략군 전체를 기각하기 이른지 저장합니다. 구현 버전, 신호 정의, 기간, 심볼, 타임프레임, 비용 가정, 파라미터 범위, 빠진 필터/확인 조건을 근거로 씁니다.
- 성공 결과라면 `bounded_conclusion`에는 현재 조건에서 무엇이 통과했는지 저장합니다.
- 성공 결과라도 넓은 검증이 없으면 `generalization_boundary`에 보편적 유효성을 주장할 수 없다고 저장합니다.
- `broader_claim_requirements`는 더 큰 주장을 위한 필요한 검증을 적습니다. 결과를 꾸미기 위한 일반 문구가 아니라, 현재 payload의 부족한 축을 기준으로 씁니다.

`title.stable_strategy_description`은 report subtitle과 첫 문단의 원천입니다. 실험별 행동을 쓰지 말고 전략 자체를 설명합니다.

`title.version_change_summary`는 전략 버전이나 핵심 메커니즘이 바뀐 경우에만 채웁니다. 예를 들어 고정 R 손익 기준에서 ATR 기준 손익 기준으로 바뀌면 이 차이를 짧게 저장합니다.

`hypothesis_and_theory`는 legacy object name일 수 있지만 최종 리포트에 standalone `가설` section을 만들라는 뜻이 아닙니다. `tested_assumptions`가 있으면 `가설` heading 없이 `핵심 요약`, `백테스트 설정`, 또는 `해석`에 녹입니다. `references`는 strategy 문서의 레퍼런스를 report writer가 짧게 연결할 수 있도록 저장합니다. 레퍼런스가 없으면 full report 생성 전에 strategy 문서를 먼저 보강합니다.
`hypothesis_and_theory.mechanism_detail`, `failure_mechanism`, `evidence_boundary`, `optional_formulas`, `momentum_mechanisms`는 레퍼런스 이름만 나열하는 것을 막기 위한 선택 필드입니다. 현재 백테스트가 메커니즘을 직접 증명하지 못하면 `evidence_boundary`에 그 한계를 저장합니다.
모멘텀 계열 리포트에서는 strategy 문서와 저장 근거가 허용하는 범위에서 과소반응, 느린 포지션 조정, 리스크 프리미엄/tail risk, 헤저/투기자 구조, spot Bitcoin 적용 한계를 저장합니다. 해당 구조가 현재 시장이나 instrument에 맞지 않으면 null로 둡니다.

`setup.algorithm_explanation`은 `백테스트 설정`에서 rule mechanics를 설명하기 위한 선택 필드입니다. 중요한 진입/청산/indicator/cost guard가 있으면 의사코드와 no-lookahead 설명을 저장합니다. 기본값은 explanatory pseudocode입니다. 정확 구현 인용일 때만 `source_reference`를 채우고, 일반 daily report에서는 내부 구현 세부사항을 불필요하게 노출하지 않습니다.

`presentation_notes.table_purposes`는 큰 표를 만들기 전에 표가 답하는 질문을 기록하기 위한 선택 필드입니다. 목적이 다른 지표를 한 표에 섞지 않도록 돕습니다.
`presentation_notes.chart_purposes`는 각 이미지가 답하는 질문을 기록합니다. 이미지가 `해석`에서 쓰이지 않으면 생성하거나 본문에 넣지 않습니다.
`presentation_notes.required_interpretive_takeaways`는 future report writer가 `해석`에서 반드시 다시 회수해야 할 표, 이미지, metric 근거를 저장합니다. 예: `result comparison table -> 4h_3d_to_1d만 gross no-cost가 양수였고, side attribution은 short 쪽 편중을 보였다`.
`presentation_notes.logic_chain`은 V1처럼 촘촘한 논리를 쓰기 위한 선택 필드입니다. 전략 아이디어, 실험 변경점, 핵심 결과, supporting driver, limiting evidence, bounded conclusion, cannot conclude, next action with reason을 저장합니다.
V2-style data display를 위해 data coverage, result comparison, cost impact, exit mix, side attribution, yearly/regime attribution, representative trades를 가능한 범위에서 저장합니다. 단, reader-facing 표나 이미지는 반드시 `table_purposes`, `chart_purposes`, 또는 `required_interpretive_takeaways` 중 하나와 연결되어야 합니다.
V1-style logic density를 위해 표와 이미지가 결과의 성공, 실패, 혼합 원인 중 무엇을 설명하는지 저장합니다. 원인을 설명하지 못하는 표는 payload metadata에 남기고 본문 표로 승격하지 않습니다.

패턴, 필터, 이미지, 타임프레임 coverage가 없다는 사실은 기본 payload 설명문에 넣지 않습니다. 의사결정에 중요하면 `risk_interpretation` 또는 `next_improvements`에만 넣습니다. 예를 들어 `5m` local closed candle coverage가 없어 빠진 비교는 리드 문장이 아니라 `next_improvements`에 저장합니다.

대표 거래에는 데이터가 있을 때만 시장 상황 맥락을 저장합니다. 거래량, candle body/range, volatility, 보유 시간, 비용 비중, 진입 후 추세 지속/반전/횡보, 근처 drawdown/equity 상태가 없으면 null로 두고 리포트에서 만들지 않습니다.
`representative_trades.*.diagnostic_narrative_inputs`는 대표 거래 설명을 더 깊게 쓰기 위한 선택 필드입니다. 이 필드의 항목은 최종 리포트의 visible heading이나 체크리스트가 아니라, 자연스러운 거래 설명 안에 녹일 근거입니다. 단일 차트만으로 판단할 수 없는 recurrence, performance distortion, engine/fill sanity는 aggregate 근거가 없으면 null 또는 `missing_evidence_note`로 남깁니다.

## 5. Tistory 이미지 삽입 메모

Payload의 image filename은 계속 filename-only로 저장합니다. `report-ko.html` preview에서는 같은 폴더의 PNG를 `<div class="section-image"><img src="./[filename].png" ...></div>` 안에 넣습니다.
Tistory 최종 게시 직전 owner가 이미지를 다시 업로드하면 local `<img>` 대신 아래처럼 Tistory token을 넣을 수 있어야 합니다.

```html
<div class="section-image">
  [##_Image|...|alignCenter|width="100%"|_##]
</div>
```

`...`는 fake/generic placeholder입니다. 실제 Tistory `kage@...` 식별자는 report data rules나 reusable docs에 고정하지 않습니다.

## 6. 필수 고정 이미지

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
- 권장 canvas는 `1800px x 1000px`입니다.
- equity와 drawdown 패널, 제목, legend, axis label이 잘리지 않도록 padding을 둡니다.

### cost_impact.png

- 거래비용 반영 전후를 비교하는 그래프입니다.
- 비용 단계별 equity curve가 있으면 line chart를 사용합니다.
- 비용 단계별 equity curve가 없고 aggregate 값만 있으면 bar chart를 사용합니다.
- line chart가 가능할 때는 no cost equity, fee only equity, fee + spread equity, fee + spread + slippage equity를 비교합니다.
- bar chart만 가능할 때는 gross PnL, fee, spread, slippage, net PnL을 비교합니다.
- 주석에는 total fee, total spread, total slippage, total transaction cost, gross PnL, net PnL, final return after costs를 가능한 범위에서 넣습니다.
- chart title이나 label에는 `cost stress`라는 표현을 쓰지 않습니다.
- 권장 canvas는 `1800px x 1000px`입니다.
- 비용 항목과 순손익 라벨이 겹치면 수치를 annotation band나 표로 옮기고 chart bar/line 위에 긴 문장을 올리지 않습니다.

### representative_win_trade.png

- 대표 수익 거래 차트입니다.
- OHLC candle data가 있으면 candlestick chart로 만듭니다.
- 거래 전후 window의 candles, entry marker, exit marker, stop line, target line, pattern zone 또는 signal zone을 가능한 범위에서 표시합니다.
- side, entry price, exit price, entry time, exit time, net PnL, exit reason을 표시합니다.
- `representative_trades.best_trade`가 있으면 우선 사용합니다.
- 없으면 전략 논리를 설명하기 쉬운 수익 거래를 고릅니다.
- 권장 canvas는 `1800px x 1000px`입니다.
- `reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/representative_win_trade.png`처럼 surrounding candles와 별도 하단 annotation band가 보이도록 만듭니다.
- 최소한 entry-to-exit 구간 전체, entry 전 `10`개 candle, exit 후 `10`개 candle을 포함합니다. 데이터가 부족하면 가능한 전체 주변 candle을 씁니다.
- 거래 기간이 길면 진입 전후 context는 거래 길이의 `30%` 이상을 우선하되, 너무 촘촘하면 x축 tick 수를 줄이고 window를 crop하지 않습니다.
- y축은 local high/low, entry, exit, stop, target을 모두 포함하고 여백을 둡니다.

### representative_loss_trade.png

- 대표 손실 거래 차트입니다.
- OHLC candle data가 있으면 candlestick chart로 만듭니다.
- 거래 전후 window의 candles, entry marker, exit marker, stop line, target line, 실패한 pattern zone 또는 signal zone을 가능한 범위에서 표시합니다.
- side, entry price, exit price, entry time, exit time, net PnL, exit reason을 표시합니다.
- `representative_trades.worst_trade`가 있으면 우선 사용합니다.
- 없으면 전략의 약점을 설명하기 쉬운 손실 거래를 고릅니다.
- 권장 canvas는 `1800px x 1000px`입니다.
- 수익 거래 이미지와 동일하게 surrounding candles와 별도 annotation band를 사용합니다.
- 최소한 entry-to-exit 구간 전체, entry 전 `10`개 candle, exit 후 `10`개 candle을 포함합니다. 데이터가 부족하면 가능한 전체 주변 candle을 씁니다.
- y축은 local high/low, entry, exit, stop, target을 모두 포함하고 여백을 둡니다.
- 손실 원인 라벨이 candle이나 stop/target line과 겹치면 plot 위 긴 라벨을 제거하고 annotation band에서 설명합니다.

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
- `report-ko.html` exists.
- `summary_equity_curve.png` exists.
- `cost_impact.png` exists.
- `representative_win_trade.png` exists.
- `representative_loss_trade.png` exists.
- `images/` 하위 폴더가 없습니다.
- `report-en.html`, `report-en.md`, `image_plan.md`, `image_plan.json` 파일이 없습니다.
- 모든 equity curve 이미지는 drawdown을 같은 이미지 안에 포함합니다.
- 별도의 `drawdown_curve.png`는 명시 요청이 없으면 생성하지 않습니다.
- 모든 PNG가 의도한 canvas dimensions를 충족합니다.
- 이미지 크기 조정 과정에서 crop이 사용되지 않았습니다.
- axis label, tick label, title, subtitle, legend, annotation, entry/exit marker, stop/target line이 이미지 밖으로 잘리지 않았습니다.
- representative trade 이미지는 candle data가 있을 때 pre-entry와 post-exit context를 포함합니다.
- representative trade y-axis가 entry, exit, stop, target, local high/low를 padding과 함께 포함합니다.
- chart text, right-edge price label, legend, callout이 서로 겹치지 않습니다.
- dense metrics는 candle plot 위가 아니라 annotation band 또는 HTML 본문/표에 있습니다.
- payload의 모든 이미지 참조는 `/`가 없는 파일명입니다.
- `report-ko.html`의 모든 이미지 참조는 같은 폴더 기준 `./[filename].png`입니다.
- `report-ko.html`에는 task 번호, run id, 내부 candidate id가 없습니다.
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
E[R] = P(win) x AvgWin - P(loss) x AvgLoss - Cost
```

수익률만 저장하지 말고, 승률, 평균 이익, 평균 손실, 손익비, 수수료, 슬리피지를 함께 저장합니다.

## 10. 금지 사항

- daily report 이미지에 task 번호, run id, 내부 candidate id를 노출하지 않습니다.
- 저장된 graph/equity/trade/cost 데이터가 없는데 임의 곡선을 만들지 않습니다.
- smoothing으로 성과 곡선을 보기 좋게 바꾸지 않습니다.
- live trading, private API, credential 사용을 하지 않습니다.
- payload에는 `.env`, API key, DB dump, 원본 CSV dump를 넣지 않습니다.
