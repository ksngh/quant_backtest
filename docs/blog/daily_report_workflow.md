# Daily Report Workflow Rules

이 문서는 사용자가 특정 전략에 대해 daily report 작성을 요청했을 때 따라야 하는 워크플로우 규칙입니다.

목표는 요청이 들어올 때마다 같은 순서로 판단하고, 필요한 데이터가 있을 때만 `docs/blog/template.md` 형식의 리포트를 작성하는 것입니다.

## 1. 적용되는 요청

다음과 같은 요청에 적용합니다.

- "`[전략명]`으로 daily report 써줘"
- "`[전략명]` 오늘 백테스트 리포트 작성해줘"
- "`[run id 또는 저장된 결과]`로 블로그 글 작성해줘"
- "방금 돌린 백테스트 결과를 daily report로 정리해줘"
- "이 전략 결과를 `template.md` 형식으로 정리해줘"

요청에 전략명, run id, 저장된 payload, 또는 방금 실행한 백테스트 결과가 포함되어 있으면 이 워크플로우를 사용합니다.

## 2. 기본 원칙

- 리포트는 `docs/blog/template.md` 형식을 따릅니다.
- 리포트 작성 데이터는 `docs/blog/backtest_report_data_rules.md`의 payload 규칙을 따릅니다.
- 작성 프롬프트는 `docs/blog/agent_handoff_prompt.md`를 기준으로 합니다.
- 제공되지 않은 값은 추정하지 않습니다.
- 누락된 필수 값은 `[확인 필요]`로 남깁니다.
- 새 백테스트 실행은 별도 task 또는 명시적 실행 지시가 있을 때만 합니다.
- 저장된 결과가 없으면 리포트를 꾸며서 작성하지 않습니다.
- 내부 추적값은 최종 리포트에 쓰지 않습니다.
- live trading, 실제 주문, private endpoint, secret 사용은 하지 않습니다.

## 3. 요청을 받으면 먼저 분류합니다

### A. payload가 이미 제공된 경우

예시:

```text
이 payload로 daily report 써줘: {...}
```

처리:

1. payload가 `docs/blog/backtest_report_data_rules.md` 구조에 맞는지 확인합니다.
2. 누락 필드는 `[확인 필요]`로 처리합니다.
3. `docs/blog/agent_handoff_prompt.md`의 작성 규칙을 적용합니다.
4. 최종 markdown 리포트를 작성합니다.

이 경우 새 백테스트를 실행하지 않습니다.

### B. 저장된 run id가 제공된 경우

예시:

```text
run 1159로 daily report 써줘
```

처리:

1. 저장된 run 결과를 읽을 수 있는지 확인합니다.
2. run 결과에서 daily report payload를 만들 수 있는지 확인합니다.
3. 부족한 값은 `[확인 필요]`로 남깁니다.
4. payload를 만든 뒤 `docs/blog/template.md` 형식으로 리포트를 작성합니다.

주의:

- run id 자체는 최종 블로그 문서에 쓰지 않습니다.
- 내부 추적용으로만 사용합니다.
- 저장된 run에서 필요한 값이 부족하면 새로 만들어내지 않습니다.

### C. 전략명만 제공된 경우

예시:

```text
FVG midpoint 전략으로 daily report 써줘
```

처리:

1. 같은 전략명의 최신 saved payload가 있는지 찾습니다.
2. payload가 있으면 A 흐름으로 진행합니다.
3. payload는 없지만 저장된 backtest run이 있으면 B 흐름으로 진행합니다.
4. 저장된 결과가 없으면 리포트 작성 전에 백테스트 실행 task가 필요하다고 기록합니다.

이 경우 전략명만으로 새 백테스트를 자동 실행하지 않습니다.

### D. "방금 돌린 결과"가 문맥에 있는 경우

예시:

```text
방금 돌린 결과로 daily report 써줘
```

처리:

1. 현재 대화 또는 직전 작업에서 생성된 payload나 saved run을 확인합니다.
2. 확인 가능한 payload가 있으면 A 흐름으로 진행합니다.
3. 확인 가능한 saved run이 있으면 B 흐름으로 진행합니다.
4. 확인 가능한 결과가 없으면 어떤 결과를 사용할지 요청합니다.

## 4. 데이터 확인 순서

리포트 작성 전 아래 순서로 확인합니다.

1. `backtest_report_payload`가 직접 제공되었는지 확인합니다.
2. 제공된 run id나 저장된 결과 참조가 있는지 확인합니다.
3. 전략명으로 매칭 가능한 최신 payload가 있는지 확인합니다.
4. 전략명으로 매칭 가능한 최신 saved run이 있는지 확인합니다.
5. 결과가 없으면 리포트 작성을 멈추고 백테스트 실행 또는 payload 제공이 필요하다고 알립니다.

## 5. 리포트 작성 순서

데이터가 준비되면 다음 순서로 작성합니다.

1. payload를 `docs/blog/backtest_report_data_rules.md` 구조로 정리합니다.
2. 누락값을 `[확인 필요]`로 표시합니다.
3. `docs/blog/template.md`의 섹션 순서를 유지합니다.
4. `docs/blog/agent_handoff_prompt.md`의 문체 규칙을 적용합니다.
5. 그래프 파일명이 있으면 markdown image를 유지합니다.
6. 최종 리포트에는 예시 문장을 남기지 않습니다.
7. 최종 리포트에는 내부 추적값을 넣지 않습니다.

## 6. 작성하면 안 되는 경우

다음 경우에는 완성 리포트를 쓰지 않습니다.

- 전략명만 있고 저장된 payload나 run을 찾을 수 없는 경우.
- 사용자가 새 백테스트 실행을 지시했지만 관련 task가 없는 경우.
- 핵심 결과 수치가 전혀 없는 경우.
- 비용 반영 여부를 알 수 없고 비용 관련 해석이 필요한 경우.
- live trading 또는 실제 주문 결과처럼 오해될 수 있는 데이터를 구분할 수 없는 경우.

이때는 필요한 입력을 짧게 정리합니다.

예시:

```text
이 전략의 daily report를 쓰려면 saved payload 또는 saved run이 필요합니다. 현재 확인 가능한 결과가 없어서 리포트를 작성하지 않았습니다.
```

## 7. 새 백테스트가 필요한 경우

전략명은 있지만 저장된 결과가 없으면 새 백테스트가 필요합니다.

이때 흐름:

1. 백테스트 실행이 현재 task 범위에 포함되어 있는지 확인합니다.
2. 포함되어 있지 않으면 새 task가 필요하다고 기록합니다.
3. 백테스트 task가 실행되어 결과가 저장된 뒤 payload를 만듭니다.
4. payload가 준비된 뒤 daily report를 작성합니다.

daily report 요청만으로 새 전략 개발이나 새 백테스트를 자동 실행하지 않습니다.

## 8. 결과 저장 규칙

백테스트 실행 후 daily report 작성을 예상한다면 결과 저장 시 다음 값을 우선 저장합니다.

- 전략명.
- 시장/심볼/타임프레임.
- 기간.
- PR.
- equity curve 이미지 파일명.
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
- 대표 거래 4개.
- 결과 해석.
- 위험 해석.
- 결론.

필드 이름과 구조는 `docs/blog/backtest_report_data_rules.md`를 따릅니다.

## 9. 최종 출력 규칙

daily report 최종 출력은 markdown만 사용합니다.

포함:

- `# [전략명] 백테스트 리포트`
- 핵심 요약.
- 가설 2개.
- 가정과 이론적 배경.
- 전략 규칙.
- 백테스트 설정.
- 결과.
- 착시 가능성.
- 대표 거래.
- 해석.
- 결론.

제외:

- 내부 run 추적값.
- 내부 config 전문.
- commit hash.
- 파일 목록.
- 별도 작업 계획.
- 후속 실험 제안.

## 10. 짧은 실행 예시

요청:

```text
FVG midpoint 전략으로 daily report 써줘
```

판단:

```text
전략명만 제공됨 -> saved payload 검색 -> 없으면 saved run 검색 -> 있으면 payload 변환 -> report 작성
```

결과가 있는 경우:

```text
docs/blog/template.md 형식으로 최종 markdown 리포트를 작성합니다.
```

결과가 없는 경우:

```text
저장된 payload 또는 saved run이 없어 daily report를 작성하지 않습니다. 먼저 백테스트 실행 또는 payload 제공이 필요합니다.
```
