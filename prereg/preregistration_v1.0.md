# Preregistration v1.0

**Working title.** Quitting winnable contests? The calibration of resignation in online chess and surrender in League of Legends

**Author.** Hongwon Jeong, Center for Creative Convergence Education, Hanyang University ERICA (ORCID 0009-0003-7908-7478). Sole author.

**Status.** Registered on 2026-11-15 as release `v1.0-prereg` of the public GitHub repository `quit-calibration`, archived on Zenodo. Written after a pilot and before any confirmatory data were downloaded. All design choices were fixed by the author on 2026-11-15.

## 1. What has already been seen (disclosure)

A pilot was run on 2026-11-15 and its results informed the hypotheses below. The pilot data are excluded from all confirmatory analyses.

- Chess: the first ~1 GB of the Lichess October 2026 dump (3,048,388 games played 2026-10-01 to early 2026-10-02; 140,386 inferred resignations with server evaluations). Crude evaluation-to-outcome curves (100 cp bins by speed and rating band) gave a mean expected score at resignation of 0.10 (classical) to 0.24 (bullet) on the lower-bound curve, against about 0.06 from the Lichess engine-based formula. The inferred termination class matched the Lichess API status in 1000/1000 sampled resignations.
- League of Legends: 2,811 KR ranked solo games from 150 seed accounts. 36.6% ended in surrender. A logistic state model gave a mean win probability of the surrendering team of 0.069 (model on all games) to 0.080 (model on games played to the end), with no visible gradient across tiers.
- No confirmatory month of chess data and no confirmatory LoL sample has been downloaded or inspected.

## 2. Research questions

- RQ1. How much chance of not losing do players give up at the moment they resign (chess) or surrender (LoL)?
- RQ2. How does that quantity vary with skill, game speed, and remaining time?
- RQ3. Do players give up more readily, and at better odds, right after a loss?
- RQ4. How does premature quitting compare with the opposite error, playing on in hopeless games?
- RQ5. Does the individual decision (chess) differ from the team vote (LoL) in its skill gradient?

The term "mistaken" is avoided. Resigning saves time, so giving up a small chance can be reasonable. The estimand is the forgone expected score, not an error rate.

## 3. Study 1: resignation in online chess

### 3.1 Data
- Source: Lichess open database (CC0), rated standard games. Confirmatory sample: all games of September 2026. Replication sample: all games of June 2026. October 2026 is excluded (pilot).
- Server evaluations (`[%eval]`) and clocks (`[%clk]`) as recorded in the dump.
- Exclusions: speed classes ultrabullet and correspondence; fewer than 10 plies; Termination "Abandoned", "Rules infraction", or "Unterminated"; either player titled BOT; missing rating; for the main analysis, games without server evaluation.

### 3.2 Classification of game endings
- Resignation: Termination "Normal", decisive result, last SAN without "#".
- Checkmate: Termination "Normal", decisive result, last SAN with "#".
- Time forfeit: Termination "Time forfeit", decisive result.
- Draw: result 1/2-1/2.
- Validation: a fresh random sample of 1,000 games per class from the confirmatory month is compared with the Lichess API `status` field. If precision of "resignation" is below 0.99, the rule is revised and the revision reported as a deviation.

### 3.3 Primary outcome: forgone expected score, G
For each resignation, G is the expected final score (win = 1, draw = 0.5, loss = 0) that a comparable player obtained from a comparable position. "Comparable" is defined by a conditional outcome model, not by the engine evaluation alone.

- Model: gradient-boosted trees (binary cross-entropy on the score with draws entered as 0.5 weights), fitted separately by speed class.
- Features of the position after the last move: evaluation from the player's side (centipawns clipped at +/-2000; forced mate as a separate category with mate distance); own rating; rating difference; own and opponent remaining clock in seconds and as a share of the initial time; increment; ply number; side to move; material count for each side.
- Training positions: one randomly chosen position per game at ply 10 or later, so that games contribute equally.
- Two versions bound the counterfactual:
  - Lower bound (L): trained on all games, where resigned games count as losses.
  - Upper bound (U): trained only on games that did not end by resignation.
- Cross-fitting: 5 folds by game identifier hash. Each resignation is scored by models that did not see that game.
- Calibration of both models is reported on held-out positions (reliability table in 10 bins, by speed class). If the held-out calibration error of model U exceeds 0.02 in any bin with at least 1,000 positions, that model is refitted with isotonic recalibration and this is reported.
- Benchmark: the Lichess engine-based win formula applied to the same evaluation.

### 3.4 Secondary outcomes
- Share of resignations with G_L at or above 0.10 and 0.20.
- Share of resignations at an evaluation of -1.00 pawns or better.
- Hopeless persistence: among losses that ended by checkmate or time forfeit, the number of own moves played while G_L stayed at or below 0.02 until the end; share with 10 or more such moves.
- Share of the forgone score that comes from wins or draws on time in comparable played-on games (to separate "flagging" from recoveries on the board).
- Implied price of time (exploratory): forgone rating points per minute saved, using G_L, the recorded rating change of the loss, and the median remaining duration of comparable played-on games.

### 3.5 Hypotheses
Thresholds are stated as effect sizes because N is in the millions. The smallest effect size of interest (SESOI) is 0.01 expected score.

- H1 (gap). In every speed class (bullet, blitz, rapid, classical), mean G_L exceeds the mean engine-based benchmark by more than 0.01, and mean G_L exceeds 0.05.
- H2 (skill). Within each speed class, mean G_L decreases with the resigner's rating: the slope per 400 rating points is negative and its 99% interval excludes values above -0.005.
- H3 (speed). Mean G_L is ordered bullet > blitz > rapid > classical.
- H4 (after a loss). Within player (player fixed effects, same speed class), when the previous game started within 60 minutes and was lost: (a) a loss is more likely to end by resignation, and (b) G_L at resignation is higher, than when the previous game was not lost. Directional, tested at the SESOI of 0.5 percentage points for (a) and 0.005 for (b).
- H5 (two-sided error). No directional hypothesis. The rates in 3.4 are reported side by side by speed and rating.

The relation between G and the resigner's own remaining clock within a speed class is exploratory (the pilot pattern was confounded with speed).

### 3.6 Threats that the design addresses
- Selection into resignation. Resigners may choose positions that are worse than the features show. Two additional estimates are reported: (i) a within-player comparison of G_L at resignation with the outcome of the same player's own played-on games from positions with model score within 0.01; (ii) a sensitivity bound (how strong an unobserved difference would be needed to bring mean G_L below 0.05).
- Selection of evaluated games. Server analysis is requested after the game (10.4% of pilot games; 6% bullet to 32% classical). Main estimates are reweighted to the full population by speed, rating band, termination class, and game-length decile. In addition, 50,000 randomly drawn resignations without server evaluation are evaluated locally and their G_L distribution is compared with the reweighted estimate.
- Local engine: Stockfish 18, one thread, 128 MB hash, a new game state for every position (engine state carry-over is not allowed), fixed budget of 1,000,000 nodes per position. If a 1,000-position timing run shows that 50,000 positions cannot be completed within 48 hours on the author's machine, the sample is reduced (minimum 20,000) while the node budget is kept. Binary hash and settings are recorded in a manifest. For reference, an earlier project on the same machine ran depth-20 MultiPV-5 at 0.93 positions per second.

### 3.7 Inference
- Player-clustered bootstrap (2,000 resamples, clusters = resigning player) for all means, shares, and slopes; 99% intervals.
- H4: linear probability and linear models with player fixed effects, standard errors clustered by player.
- The replication month is analysed with frozen code and reported in full, whatever the result.

## 4. Study 2: surrender in League of Legends

### 4.1 Data
- Riot Games API (personal key): league-v4 for a tier-stratified sample of accounts; match-v5 for match and timeline data. Ranked solo queue (queue 420). Platforms: KR, EUW1, and NA1. Ten strata per platform: Iron, Bronze, Silver, Gold, Platinum, Emerald, Diamond (divisions I to IV, randomly drawn ladder pages), Master, Grandmaster, Challenger. 200 seed accounts per stratum (seed fixed in the collection script), up to 20 most recent ranked solo matches per account, giving about 40,000 matches per platform and about 120,000 in total before de-duplication. The sample may be enlarged by raising the number of seed accounts per stratum with the same script before any outcome analysis; the final N is reported. The patch of each match is recorded and entered as a covariate in the state model. Pilot matches are excluded.
- Exclusions: remakes (`gameEndedInEarlySurrender` or duration under 5 minutes); surrenders before 15:00 (leaver-related unanimous votes); matches with a leaver, defined as a participant whose total gold and position do not change for 3 or more consecutive frames before the end; matches without a timeline.
- Raw API data are not redistributed.

### 4.2 Outcome
P_surr: the model win probability of the surrendering team at the last timeline frame before the game ended.

- State model: gradient-boosted trees on per-minute frames from minute 5. Features (team differences and levels): total gold, experience, kills, towers, inhibitors, dragons and dragon soul, baron and elder buffs active, number of champions alive on each side and summed respawn time remaining (reconstructed from kill events and levels), game minute.
- Bounds as in Study 1: model L on all matches (surrenders count as losses), model U on matches played to the end. Cross-fitting in 5 folds by match.
- Calibration on held-out frames of played-out matches is reported.

### 4.3 Hypotheses
- H6 (tail). The share of surrenders with P_surr at or above 0.10 under model L exceeds 5%.
- H7 (no skill gradient). The slope of mean P_surr (model L) across the ten strata is within +/-0.005 per stratum step (equivalence test at the 99% level). The contrast with H2 is the cross-domain comparison: the standardized skill slope in chess is more negative than in LoL.
- Surrender timing (15 to 20 minutes versus later) is exploratory.

### 4.4 Stated limits
- Only passed votes are observable. Failed votes and vote timing are not in the API, so no LoL counterpart of the hopeless-persistence analysis is possible.
- Team composition, scaling, and communication are not modelled. P_surr is an upper-leaning estimate of the surrendering team's chances, because a team that wants to quit plays worse.
- Matches are clustered by seed account; intervals use a cluster bootstrap by seed account. Platform is a fixed effect, and H6 and H7 are also reported per platform.

## 5. What would count against the main claims
- H1 fails if, with the conditional model, mean G_L is at or below 0.05 in two or more speed classes. The paper would then report that resignations are well calibrated once clock and phase are taken into account.
- The cross-domain claim (RQ5) fails if H2 fails or if H7 is rejected.

## 6. Deviations
Any change after registration is listed in a deviations table with date, reason, and whether results had been seen. Registered and corrected analyses are both reported.

## 7. Open materials
- Code, manifests, aggregate tables, and this document: public GitHub repository, archived on Zenodo at registration and again at submission.
- Chess: game identifiers and derived per-game variables (public CC0 source).
- LoL: match identifiers and aggregate tables only. No player identifiers.

## 8. Ethics and AI use
Secondary analysis of public data; no ethics review was sought. Player names are used only for clustering and are replaced by random identifiers in shared files. Generative AI (Claude, Anthropic) was used for literature search support, code scaffolding, and drafting; the author verified all outputs. A usage log is kept in the repository.

## 9. Relation to the author's other work
A separate manuscript studies performance after a loss in chess. The present study concerns the decision to quit, uses different months of data, and reports no overlapping results.

## 10. Closest prior work
Purohit and Srivastava (2026, Cognitive Science, doi:10.1111/cogs.70193) model who resigns in classical Lichess games with a survival model and raw centipawn evaluations. The present study estimates the chance given up at the moment of resignation with skill- and clock-conditional outcome models, covers fast time controls, measures the opposite error, and adds a team-vote comparison.
