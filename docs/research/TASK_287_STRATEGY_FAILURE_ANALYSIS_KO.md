# Task 287 전략 실패 분석 문서

문서 상태: `RESEARCH_ONLY_RECORD`

작성일: `2026-05-31`

관련 보고서:

- `reports/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md`
- `reports/TASK_285_REGIME_ROBUST_MULTI_WINDOW_STRATEGY_REPAIR.md`
- `reports/TASK_284_TASK283_MULTI_AXIS_ROBUSTNESS_REVALIDATION.md`
- `reports/TASK_283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT.md`
- `reports/TASK_281_OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH.md`

관련 DB run:

- Task 287: `1085`-`1159`
- Primary candidate: `T285_R3_CORE_SHORT_ONLY_B2`
- Comparators:
  - `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`
  - `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`

최종 결론:

- `T285_R3_CORE_SHORT_ONLY_B2`는 `2026-05-20+`, `2026-05-25+` owner replay에서는 수익이 났지만, repaired `2026-04-20+` 전체 구간과 pre-owner 구간에서 강하게 실패했다.
- 실패 원인은 수수료 계산 오류가 아니라 전략 가설 자체의 구간 의존성, 비용 취약성, 독립 구간 불안정성, 그리고 1분봉 short-only liquidity sweep fade 구조의 낮은 순 기대값이다.
- Task 287 비용 검증 결과는 정상이다. 75개 run 모두 fee/spread/slippage가 non-zero였고 formula mismatch와 summary mismatch가 모두 `0`이었다.
- 따라서 이 전략은 live/paper로 승격하면 안 되고, 새 모델 개발은 별도 task에서 train/OOS split과 비용 stress gate를 먼저 고정한 뒤 진행해야 한다.

## 1. 전략이 무엇이었는가

### 1.1 전략 이름

Primary locked candidate:

```text
T285_R3_CORE_SHORT_ONLY_B2
```

전략 계보:

```text
Task 281 high-activity owner-window model
-> Task 283 principle-first LSR/MTF priority ensemble
-> Task 284 locked robustness revalidation
-> Task 285 short/core-only repair
-> Task 287 repaired 0420 locked OOS/WFO validation
```

Task 287에서 검증한 primary 전략은 새로운 전략이 아니다. Task 285에서 선택된 `T285_R3_CORE_SHORT_ONLY_B2`를 그대로 replay한 locked no-retune 전략이다.

### 1.2 전략의 핵심 아이디어

전략의 핵심은 다음 한 문장으로 요약된다.

```text
최근 고점 위로 가격이 찔렀지만 종가가 다시 고점 아래로 들어오고,
단기/중기 모멘텀이 이미 약하면,
그 상승은 진짜 돌파가 아니라 stop-liquidity sweep일 가능성이 있으며,
forced buying이 끝난 뒤 하락 반전 또는 하락 지속이 나올 수 있다.
```

즉, 이 전략은 bullish breakout을 따라가는 전략이 아니라, 실패한 상단 돌파를 short으로 fade하는 전략이다.

### 1.3 시장 미시구조 원리

비트코인 1분봉 시장에서 이 가설이 그럴듯해 보였던 이유는 다음과 같다.

1. 최근 고점 근처에는 short stop, breakout buy stop, 추격 매수 주문이 몰릴 수 있다.
2. 가격이 최근 고점을 살짝 넘으면 stop과 breakout order가 시장가 매수로 체결될 수 있다.
3. 이 매수 흐름이 새로운 정보 기반 매수가 아니라 stop-triggered flow라면, 체결 이후 추가 수요가 약해질 수 있다.
4. 그 상태에서 종가가 다시 이전 range 안쪽으로 들어오면, 돌파 실패 신호가 된다.
5. 이미 60분/240분 prior return이 약하면, 상단 sweep 이후의 매수는 trend reversal이 아니라 일시적 squeeze일 가능성이 커진다.
6. 그러면 short 진입 후 가격이 다시 range 안으로 내려오면서 수익이 발생할 수 있다.

경제학적으로는 다음 구조다.

```text
주문 집중 구간 -> 강제 체결 -> 일시적 가격 왜곡 -> 추가 수요 부재 -> 가격 정상화
```

수학적으로는 단기 가격이 efficient price에서 잠시 이탈했다가 다시 되돌아오는 microstructure mean reversion 가설이다.

### 1.4 실제 signal 수식

사용 데이터:

- `BTCUSDT`
- `1m` candle
- `open`, `high`, `low`, `close`, `volume`
- completed candle only
- signal candle과 execution candle 분리

기본 표기:

```text
C_t = t 시점 close
O_t = t 시점 open
H_t = t 시점 high
L_t = t 시점 low
H60_{t-1} = t 이전 60개 candle high의 max
r60_t = C_{t-1} / C_{t-61} - 1
r240_t = C_{t-1} / C_{t-241} - 1
```

bps 변환:

```text
return_bps = return * 10000
```

단기 모멘텀 vote:

```text
v60 =
  -1, if r60_bps < -80
  +1, if r60_bps > +80
   0, otherwise
```

중기 모멘텀 vote:

```text
v240 =
  -1, if r240_bps < -20
  +1, if r240_bps > +20
   0, otherwise
```

상단 liquidity sweep / failed breakout vote:

```text
vfade =
  -1, if H_t > H60_{t-1} and C_t < H60_{t-1}
   0, otherwise
```

core short signal:

```text
v60 + v240 + vfade <= -2
```

즉, 세 요소 중 최소 두 개가 bearish일 때만 short signal이 발생한다.

추가 조건:

- warmup `960` bars
- Sunday UTC `12`-`18` hour core signal skip
- incomplete hold geometry skip
- Task 285 repair filter:

```text
side == SHORT
and task283_layer == core
```

Task 285의 `core_short_only` repair는 long과 scout sleeve를 제거하고 full-size core short만 남겼다.

### 1.5 진입, 손절, 익절 구조

전략의 locked exit geometry:

```text
core_target_bps = 260 bps
core_stop_bps   = 130 bps
core_hold_bars  = 480 bars
core_fraction   = 1.00
```

short 기준:

```text
Entry Price = signal candle 다음 candle open
Take Profit = 약 entry 기준 -2.60%
Stop Loss = 약 entry 기준 +1.30%
Nominal gross R = 260 / 130 = 2.0R
Max Hold = 480분
```

실행 순서:

- signal은 completed candle에서 생성한다.
- entry는 다음 candle open에 실행한다.
- stop/target 조건은 candle high/low로 감지한다.
- stop과 target이 같은 candle에서 모두 닿으면 보수적으로 stop-first로 처리한다.
- Task 283 B2 계열은 exit condition 발생 후 다음 candle open에서 청산하는 shifted-exit 구조를 사용한다.

### 1.6 왜 손익비가 좋아 보였는가

gross 기준으로는 2R 전략이다.

무비용 가정의 break-even win rate:

```text
Required Win Rate = Loss / (Win + Loss)
                  = 1R / (2R + 1R)
                  = 33.33%
```

즉, 비용이 없다면 약 33.33%만 맞아도 기대값이 0이다.

하지만 1분봉 crypto 시장에서는 이 계산이 그대로 성립하지 않는다. 왕복 비용이 stop과 target 모두에 영향을 준다.

Task 287 base run `1085`의 effective one-way cost는 약 `18.8127 bps`였다.

대략적인 왕복 비용:

```text
round_trip_cost_bps ~= 18.8127 * 2
                    ~= 37.6254 bps
```

short target과 stop을 비용 반영 후 단순화하면:

```text
Gross target = 260 bps
Gross stop   = 130 bps

Net win  ~= 260 - 37.6 = 222.4 bps
Net loss ~= 130 + 37.6 = 167.6 bps
```

비용 반영 break-even win rate:

```text
Required Win Rate ~= 167.6 / (222.4 + 167.6)
                  ~= 42.97%
```

따라서 nominal 2R 전략이지만, 실제로는 약 43% 이상의 승률이 필요했다.

Task 287 full 0420+ primary run `1085`의 관측 win rate:

```text
Observed Win Rate = 34.00%
```

이는 비용 반영 break-even보다 한참 낮다.

### 1.7 수수료, 스프레드, 슬리피지 구조

Task 287의 base cost profile은 `conservative_crypto_1m`이다.

구성:

```text
taker_fee_bps = 10.0
spread_bps = 3.0
slippage_bps = 5.0
minimum_slippage_bps = 1.0
volatility_slippage_multiplier = 0.1
```

실제 effective slippage:

```text
effective_slippage_bps
= max(minimum_slippage_bps, slippage_bps + volatility_bps * volatility_slippage_multiplier)
```

execution별 cost:

```text
fee_cost      = notional * fee_bps / 10000
spread_cost   = notional * spread_bps / 10000
slippage_cost = notional * effective_slippage_bps / 10000
total_cost    = fee_cost + spread_cost + slippage_cost
```

Task 287에서 비용이 적게 잡힌 것이 아니다. primary full run `1085` 기준:

```text
executed notional = 87,713,793.76
fee               = 87,713.79
spread            = 26,314.14
slippage          = 50,985.41
total cost        = 165,013.34
effective one-way = 18.8127 bps
formula mismatch  = 0
summary mismatch  = 0
```

즉, 비용은 충분히 크게 반영되었고, 전략의 gross edge가 그 비용을 이기지 못했다.

## 2. 왜 이 전략을 선택했는가

### 2.1 이전 결과에서 short core가 가장 그럴듯해 보였다

Task 281, Task 283, Task 284 과정에서 owner window `2026-05-20+`에서는 core/scout ensemble이 높은 수익을 냈다.

하지만 Task 284 이후 분석에서 다음 문제가 드러났다.

- long/scout sleeve는 turnover를 늘렸지만 edge가 약했다.
- 수익은 주로 short side에 집중됐다.
- owner window에서 강하게 맞은 방향은 bearish failed-rally 구조였다.
- pre-owner 구간은 약하거나 음수였다.

그래서 Task 285에서는 다음 repair 가설을 세웠다.

```text
문제가 long/scout dilution이라면,
long과 scout을 제거하고 core short만 남기면
edge가 더 순수하게 드러날 수 있다.
```

이것이 `T285_R3_CORE_SHORT_ONLY_B2` 선택의 직접적인 이유다.

### 2.2 경제학적 선택 이유

비트코인 1분봉에서 short-only failed-rally가 특히 후보가 될 수 있었던 이유:

- BTC는 레버리지 참여자가 많아 고점 위 stop cluster가 자주 형성된다.
- 급등 후 상단 wick 또는 close-back-inside가 나오면 forced buying exhaust로 볼 수 있다.
- 1분봉에서는 작은 가격 왜곡도 full-notional short에서 의미 있는 PnL로 증폭될 수 있다.
- owner window `2026-05-20+`는 하락 압력 또는 반등 실패 구조가 강하게 나타난 구간이었다.

### 2.3 수학적 선택 이유

전략은 단순 RSI나 MACD 조합이 아니라 세 가지 조건의 joint event를 본다.

```text
P(short edge)
= P(mean reversion after upper sweep | prior 60m weakness, prior 240m weakness)
```

단일 조건이 아니라 conditional edge를 노린 것이다.

구조:

```text
상단 liquidity sweep
and 단기 momentum 약세
and 중기 momentum 약세
=> short
```

이 방식은 단순한 과매수/과매도보다 원리 측면에서 더 낫다. 문제는 원리가 틀렸다기보다, 그 원리가 특정 구간에서만 성립했고 비용 이후에는 일반화되지 않았다는 점이다.

## 3. 실험을 어떻게 진행했는가

### 3.1 실험 목표

Task 287의 목표는 수익률을 높이는 것이 아니라 locked validation이었다.

명시적 원칙:

- no retune
- no parameter search
- no new factor
- no model redesign
- owner window만으로 promotion 금지
- repaired `2026-04-20+` 데이터 전체에서 검증
- 모든 decision-driving run DB 저장
- realistic fee/spread/slippage 반영

### 3.2 데이터

검증 대상:

```text
source = binance_spot
symbol = BTCUSDT
interval = 1m
start = 2026-04-20T00:00:00Z
end = 2026-05-28T08:26:00Z
```

Task 286 이후 repaired data guard:

```text
closed candles = 55227
expected continuous candles = 55227
continuity gaps = 0
duplicate open-time groups = 0
April-20-forward complete = True
```

따라서 Task 282/284/285에서 있었던 April/May missing-data blocker는 Task 287에서는 제거됐다.

### 3.3 검증 후보

Primary:

```text
T285_R3_CORE_SHORT_ONLY_B2
```

Comparators:

```text
T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002
T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002
```

비교 후보를 둔 이유:

- Task 283 B2는 repair 전 원본 principle-first ensemble이다.
- Task 281 B1은 owner-window high-activity 성공 모델이다.
- Task 285 R3가 정말 개선이었다면 원본/legacy보다 더 안정적이어야 한다.

### 3.4 검증 구간

Decision-driving windows:

```text
full_0420_latest        = 2026-04-20T00:00:00Z ~ 2026-05-28T08:26:00Z
pre_owner_0420_0519     = 2026-04-20T00:00:00Z ~ 2026-05-19T23:59:00Z
owner_replay_0520_latest
owner_replay_0525_latest
```

독립 weekly windows:

```text
w1_0420_0426
w2_0427_0503
w3_0504_0510
w4_0511_0517
w5_0518_0524
w6_0525_latest
```

WFO reporting partitions:

```text
wfo_0420_0503
wfo_0504_0517
wfo_0518_latest
```

Endpoint diagnostics:

```text
full_0420_drop_first_6h
full_0420_drop_first_24h
full_0420_drop_last_6h
full_0420_drop_last_24h
owner_0520_drop_last_12h
owner_0520_drop_last_24h
```

### 3.5 비용 프로필

Base:

```text
conservative_crypto_1m
```

Stress:

```text
cost_2x
cost_3x
high_slippage_stress
```

Task 287에서는 zero-cost run을 promotion evidence로 쓰지 않았다.

### 3.6 pass/fail gate

OOS supported로 인정하려면 최소 다음 조건을 모두 통과해야 했다.

```text
full 0420+ return >= +3%
full 0420+ completed trips >= 50
pre-owner return > 0%
independent weekly windows >= 4
independent positive fraction >= 75%
independent aggregate return >= +3%
single independent window contribution <= 60%
return without top-three winners > 0%
full cost/gross <= 0.60
2x cost full return > -1%
3x cost full return reported
cost formula mismatch = 0
summary cost mismatch = 0
no data anomaly
```

### 3.7 실험 결과 요약

Primary `T285_R3_CORE_SHORT_ONLY_B2`:

| 구간 | Return | Trips | 해석 |
| --- | ---: | ---: | --- |
| full_0420_latest | `-13.0706%` | `50` | 전체 repaired OOS 실패 |
| pre_owner_0420_0519 | `-17.4283%` | `39` | owner 이전 구간 강한 실패 |
| owner_replay_0520_latest | `+6.1764%` | `10` | owner 구간만 성공 |
| owner_replay_0525_latest | `+3.6703%` | `5` | 더 좁은 owner 구간 성공, 표본 작음 |
| independent weekly aggregate | `-8.2103%` | - | 독립 구간 실패 |
| 2x cost full | `-27.9587%` | `50` | 비용 stress 취약 |
| 3x cost full | `-40.2970%` | `50` | 비용 stress 붕괴 |
| high slippage full | `-32.4273%` | `50` | 슬리피지 stress 붕괴 |

Comparators:

| Candidate | Full 0420+ | Trips | Independent aggregate | Classification |
| --- | ---: | ---: | ---: | --- |
| `T283_B2...` | `-15.0301%` | `318` | `-10.0735%` | `COST_FRAGILE` |
| `T281_B1...` | `-14.7305%` | `318` | `-10.0970%` | `COST_FRAGILE` |

즉, primary만 실패한 것이 아니다. repair 전 ensemble과 legacy owner model도 repaired 0420+ OOS에서는 같이 실패했다.

## 4. 실험의 한계

### 4.1 데이터 기간이 짧다

검증 기간은 약 38일이다.

```text
2026-04-20 ~ 2026-05-28
```

1분봉 수는 많지만 regime 수는 많지 않다. BTC의 장기적인 bull, bear, chop, liquidation cascade, low-vol compression, event-news shock를 충분히 포괄한다고 보기 어렵다.

### 4.2 tick/order book 데이터가 없다

이 실험은 1분봉 OHLCV만 사용했다.

없는 데이터:

- bid/ask quote
- order book depth
- trade aggressor side
- queue position
- 실제 spread 변화
- partial fill
- market impact
- liquidation print
- funding rate
- futures open interest

따라서 liquidity sweep이라는 이름을 썼지만, 실제 stop order나 liquidation flow를 직접 관측한 것이 아니다. OHLCV로 만든 proxy다.

### 4.3 short 체결은 simulated cash-bounded short다

전략은 spot BTCUSDT 데이터를 사용하지만 short을 시뮬레이션했다.

주의점:

- 실제 spot 계좌에서는 borrow/margin 없이는 BTC short을 할 수 없다.
- 이 백테스트는 futures funding, borrow cost, liquidation, margin requirement를 반영하지 않는다.
- 따라서 실제 운용 가능성은 별도 execution/risk task 없이는 평가할 수 없다.

Task 287 결론이 research-only인 이유 중 하나다.

### 4.4 candle 내부 체결 순서의 불확실성

1분봉에서 stop과 target이 같은 candle에서 모두 touch될 수 있다.

Task 287은 보수적으로:

```text
stop first
```

를 적용했다.

이건 낙관 편향을 줄이지만, 실제 tick path를 알 수 없다는 한계는 남는다.

### 4.5 비용 모델은 정적이다

Task 287은 conservative cost와 stress cost를 썼지만, 실제 시장에서는 비용이 상태 의존적이다.

실제 비용은 다음에 따라 달라진다.

- order size
- order book depth
- volatility spike
- market session
- exchange congestion
- taker flow imbalance
- news/liquidation event

Task 287의 cost stress는 이 문제를 일부 다루지만, 실제 체결 품질 전체를 대체하지는 못한다.

### 4.6 이전 연구 과정의 data-snooping 위험

Task 281/283/285 후보는 owner window 성과를 관찰한 뒤 발전했다.

Task 287은 no-retune 검증이라 data-snooping을 더 늘리지는 않았지만, 검증 대상 전략 자체는 과거 fixed owner window 성과를 보고 선택된 계보를 가진다.

즉:

```text
Task 287 = locked validation
전략 계보 = owner-window influenced
```

이 차이를 명확히 봐야 한다.

## 5. 전략이 틀린 이유

### 5.1 가장 큰 이유: edge가 owner window에 집중됐다

Primary 전략은 owner replay에서는 좋아 보였다.

```text
2026-05-20+ return = +6.1764%
2026-05-25+ return = +3.6703%
```

하지만 repaired full OOS에서는:

```text
2026-04-20+ return = -13.0706%
pre-owner return = -17.4283%
```

이는 전략이 보편적 edge가 아니라 특정 구간의 하락 구조에 맞아떨어진 가능성을 강하게 시사한다.

특히 owner window는 검증 독립성이 낮다. 이 구간은 여러 이전 task에서 반복적으로 관찰되고 모델 선택에 영향을 주었다.

### 5.2 liquidity sweep fade 가설이 모든 regime에서 맞지 않았다

전략은 다음을 가정했다.

```text
최근 고점 sweep + close back inside + bearish momentum
=> failed rally
=> short edge
```

하지만 실제로는 pre-owner 구간에서 이 패턴이 자주 손실로 이어졌다.

가능한 시장 해석:

- 고점 sweep이 stop-hunt가 아니라 trend continuation의 early breakout이었다.
- close-back-inside가 진짜 reversal이 아니라 noise였다.
- prior 60m/240m bearish return이 이미 소진된 정보였고, 오히려 mean-reversion rebound 직전이었다.
- 상승장에서 high sweep은 bearish trap이 아니라 short squeeze continuation 신호가 될 수 있었다.
- 1분봉의 60-bar high는 너무 가까운 구조라 noise sweep이 많았다.

즉, 패턴의 이름은 liquidity sweep이지만 실제로는 다음 두 현상을 구분하지 못했다.

```text
fake breakout after stop run
real breakout or squeeze continuation
```

### 5.3 비용 이후 기대값이 음수였다

full 0420+ primary run:

```text
gross_pnl = +34,307.78
total_cost = 165,013.34
net_pnl = -130,705.56
cost/gross = 4.8098
```

이 숫자가 핵심이다.

gross로는 약간 벌었지만 비용이 gross의 4.8배였다. 즉, 방향 예측이 완전히 틀린 것만이 아니라, 맞은 거래의 크기와 빈도가 1분봉 비용 구조를 이길 만큼 충분하지 않았다.

independent weekly aggregate도 비슷하다.

```text
independent return = -8.2103%
independent cost/gross = 2.0393
```

비용을 2x로 키우면:

```text
full return = -27.9587%
```

3x로 키우면:

```text
full return = -40.2970%
```

이 정도면 비용 stress를 버티는 edge가 아니라 비용에 의해 무너지는 micro-edge다.

### 5.4 nominal 2R이 실제 2R이 아니었다

표면상 손익비:

```text
target = 260 bps
stop = 130 bps
gross R = 2.0
```

하지만 비용 반영 후:

```text
net win ~= 222 bps
net loss ~= 168 bps
required win rate ~= 43%
```

observed full win rate:

```text
34%
```

independent weekly windows에서는 더 나빴다.

따라서 "2R 전략"이라는 표현은 비용 전 gross geometry에만 맞고, 실제 net expectancy에서는 성립하지 않았다.

### 5.5 거래 횟수는 full 기준만 겨우 통과했다

Primary full run은 정확히 `50` trips로 최소 기준을 통과했다.

하지만 weekly로 나누면:

```text
w1 = 7 trips
w2 = 7 trips
w3 = 7 trips
w4 = 10 trips
w5 = 8 trips
w6 = 5 trips
```

대부분 weekly window는 통계적으로 불안정하다.

owner `2026-05-25+`는 `5` trips뿐이다. `+3.6703%`라는 숫자는 커 보이지만, 실제로는 극소수 거래에 의해 만들어진 결과다.

### 5.6 independent weekly consistency가 없었다

Primary independent weekly 결과:

```text
w1 = -6.1071%
w2 = -3.2146%
w3 = -2.4801%
w4 = +0.1067%
w5 = -0.1856%
w6 = +3.6703%
```

positive fraction:

```text
2 / 6 = 33.33%
```

pass gate:

```text
>= 75%
```

즉, 수익은 후반 특정 구간에 몰렸고, 앞 구간 대부분은 손실이었다.

### 5.7 return concentration 문제가 있었다

Task 287 gate에서 primary는 다음도 실패했다.

```text
single-window winner concentration = 0.9717
required <= 0.60
return without top-three winners = -13.3426%
full return without top-three winners = -17.3957%
```

의미:

- 독립 수익은 특정 구간에 과도하게 의존했다.
- 가장 큰 winner들을 제거하면 전략은 더 명확히 음수다.
- edge가 넓게 분포하지 않고 tail event 또는 특정 window에 집중됐다.

### 5.8 short-only repair가 문제를 해결하지 못했다

Task 285의 repair 논리는 다음이었다.

```text
long/scout이 문제라면 제거하고 core short만 남기자.
```

Task 287 결과는 다음을 보여준다.

```text
long/scout 제거는 owner window 성과를 유지했지만,
pre-owner와 full OOS 실패를 해결하지 못했다.
```

즉, 문제의 본질은 sleeve dilution이 아니라 core short signal 자체의 regime dependence였다.

### 5.9 `2026-05-20+` 구간은 bearish failed-rally에 우호적이었다

owner window의 buy-and-hold baseline:

```text
owner_replay_0520_latest buy-and-hold = -4.5907%
owner_replay_0525_latest buy-and-hold = -4.9533%
```

이 구간은 long buy-and-hold가 손실인 하락성 구간이었다.

short-only failed-rally 전략이 이 구간에서 잘 맞은 것은 이상하지 않다. 문제는 이것이 전체 기간에서 반복되지 않았다는 점이다.

pre-owner buy-and-hold:

```text
pre_owner_0420_0519 buy-and-hold = +4.0682%
```

이 구간은 오히려 long 방향성이 있었다. short-only 전략은 구조적으로 불리했다.

따라서 전략의 본질은 alpha라기보다 bearish regime exposure였을 가능성이 높다.

### 5.10 regime filter가 부족했다

전략은 60m/240m return vote를 사용했지만, 이것만으로 bull/rebound/chop/forced-liquidation regime을 구분하기에는 부족했다.

부족했던 것:

- higher timeframe trend alignment
- realized volatility regime
- funding/open interest proxy
- liquidation-like move proxy
- volume expansion versus low-volume drift 구분
- session liquidity regime
- trend continuation breakout과 fake breakout 분류

특히 pre-owner 구간에서는 short signal이 bullish drift 또는 rebound regime과 충돌했을 가능성이 크다.

## 6. 전략이 완전히 무가치한가

아니다. 전략 아이디어 자체는 폐기할 필요가 없다.

하지만 현재 형태는 사용할 수 없다.

유효할 수 있는 조건:

- 명확한 higher-timeframe bearish regime
- 최근 rebound가 low-volume 또는 weak-body인 경우
- high sweep 후 displacement down이 확인되는 경우
- 비용 대비 target distance가 충분한 경우
- stop이 단순 bps가 아니라 구조적 invalidation 위에 놓이는 경우
- signal 수가 충분하면서도 비용/gross가 낮은 경우

현재 locked 전략이 실패한 이유는 원리 자체가 완전히 틀려서라기보다, 원리를 관측하는 proxy와 regime 조건이 너무 약했고, 1분봉 비용 구조에 비해 edge가 작았기 때문이다.

## 7. 다음 모델 개발 전 반드시 반영해야 할 교훈

### 7.1 owner window는 절대 selection target이 되면 안 된다

다음 task에서는 먼저 split을 고정해야 한다.

예시:

```text
train/development = 2026-04-20 ~ 2026-05-10
validation        = 2026-05-11 ~ 2026-05-19
locked test       = 2026-05-20 ~ latest
```

또는 walk-forward를 먼저 고정해야 한다.

중요한 것은 `2026-05-20+` 결과를 보고 전략을 고르는 과정을 막는 것이다.

### 7.2 비용/gross gate를 entry 이전에 고려해야 한다

Task 287 primary full:

```text
gross = +34,307.78
cost = 165,013.34
```

이 정도면 entry edge gate가 사후가 아니라 사전에 있어야 한다.

다음 전략은 최소한 다음을 요구해야 한다.

```text
expected_reward_bps >= k * round_trip_cost_bps
expected_reward_bps / expected_risk_bps after cost >= threshold
```

### 7.3 fixed bps stop/target만으로는 부족하다

260/130 bps fixed geometry는 단순하고 재현 가능하지만 regime-sensitive하지 않다.

다음 모델에서는 비교해야 한다.

- ATR 기반 stop
- swing high/low 기반 stop
- sweep extreme + buffer 기반 stop
- liquidity pool target
- VWAP/mean target
- trailing stop
- time-stop adaptive exit

### 7.4 fake breakout과 real breakout 분류가 핵심이다

이번 전략은 sweep 후 close-back-inside만으로 fake breakout을 가정했다.

다음에는 최소한 다음 feature가 필요하다.

- sweep candle body ratio
- close location value
- post-sweep displacement down
- sweep volume versus prior volume
- retest failure
- higher timeframe trend
- range width / volatility compression 상태
- session open/close proximity

### 7.5 short-only 전략은 regime exposure를 alpha로 착각하기 쉽다

owner window에서 short-only가 잘 된 것은 그 구간이 하락성 구간이었기 때문일 수 있다.

다음에는 반드시 비교해야 한다.

- short-only strategy versus simple short bias baseline
- short signal versus random short entries with same hold distribution
- bearish regime filter alone versus full pattern
- same pattern in bullish, bearish, sideways regime

## 8. 최종 기록

Task 287에서 확인된 사실:

```text
1. 데이터 문제는 해결됐다.
2. 수수료/스프레드/슬리피지 계산 오류는 발견되지 않았다.
3. primary 전략은 full 0420+ 기준 +3% 목표를 충족하지 못했다.
4. primary 전략은 pre-owner 구간에서 크게 실패했다.
5. owner window 수익은 독립 evidence가 아니었다.
6. 비교 후보들도 repaired OOS에서 모두 실패했다.
7. 실패 원인은 accounting 문제가 아니라 전략 가설의 일반화 실패와 비용 취약성이다.
```

따라서 기록상 결론은 다음과 같다.

```text
T285_R3_CORE_SHORT_ONLY_B2는 특정 bearish owner window에서 작동한 short-only failed-rally 전략이었지만,
repaired 2026-04-20-forward locked OOS/WFO 검증에서는 비용 이후 기대값이 음수였고,
독립 weekly consistency와 pre-owner robustness를 충족하지 못했다.
이 전략은 research-only rejected 상태로 유지한다.
```
