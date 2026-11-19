# Preregistration 2 (v1.0): the strong quit more, not better

**Project.** Quitting in online chess (repository beatsbywoni/quit-calibration; first preregistration v1.0, doi:10.5281/zenodo.24247036).
**Author.** Hongwon Jeong, Hanyang University ERICA (ORCID 0009-0003-7908-7478). Sole author.
**Status.** Written 2026-11-18, finalised and registered 2026-11-19 as release `v2.0-prereg2` of the repository (archived on Zenodo as a new version). At registration the July and August 2026 Lichess databases had not been downloaded by the author.

## 1. Why a second preregistration

The first preregistration concerned the expected score given up at resignation (hypotheses H1 to H7) and has been carried out on September and June 2026. After those results were seen, exploratory move-level analyses were run on the same two months, guided by two rounds of simulated review. Their history, including two central claims that were formulated and then refuted by my own analyses, is in the deviations log (`prereg/clarifications_and_deviations.md`, D4 to D6) and is summarised here so that the reader knows what was tried:

1. Draft claim 1 ("players of all ratings resign at the same evaluation, so they ignore the opponent") was based on evaluations at resignation only. A hazard analysis of all positions at risk showed that stronger players resign far more often in the same board state, and that resignation responds strongly to the opponent's clock. Claim withdrawn.
2. Draft claim 2 ("stronger players resign more only where the value of playing on is low; their resignations are better aimed") rested on a continuation value that counted later resignations as losses, which mechanically lowers the value of positions held by players who resign often. With a value that excludes games the player ended by resigning, the rating gradient in the hazard is a level shift: about the same ratio at every value. Claim withdrawn.

What survived on both months is stated below as hypotheses K1 to K7. They are exploratory findings from September and June 2026 and are to be tested on two months that have not been downloaded: **July 2026 and August 2026**.

## 2. Data

- Lichess open database, rated standard games, July 2026 and August 2026, same exclusions as in preregistration 1 (ultrabullet and correspondence, fewer than 10 plies, terminations other than "Normal" and "Time forfeit", BOT accounts, missing ratings). Games without server evaluation are excluded from the move-level analysis.
- Extraction: `code/chess_stage_a.py` (now also records whether the Event tag names a tournament, swiss, or arena) and `code/chess_hazard.py` (extraction step). A 10% sample of evaluated games is drawn by a hash of the game identifier (crc32 of the identifier plus "h", modulo 10 equal to 0).
- Risk set: every position at ply 10 or later in which the player's server evaluation is -3.00 pawns or worse, or a forced mate against the player. Event: the player resigns in that position (it is the last evaluated position of a game that ended by that player's resignation).
- Time controls tested: bullet, blitz, rapid. Classical is reported but not tested, because the continuation-value model was poorly calibrated there in both exploratory months (gaps of 0.10 to 0.20).
- Rating bands of the player: under 1200, 1200 to 1599, 1600 to 1999, 2000 and above.

## 3. Measures (all computed by `chess_hazard.py --rot`, frozen at registration)

Frozen files (SHA-256): `code/chess_hazard.py` 4886dc9bd01391002b67afc8089d0952d74b6baa059ade8b3e773af41e6423f7; `code/chess_stage_a.py` 988277ceba91ad98ac87174b3bae52c570067ff238745657d02d0b938154ec51. The decision rules K1 to K6 are computed by the script (`decisions`), K7 from the stage A cell counts (`K7_monotone`).

- **Continuation value V_U**: gradient-boosted regression (150 iterations, learning rate 0.1, 63 leaves, at least 200 per leaf, L2 = 1, random_state 29) of the final score on the state (evaluation, mate flag and distance, own rating, rating difference, both clocks in seconds and as shares, increment, ply, side to move, material of both sides, change in evaluation over two plies, positions already spent in the losing state), trained on at-risk positions of games that the player did NOT end by resigning, cross-fitted in 5 folds by game.
- **Hazard profile**: binomial logit on cells (rating band x 50 quantile bins of V_U), h = Lambda(a_band + s_band * ln(V_U + 0.02)).
- **Inference**: 99% intervals from a bootstrap over 40 hash groups of players, 500 replications, conditional on the fitted V_U.
- **Calibration gate**: within each time control and month, if the gap between mean predicted and realised score of V_U exceeds 0.03 in any of 10 quantile bins within any rating band (positions of games not ended by the player's resignation), V_U is recalibrated by isotonic regression within band (fitted on those same positions), results are reported both ways, and the recalibrated version decides for that time control and month. The rule is coded in the script (output field `calibration_gate`). In the exploratory months the largest gaps were 0.022 (bullet), 0.011 (blitz), and 0.016 (rapid), so the gate was not triggered in any tested time control; it was triggered in classical (0.13 to 0.20).

## 4. Hypotheses

A hypothesis counts as confirmed only if it holds in both months and in every time control listed for it.

- **K1 (the strong quit more at every value).** Bullet, blitz, rapid. The ratio of fitted hazards, 2000 and above versus under 1200, has a 99% lower bound above 1.3 at V_U = 0.05 and at V_U = 0.40.
  Exploratory basis: ratios of 1.8 to 2.5 at both values in September and June; smallest 99% lower bound 1.72.
- **K2 (not better aimed: no steeper profile).** Bullet, blitz, rapid. The slope difference s(2000 and above) minus s(under 1200) has a 99% lower bound above -0.10. (A more negative slope for strong players would mean a hazard that reacts more sharply to value.)
  Exploratory basis: differences between +0.001 and +0.066; 99% lower bounds between -0.031 and +0.025.
- **K3 (everyone discriminates).** Bullet, blitz, rapid. In every rating band, the within-player Mantel-Haenszel odds ratio of resigning in the lowest fifth of V_U versus the upper half has a 99% lower bound above 5.
  Exploratory basis: 12 to 30 in every band; smallest 99% lower bound 9.6.
- **K4 (no gradient in targeting).** Blitz and rapid only. The exposure-standardised share of resignations that fall in the upper half of V_U differs between the lowest and the highest band by less than 0.05 in absolute value (99% interval inside +/-0.05). Bullet is reported without a hypothesis: there the lowest band had a higher share in both exploratory months (0.21 against 0.14; 0.19 against 0.13).
  Exploratory basis: differences of about 0.00 to +0.02 in blitz and rapid; all 99% bounds inside [-0.013, +0.026].
- **K5 (extensive margin).** Bullet, blitz, rapid. Among players with at least 100 at-risk positions, the share who never resign is higher in the lowest band than in the highest by more than 0.15 (99% lower bound).
  Exploratory basis: differences of 0.31 to 0.33; smallest 99% lower bound 0.29.
- **K6 (the opponent's clock).** Bullet, blitz, rapid. In a linear probability model with board-state cells, player fixed effects, and controls (rating difference, own clock, change in evaluation, time in the losing state, ply), halving the opponent's remaining time lowers the hazard by more than 15% of its mean (99% upper bound below -15%).
  Exploratory basis: -50%, -36%, -27% in September; -51%, -36%, -27% in June; the 99% upper bound closest to the threshold is -26% (rapid).
- **K7 (game level).** All four time controls, all games (stage A cell counts, no sampling). The share of decisive games that end by resignation increases monotonically across the four rating bands (band of the mean rating of the two players).
  Exploratory basis: blitz 0.42, 0.50, 0.53, 0.57; classical 0.44, 0.54, 0.69, 0.75 in September, the same to two decimals in June. This is the opposite of the direction reported by Purohit and Srivastava (2026) for classical games of 2020.

## 5. Robustness reported with the tests (not decisive)

None of the following enters the decisions. Some of them would not meet the thresholds above in the exploratory months, and this is stated here so that it cannot be presented later as a surprise: with V_L, the slope difference in blitz had a 99% lower bound of -0.126 in September (strong players look steeper under the value that is mechanically lowered for frequent resigners) and the hazard ratio at V = 0.40 had a lower bound of 1.16; in bullet, after excluding berserk games and large rating changes, the lower bound of the slope difference was -0.109 in June. In the other direction, without forced mates the slope of the strongest band was flatter than that of the weakest by 0.14 to 0.19 in blitz and rapid.

The same quantities (i) with V_L, the value that counts later resignations as losses, (ii) excluding tournament, swiss, and arena games, (iii) restricted to evaluations of -4.00 or worse, (iv) excluding games with a halved starting clock and rating changes above 20 points, (v) hazard profiles with a control for the expected number of remaining plies, without forced mates, and for players rated 1200 and above only, (vi) a common floor in the logit, (vii) AUC by band, (viii) classical.

The scale of server evaluations differed between June and September 2026 by about 20%. The risk-set threshold is nominal (-3.00 in each month's units). Results at -4.00 are reported to show sensitivity; no rescaling is applied.

## 6. What would count against the claim

"Stronger players quit more, not better" is refuted if K1 fails (no level difference) or if K2 fails (strong players' profile is steeper by more than 0.10). K3 to K7 qualify the claim and are reported whatever the outcome.

## 7. Not preregistered

Within-player changes across months (does a player's hazard profile move when her rating rises?) will be examined with the four months available and reported as exploratory. Interpretation of the level shift (value of time, disutility of lost positions, norms, composition) is not tested here.

## 8. Open materials, ethics, AI use

The frozen code and this document are in the repository at registration; manifests and aggregate outputs for all four months follow with the submission. Secondary analysis of public data; no ethics review was sought. Generative AI (Claude, Anthropic) was used for code, analysis support, simulated reviews of drafts, and drafting; the author verified outputs and takes responsibility. A usage log is in the repository.
