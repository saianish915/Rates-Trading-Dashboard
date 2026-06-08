# Rates Trading Dashboard

## Hypothesis

Rising long-duration US Treasury yields, driven by persistent inflation, elevated oil prices, and fiscal deterioration, create a potential entry point for bond investors. However, the same forces driving yields higher may continue to push them further, making timing critical.

This project tests whether a rules-based signal system using publicly available macroeconomic indicators can identify favorable entry points for long-duration Treasury bonds, and whether such a system can outperform a simple buy and hold strategy.

---

## Background

In May 2026, the 30-year Treasury yield approached 5.18%, levels not seen since 2007, driven by four structural forces:

- The Iran war pushing oil prices above $100, adding to inflationary pressure
- US fiscal deterioration and rising budget deficits increasing bond supply
- Central bank paralysis as the Fed could neither cut nor raise rates decisively
- A resilient US economy reducing urgency for monetary easing

Investors faced a classic dilemma: yields looked historically attractive, but the same forces driving them higher showed no signs of reversing. Barclays warned yields could breach 5.5%. BlackRock recommended reducing bond exposure entirely. Goldman Sachs described the situation as an "uneasy introduction of value."

The question this project attempts to answer: can a systematic, indicator-based approach navigate this environment better than simply buying and holding?

---

## Methodology

### Indicator Selection

Five macroeconomic indicators were selected based on their theoretical relationship to bond prices:

| Indicator | Rationale |
|-----------|-----------|
| 30yr Treasury Yield | Primary asset being traded. High yields indicate attractive entry but also ongoing selling pressure |
| CPI Inflation | Determines Fed policy direction. Cooling inflation is the primary catalyst for rate cuts and bond rallies |
| Non Farm Payrolls | Weak jobs data forces the Fed toward cuts, reducing yields and lifting bond prices |
| Brent Crude Oil | Directly tied to the Iran war. Oil drives inflation expectations which drive yields |
| TLT ETF Price | Measures current bond market momentum and investor sentiment toward duration |

### Scoring System

Each indicator was scored from -2 to +2 based on predefined thresholds:

30yr Yield:
  >= 5.0%          → +1  (historically attractive)
  >= 5.5%          → +1  (curve steepening bonus)
  < 4.5%           → -1

CPI:
  Cooling < 3.0%   → +2
  Cooling > 3.0%   → +1
  Rising > 4.0%    → -2
  Rising < 4.0%    → -1

NFP Jobs:
  < 100k           → +2
  < 150k           → +1
  < 200k           →  0
  < 250k           → -1
  > 250k           → -2

Brent Oil:
  < $60            → +2
  < $70            → +1
  < $85            →  0
  < $100           → -1
  > $100           → -2

TLT Price:
  > $95            → +2
  > $90            → +1
  > $85            →  0
  < $85            → -1

### Signal Generation

Total Score >= 5   → STRONG BUY
Total Score >= 2   → BUY
Total Score >= -1  → NEUTRAL
Total Score >= -4  → WAIT
Total Score < -4   → STRONG AVOID

Positions were entered on BUY or STRONG BUY signals and exited when the signal deteriorated to NEUTRAL, WAIT, or STRONG AVOID.

### Data Sources

All data was pulled automatically via API:

| Data | Source | Frequency |
|------|--------|-----------|
| Treasury Yields | FRED API (DGS30, DGS10) | Daily |
| CPI Inflation | FRED API (CPIAUCSL) | Monthly |
| Non Farm Payrolls | FRED API (PAYEMS) | Monthly |
| Oil Prices | Yahoo Finance (BZ=F, CL=F) | Daily |
| TLT Price | Yahoo Finance (TLT) | Daily |

Signal rebalancing was done monthly, consistent with the frequency of the slowest updating indicators (CPI and NFP).

---

## Experiments

### Experiment 1: Base Signal Strategy (V1)

The simplest implementation. Enter 100% when signal says BUY or STRONG BUY. Exit when signal deteriorates. No additional filters.

Result:

Strategy Return:  +4.1%
Buy & Hold:       -34.0%
Excess Return:    +38.1%
Sharpe Ratio:     0.15
Max Drawdown:     -9.2%
Win Rate:         50%
Total Trades:     8

The strategy significantly outperformed buy and hold by avoiding the 2022 Federal Reserve rate hiking cycle, during which TLT lost over 34% of its value.

---

### Experiment 2: Enhanced Strategy with Three Modifications (V2)

Three improvements were added to attempt to increase the Sharpe ratio and win rate:

Modification 1: Position Sizing
Scale position size by signal strength rather than going all in:
STRONG BUY → 100% invested
BUY        → 75% invested

Modification 2: Stop Loss
Automatically exit any trade that loses more than 3% to limit downside on losing trades.

Modification 3: Trend Filter
Only enter positions when TLT is trading above its 3-month moving average, avoiding entries into falling markets.

Result:

Strategy Return:  -7.2%
Buy & Hold:       -34.0%
Excess Return:    +26.8%
Sharpe Ratio:     -0.44
Max Drawdown:     -8.4%
Win Rate:         22%
Total Trades:     9

All three modifications made performance significantly worse. The win rate dropped from 50% to 22% and the strategy produced a negative return.

---

### Experiment 3: Adjusted Parameters (V3)

After analyzing why V2 failed, the modifications were adjusted:
- Trend filter removed entirely
- Position sizing returned to 100%
- Stop loss widened from -3% to -7% to give trades room to breathe on a monthly timeframe

Result:

Strategy Return:  +4.1%
Buy & Hold:       -34.0%
Excess Return:    +38.1%
Sharpe Ratio:     0.15
Max Drawdown:     -9.2%
Win Rate:         50%
Total Trades:     8

V3 produced identical results to V1, confirming that the original modifications added no value.

---

## Results

| Metric | V1 (Base) | V2 (Enhanced) | V3 (Adjusted) |
|--------|-----------|---------------|---------------|
| Strategy Return | +4.1% | -7.2% | +4.1% |
| Buy & Hold Return | -34.0% | -34.0% | -34.0% |
| Excess Return | +38.1% | +26.8% | +38.1% |
| Sharpe Ratio | 0.15 | -0.44 | 0.15 |
| Max Drawdown | -9.2% | -8.4% | -9.2% |
| Win Rate | 50% | 22% | 50% |
| Total Trades | 8 | 9 | 8 |

The base strategy was the best performing version across all metrics.

---

## Backtest Limitations and Statistical Credibility

The 38% excess return over 2020-2026 requires important context:

1. The window is historically anomalous
The backtest period contains three back-to-back
extreme regimes: the COVID crash, the zero-rate era,
and the most aggressive Fed tightening cycle in 40 years.
The excess return is driven primarily by avoiding bonds
during the 2022 tightening cycle when buy and hold lost 34%.
Whether this generalizes to future cycles is untested.

2. Only 8 trades over 6 years
With only 8 trades the Sharpe ratio of 0.15 and win rate
of 50% are not statistically significant. A minimum of
30 trades is typically required for meaningful strategy
evaluation. The signal is too infrequent to draw strong
conclusions from win rate alone.

3. Single regime test
The strategy has only been tested through one full
tightening cycle. A more robust test would require
data from the 1970s and 1980s tightening cycles.

4. No transaction costs modeled
Real bond trading involves bid-ask spreads and
duration risk that would reduce the excess return
in practice.

5. Walk forward test would strengthen credibility
Training on 2020-2022 and testing on 2023-2026
separately would provide a cleaner out-of-sample
validation within the available data.

---

## Conclusion and Takeaways

1. The hypothesis was partially supported

A rules-based macro signal system can outperform buy and hold significantly over a period that includes a major rate hiking cycle. The 38% excess return over six years demonstrates that systematic indicator-based timing adds value versus passive exposure.

2. Complexity destroyed alpha

The most important finding was that adding sophistication to the strategy consistently made it worse. The trend filter blocked entries during the precise windows when the signal was correct. The tight stop loss caused premature exits before positions recovered. This reflects a well-documented phenomenon in macro trading: over-fitting and over-engineering reduces robustness.

3. Oil is the key variable in the current environment

Of the five indicators, oil had the most asymmetric impact on the current signal. With Brent above $100 driven by the Iran war, the oil score alone was enough to suppress a BUY signal even when other indicators were favorable. A resolution to the Middle East conflict would likely flip the overall signal from WAIT to BUY within a single monthly rebalancing cycle.

4. The Sharpe ratio remains low

A Sharpe ratio of 0.15 indicates the strategy is not yet risk-adjusted efficient. With only 8 trades over 6 years, there is insufficient trade frequency to build a smooth return profile. Future work would explore increasing signal sensitivity or applying the framework to additional fixed income instruments to increase trade frequency.

5. Limitations

- Backtest covers only one full rate hiking cycle (2022-2023)
- Monthly rebalancing misses intra-month opportunities
- Oil scoring does not distinguish between supply and demand driven moves
- No transaction costs or slippage modeled

---

## Tech Stack

Python          Signal engine and data pipeline
FRED API        Treasury yields, CPI, NFP data
yfinance        Oil prices and TLT ETF data
Plotly          Interactive dashboard charts
smtplib         Automated email alerts
GitHub Actions  Cloud scheduling (8am EST daily)
Google Colab    Development and backtesting

