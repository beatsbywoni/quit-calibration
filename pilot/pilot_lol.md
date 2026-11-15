# LoL pilot summary

ranked-solo games used: 2811; surrendered: 1028 (0.366)

## Flags x duration (all files; check what gameEndedInEarlySurrender means)

| surrender | earlySurrender | duration | n |
|---|---|---|---|
| False | False | 15-20m | 12 |
| False | False | 20m+ | 1769 |
| False | False | 5-15m | 2 |
| False | True | dur<5m | 92 |
| True | False | 15-20m | 350 |
| True | False | 20m+ | 653 |
| True | False | 5-15m | 25 |
| True | False | dur<5m | 9 |

## Timeline event types seen (is there any surrender-vote event?)

```
{
 "ITEM_PURCHASED": 642071,
 "ITEM_DESTROYED": 608127,
 "WARD_PLACED": 572221,
 "SKILL_LEVEL_UP": 415144,
 "LEVEL_UP": 382673,
 "CHAMPION_KILL": 171581,
 "TURRET_PLATE_DESTROYED": 143166,
 "WARD_KILL": 111242,
 "BUILDING_KILL": 34824,
 "ITEM_UNDO": 25968,
 "ITEM_SOLD": 25200,
 "ELITE_MONSTER_KILL": 24064,
 "CHAMPION_SPECIAL_KILL": 23532,
 "DRAGON_SOUL_GIVEN": 3348,
 "OBJECTIVE_BOUNTY_PRESTART": 2984,
 "PAUSE_END": 2811,
 "GAME_END": 2811,
 "FEAT_UPDATE": 1443,
 "OBJECTIVE_BOUNTY_FINISH": 1115,
 "CHAMPION_TRANSFORM": 152
}
```

## Model B (non-surrender games only): P(win) of surrendering team at the last frame

n = 1028; mean = 0.0796; median = 0.0439
share >= 0.05: 0.4621; >= 0.10: 0.2471; >= 0.20: 0.0914; >= 0.30: 0.0496

| group | n | mean p | share>=0.10 | share>=0.20 |
|---|---|---|---|---|
| dur 20-25m | 258 | 0.051 | 0.120 | 0.027 |
| dur 25m+ | 395 | 0.109 | 0.397 | 0.154 |
| dur <20m | 375 | 0.068 | 0.176 | 0.069 |
| tier DIAMOND | 204 | 0.079 | 0.245 | 0.103 |
| tier EMERALD | 179 | 0.079 | 0.257 | 0.089 |
| tier GOLD | 171 | 0.078 | 0.257 | 0.076 |
| tier IRON | 154 | 0.082 | 0.234 | 0.084 |
| tier PLATINUM | 158 | 0.084 | 0.234 | 0.114 |
| tier SILVER | 162 | 0.076 | 0.253 | 0.080 |

Held-out calibration (non-surrender games, team 100):

| predicted | n | observed |
|---|---|---|
| 0.0-0.1 | 693 | 0.065 |
| 0.1-0.2 | 778 | 0.184 |
| 0.2-0.3 | 875 | 0.246 |
| 0.3-0.4 | 1135 | 0.337 |
| 0.4-0.5 | 1192 | 0.431 |
| 0.5-0.6 | 1198 | 0.526 |
| 0.6-0.7 | 1139 | 0.630 |
| 0.7-0.8 | 1078 | 0.694 |
| 0.8-0.9 | 886 | 0.819 |
| 0.9-1.0 | 1039 | 0.966 |

## Model A (all games): P(win) of surrendering team at the last frame

n = 1028; mean = 0.0691; median = 0.0346
share >= 0.05: 0.3794; >= 0.10: 0.2004; >= 0.20: 0.0788; >= 0.30: 0.0447

| group | n | mean p | share>=0.10 | share>=0.20 |
|---|---|---|---|---|
| dur 20-25m | 258 | 0.042 | 0.085 | 0.019 |
| dur 25m+ | 395 | 0.098 | 0.337 | 0.137 |
| dur <20m | 375 | 0.057 | 0.136 | 0.059 |
| tier DIAMOND | 204 | 0.069 | 0.201 | 0.083 |
| tier EMERALD | 179 | 0.068 | 0.229 | 0.061 |
| tier GOLD | 171 | 0.067 | 0.193 | 0.070 |
| tier IRON | 154 | 0.071 | 0.182 | 0.078 |
| tier PLATINUM | 158 | 0.074 | 0.196 | 0.108 |
| tier SILVER | 162 | 0.066 | 0.198 | 0.074 |
