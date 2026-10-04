# Resultados de las consultas

## Q1 — Tasa de retraso por clima (solo express y same_day)

| weather | deliveries | delayed | delay_rate_pct |
|---|---|---|---|
| stormy | 2081 | 1717 | 82.5 |
| rainy | 2062 | 1555 | 75.4 |
| foggy | 2068 | 1278 | 61.8 |
| clear | 2122 | 719 | 33.9 |
| hot | 2092 | 707 | 33.8 |
| cold | 2087 | 666 | 31.9 |

Chi-cuadrado entre climas: p < 0.001

## Q2 — Tasa de retraso por transportista (express/same_day con lluvia o tormenta)

| carrier | deliveries | delayed | delay_rate_pct |
|---|---|---|---|
| ekart | 460 | 378 | 82.2 |
| shadowfax | 440 | 354 | 80.5 |
| delhivery | 442 | 354 | 80.1 |
| ecom_express | 451 | 358 | 79.4 |
| blue_dart | 466 | 368 | 79.0 |
| xpressbees | 502 | 394 | 78.5 |
| fedex | 463 | 363 | 78.4 |
| dhl | 461 | 354 | 76.8 |
| amazon_logistics | 458 | 349 | 76.2 |

Chi-cuadrado entre transportistas: p = 0.494


Verificación SQL == pandas: Q1 True, Q2 True
