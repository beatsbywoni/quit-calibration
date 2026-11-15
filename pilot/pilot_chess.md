# Chess pilot summary

games parsed: 3048388 (2026.10.01 00:00:25 .. 2026.10.02 00:16:52); eval share: 0.1043

## Composition (eval vs no eval)

| eval | speed | class | n | mean Elo | mean plies |
|---|---|---|---|---|---|
| False | blitz | draw | 55846 | 1682 | 110.6 |
| False | blitz | mate | 304710 | 1541 | 70.3 |
| False | blitz | other | 1947 | 1602 | 1.9 |
| False | blitz | resign | 609609 | 1629 | 58.7 |
| False | blitz | time | 292780 | 1613 | 78.9 |
| False | bullet | draw | 29728 | 1924 | 102.3 |
| False | bullet | mate | 224780 | 1784 | 62.7 |
| False | bullet | other | 778 | 1736 | 1.9 |
| False | bullet | resign | 235204 | 1824 | 50.4 |
| False | bullet | time | 525066 | 1735 | 70.1 |
| False | classical | draw | 753 | 1645 | 102.9 |
| False | classical | mate | 3737 | 1489 | 72.3 |
| False | classical | other | 12 | 1476 | 11.1 |
| False | classical | resign | 6408 | 1547 | 56.2 |
| False | classical | time | 1107 | 1485 | 48.4 |
| False | rapid | draw | 20344 | 1503 | 108.7 |
| False | rapid | mate | 116993 | 1377 | 69.0 |
| False | rapid | other | 810 | 1382 | 1.9 |
| False | rapid | resign | 228571 | 1504 | 57.8 |
| False | rapid | time | 45756 | 1448 | 66.6 |
| False | ultrabullet | draw | 403 | 1889 | 90.9 |
| False | ultrabullet | mate | 4656 | 1798 | 47.2 |
| False | ultrabullet | other | 112 | 1487 | 1.0 |
| False | ultrabullet | resign | 708 | 1958 | 41.9 |
| False | ultrabullet | time | 19582 | 1700 | 58.6 |
| True | blitz | draw | 5522 | 1839 | 106.6 |
| True | blitz | mate | 39822 | 1525 | 67.6 |
| True | blitz | other | 4 | 1796 | 33.2 |
| True | blitz | resign | 69747 | 1698 | 61.6 |
| True | blitz | time | 30955 | 1653 | 76.5 |
| True | bullet | draw | 1141 | 1848 | 97.1 |
| True | bullet | mate | 17410 | 1679 | 59.5 |
| True | bullet | other | 2 | 1439 | 46.5 |
| True | bullet | resign | 14203 | 1789 | 54.1 |
| True | bullet | time | 32067 | 1606 | 66.0 |
| True | classical | draw | 264 | 1754 | 103.8 |
| True | classical | mate | 1810 | 1525 | 69.6 |
| True | classical | other | 3 | 1526 | 32.0 |
| True | classical | resign | 3195 | 1646 | 63.5 |
| True | classical | time | 332 | 1579 | 65.0 |
| True | rapid | draw | 3883 | 1626 | 107.2 |
| True | rapid | mate | 32572 | 1390 | 67.9 |
| True | rapid | other | 16 | 1345 | 34.7 |
| True | rapid | resign | 53371 | 1564 | 61.9 |
| True | rapid | time | 9262 | 1519 | 73.5 |
| True | ultrabullet | draw | 12 | 1727 | 79.7 |
| True | ultrabullet | mate | 391 | 1809 | 54.2 |
| True | ultrabullet | resign | 22 | 1863 | 55.3 |
| True | ultrabullet | time | 1982 | 1625 | 58.0 |

## Resignations, overall

| group | n | median_cp_loser | share_mate_against | share_cp_ge_-300 | share_cp_ge_-100 | mean_lichess_win | ES_played_on>=0.05 | ES_played_on>=0.10 | ES_played_on>=0.20 | ES_all>=0.10 | ES_all>=0.20 | n_with_curve |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 140386 | -806 | 0.288 | 0.042 | 0.027 | 0.060 | 0.993 | 0.761 | 0.420 | 0.583 | 0.248 | 140321 |

## by speed

| group | n | median_cp_loser | share_mate_against | share_cp_ge_-300 | share_cp_ge_-100 | mean_lichess_win | ES_played_on>=0.05 | ES_played_on>=0.10 | ES_played_on>=0.20 | ES_all>=0.10 | ES_all>=0.20 | n_with_curve |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| blitz | 69684 | -797 | 0.281 | 0.041 | 0.026 | 0.060 | 1.000 | 0.821 | 0.467 | 0.636 | 0.240 | 69684 |
| bullet | 14190 | -827 | 0.274 | 0.040 | 0.028 | 0.059 | 1.000 | 1.000 | 0.713 | 1.000 | 0.566 | 14190 |
| classical | 3190 | -802 | 0.297 | 0.050 | 0.034 | 0.063 | 0.708 | 0.444 | 0.183 | 0.316 | 0.114 | 3127 |
| rapid | 53300 | -811 | 0.300 | 0.044 | 0.029 | 0.060 | 1.000 | 0.638 | 0.294 | 0.419 | 0.181 | 53300 |
| ultrabullet | 22 | -883 | 0.727 | 0.000 | 0.000 | 0.006 | 1.000 | 1.000 | 0.750 | 1.000 | 0.700 | 20 |

## by rating band

| group | n | median_cp_loser | share_mate_against | share_cp_ge_-300 | share_cp_ge_-100 | mean_lichess_win | ES_played_on>=0.05 | ES_played_on>=0.10 | ES_played_on>=0.20 | ES_all>=0.10 | ES_all>=0.20 | n_with_curve |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1200-1599 | 43508 | -822 | 0.296 | 0.046 | 0.031 | 0.060 | 0.999 | 0.672 | 0.411 | 0.571 | 0.248 | 43503 |
| 1600-1999 | 48818 | -801 | 0.286 | 0.036 | 0.022 | 0.057 | 0.988 | 0.725 | 0.398 | 0.544 | 0.234 | 48796 |
| 2000+ | 28504 | -768 | 0.268 | 0.033 | 0.016 | 0.059 | 0.993 | 0.916 | 0.426 | 0.608 | 0.180 | 28481 |
| <1200 | 19556 | -842 | 0.302 | 0.065 | 0.048 | 0.070 | 0.996 | 0.825 | 0.487 | 0.671 | 0.379 | 19541 |

## by previous game (60 min)

| group | n | median_cp_loser | share_mate_against | share_cp_ge_-300 | share_cp_ge_-100 | mean_lichess_win | ES_played_on>=0.05 | ES_played_on>=0.10 | ES_played_on>=0.20 | ES_all>=0.10 | ES_all>=0.20 | n_with_curve |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 44052 | -803 | 0.282 | 0.046 | 0.030 | 0.062 | 0.989 | 0.736 | 0.406 | 0.558 | 0.244 | 44020 |
| prevloss | 46130 | -802 | 0.279 | 0.046 | 0.029 | 0.062 | 0.996 | 0.780 | 0.443 | 0.611 | 0.266 | 46117 |
| prevnonloss | 50204 | -812 | 0.302 | 0.037 | 0.023 | 0.056 | 0.995 | 0.766 | 0.411 | 0.580 | 0.235 | 50184 |

## by loser clock

| group | n | median_cp_loser | share_mate_against | share_cp_ge_-300 | share_cp_ge_-100 | mean_lichess_win | ES_played_on>=0.05 | ES_played_on>=0.10 | ES_played_on>=0.20 | ES_all>=0.10 | ES_all>=0.20 | n_with_curve |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <10s | 6313 | -821 | 0.387 | 0.038 | 0.027 | 0.051 | 0.999 | 0.851 | 0.425 | 0.653 | 0.254 | 6311 |
| 10-29s | 15453 | -831 | 0.356 | 0.032 | 0.024 | 0.050 | 0.999 | 0.835 | 0.454 | 0.665 | 0.278 | 15453 |
| 30s+ | 118406 | -803 | 0.274 | 0.044 | 0.028 | 0.062 | 0.992 | 0.747 | 0.415 | 0.569 | 0.243 | 118343 |

## P(resign | loss), all games

```
{
 "blitz|none": {
  "n_loss": 349871,
  "p_resign": 0.5089
 },
 "blitz|prevloss": {
  "n_loss": 464449,
  "p_resign": 0.5139
 },
 "blitz|prevnonloss": {
  "n_loss": 520790,
  "p_resign": 0.4905
 },
 "bullet|none": {
  "n_loss": 180884,
  "p_resign": 0.2487
 },
 "bullet|prevloss": {
  "n_loss": 412923,
  "p_resign": 0.2437
 },
 "bullet|prevnonloss": {
  "n_loss": 445254,
  "p_resign": 0.2221
 },
 "classical|none": {
  "n_loss": 7515,
  "p_resign": 0.5695
 },
 "classical|prevloss": {
  "n_loss": 4483,
  "p_resign": 0.5844
 },
 "classical|prevnonloss": {
  "n_loss": 4127,
  "p_resign": 0.5893
 },
 "rapid|none": {
  "n_loss": 171779,
  "p_resign": 0.5689
 },
 "rapid|prevloss": {
  "n_loss": 148074,
  "p_resign": 0.5969
 },
 "rapid|prevnonloss": {
  "n_loss": 159019,
  "p_resign": 0.5755
 },
 "ultrabullet|none": {
  "n_loss": 1368,
  "p_resign": 0.0132
 },
 "ultrabullet|prevloss": {
  "n_loss": 13960,
  "p_resign": 0.033
 },
 "ultrabullet|prevnonloss": {
  "n_loss": 11739,
  "p_resign": 0.0175
 }
}
```

## Trailing plies at loser eval <= -7.00 before the end

```
{
 "blitz|mate": {
  "n": 39809,
  "share_trail>=10plies": 0.4247,
  "share_trail>=20plies": 0.262,
  "median_trail": 7
 },
 "blitz|resign": {
  "n": 69684,
  "share_trail>=10plies": 0.274,
  "share_trail>=20plies": 0.1127,
  "median_trail": 4
 },
 "blitz|time": {
  "n": 30934,
  "share_trail>=10plies": 0.1764,
  "share_trail>=20plies": 0.0927,
  "median_trail": 0
 },
 "bullet|mate": {
  "n": 17406,
  "share_trail>=10plies": 0.4377,
  "share_trail>=20plies": 0.2619,
  "median_trail": 7
 },
 "bullet|resign": {
  "n": 14190,
  "share_trail>=10plies": 0.2807,
  "share_trail>=20plies": 0.1211,
  "median_trail": 4
 },
 "bullet|time": {
  "n": 32059,
  "share_trail>=10plies": 0.1808,
  "share_trail>=20plies": 0.0999,
  "median_trail": 0
 },
 "classical|mate": {
  "n": 1807,
  "share_trail>=10plies": 0.5091,
  "share_trail>=20plies": 0.342,
  "median_trail": 11
 },
 "classical|resign": {
  "n": 3190,
  "share_trail>=10plies": 0.3351,
  "share_trail>=20plies": 0.1495,
  "median_trail": 4
 },
 "classical|time": {
  "n": 331,
  "share_trail>=10plies": 0.2477,
  "share_trail>=20plies": 0.145,
  "median_trail": 0
 },
 "rapid|mate": {
  "n": 32534,
  "share_trail>=10plies": 0.4666,
  "share_trail>=20plies": 0.303,
  "median_trail": 9
 },
 "rapid|resign": {
  "n": 53300,
  "share_trail>=10plies": 0.3138,
  "share_trail>=20plies": 0.1406,
  "median_trail": 4
 },
 "rapid|time": {
  "n": 9242,
  "share_trail>=10plies": 0.2219,
  "share_trail>=20plies": 0.1162,
  "median_trail": 0
 },
 "ultrabullet|mate": {
  "n": 390,
  "share_trail>=10plies": 0.5256,
  "share_trail>=20plies": 0.2949,
  "median_trail": 11
 },
 "ultrabullet|resign": {
  "n": 22,
  "share_trail>=10plies": 0.5455,
  "share_trail>=20plies": 0.3636,
  "median_trail": 10
 },
 "ultrabullet|time": {
  "n": 1982,
  "share_trail>=10plies": 0.2447,
  "share_trail>=20plies": 0.1483,
  "median_trail": 0
 }
}
```
