# Strategy Documentation Rules

이 디렉터리는 백테스트, 모델 개발, 전략 수정 전에 반드시 읽거나 작성해야 하는 전략 문서를 보관합니다.

## Required Order

전략/모델/백테스트 작업은 아래 순서를 따릅니다.

```text
state files -> relevant task.md -> relevant docs/strategy/*.md -> implementation/backtest/report generation
```

규칙:

- 관련 task가 없으면 strategy 문서를 만들기 전에 task를 먼저 만들고 멈춥니다.
- 관련 task는 있지만 strategy 문서가 없으면 `STRATEGY_TEMPLATE.md`를 기준으로 strategy 문서를 만들고 멈춥니다.
- strategy 문서와 task가 모두 있어야 전략 구현, 파라미터 튜닝, 백테스트 실행, 검증 run 저장을 진행할 수 있습니다.
- 전략 로직, 리스크 로직, 비용 가정, 체결 가정, 검증 구간, research-only/live-trading boundary가 바뀌면 같은 task 안에서 strategy 문서를 업데이트합니다.

## File Naming

파일명은 report-facing strategy slug와 버전을 사용합니다.

```text
docs/strategy/[strategy-slug]_[version].md
```

예시:

```text
docs/strategy/priority_ensemble_activity_scout_v1.md
docs/strategy/fvg_midpoint_v1.md
docs/strategy/liquidity_sweep_reversal_v2.md
```

## Boundary

이 디렉터리의 문서는 연구 설계와 검증 계획을 기록하기 위한 것입니다. 실거래 승인 문서가 아닙니다.

전략 문서가 존재해도 아래는 여전히 금지됩니다.

- live trading.
- real order execution.
- exchange order/account/private endpoint usage.
- secrets, API keys, `.env` changes.
- leverage/futures behavior unless a later task explicitly assigns it.
