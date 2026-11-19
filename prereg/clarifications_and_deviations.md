# Clarifications made before confirmatory data were analysed

Written 2026-11-15, after registration (release v1.0-prereg) and before any confirmatory data were parsed or analysed. These are implementation choices that the registered text left open. None was informed by confirmatory data.

| # | Registered text | Implementation | Reason |
|---|---|---|---|
| C1 | H4: "the previous game started within 60 minutes and was lost", "same speed class" | The previous game is the player's most recent game in the same speed class in the monthly dump, started at most 3,600 s earlier. | Makes "same speed class" operational. |
| C2 | H4a uses losses from all games | H4a is estimated on all losses of a 10% sample of players, selected by a hash of the player name (hash mod 10 = 0). | Keeps the all-games table manageable. The sample is fixed by the hash, not by any outcome. |
| C3 | Hopeless persistence: own moves played while G_L stayed at or below 0.02 until the end | G_L is computed only for trailing positions reached by walking back from the end while the loser's evaluation is -3.00 pawns or worse (at most 80 plies). A position better than -3.00 ends the run. | Computing G_L for every ply of every loss is not feasible. The rule can only undercount persistence. |
| C4 | Training positions: "one randomly chosen position per game at ply 10 or later" | The position is drawn uniformly from plies 10 and later that carry a server evaluation, with a per-game seed derived from the game identifier; the point of view (White or Black) is drawn at random with the same seed. | Reproducibility and symmetry. |
| C5 | Model: gradient-boosted trees | scikit-learn HistGradientBoostingClassifier, 300 iterations, learning rate 0.08, 63 leaves, minimum 200 samples per leaf, L2 = 1, no early stopping, random_state 29; draws enter as two half-weight rows. LoL: 300 iterations, learning rate 0.05, 31 leaves, minimum 50 per leaf. | Fixes hyperparameters before data. |
| C6 | Reweighting by game-length decile | Game length is binned in 10-ply bins at extraction; each bin is assigned to a decile by its cumulative midpoint in the all-games distribution. | The dump is parsed once, before deciles are known. |
| C7 | LoL leaver: a participant whose total gold and position do not change for 3 or more consecutive frames before the end | Applied literally to the four frames before the final frame. In the pilot this rule flagged no match, so a looser rule (position unchanged, gold ignored) is reported as a sensitivity analysis. The registered rule stays primary. | Passive gold income continues for inactive players. |
| C8 | Respawn time remaining | Reconstructed from kill events, the victim's level at the latest frame, and the published death-timer table (base wait by level, increased after minute 15, capped at +50%). | The API does not expose respawn timers. |
| C9 | LoL clusters: seed account | A match is assigned to the first seed account found among its participants. | A match can contain more than one seed account. |
| C10 | Within-player comparison with own played-on games "from positions with model score within 0.01" | Resignations and the same player's training positions from games played to the end are matched within 0.02-wide bins of the model score (same speed class). The comparison is the mean realised score of the matched own positions minus the mean G_L of the matched resignations. | A fixed bin of width 0.02 is the computable form of "within 0.01". |
| C11 | Share of the forgone score that comes from wins or draws on time | A separate cross-fitted model (same features, all games) predicts the probability that the player wins by time forfeit; the share is its mean at resignation divided by mean G_L. Draws on time are not counted. | Time-forfeit draws cannot be separated from other draws in the dump. |
| C12 | Implied price of time (exploratory) | Forgone rating points = K x G_L with K = abs(recorded rating change of the loss) / E, where E is the pre-game expected score from the rating difference (logistic, 400-point scale, clipped to 0.05 to 0.95). Minutes saved = cross-fitted median clock time still used after comparable positions in games played to the end. The price is the ratio of weighted means. | Makes the registered description operational. |
| C13 | Sensitivity bound | The bound is the factor by which the odds of every G_L would have to be divided for the weighted mean G_L to fall to 0.05. | One-parameter form of "how strong an unobserved difference would be needed". |
| C14 | Local-engine validation | The engine sample (resignations without server evaluation) is scored with the same cross-fitted models, using the local evaluation of the final position. It is compared with evaluated resignations reweighted to the unevaluated population (weight = unevaluated count / evaluated count per cell). | The engine sample represents unevaluated games only. |


# Deviations and additions after confirmatory results were seen

| # | Date | What | Why | Results seen? |
|---|---|---|---|---|
| D1 | 2026-11-16 | Bridge sample: 9,883 resignations WITH a server evaluation were also evaluated with the local engine (same settings as the registered validation). Exploratory. | The registered engine validation gave a higher mean G_L for unevaluated resignations than the reweighted estimate. The bridge sample tests whether the two evaluation sources are on the same scale. | Yes (September results) |
| D2 | 2026-11-16 | Bridge-scaled engine comparison: local centipawn values of the registered engine sample are multiplied by 1.206 (pooled through-origin slope of server on local evaluation in the bridge sample) and rescored. Reported next to the registered, unscaled comparison. Exploratory. | The bridge sample showed that the local engine gives evaluations about 20% smaller in magnitude than the server on the same positions. | Yes (September results) |

## D3 (2026-11-16, after September results, before any June result was seen): crash fix in chess_model.py

The June run stopped in the first fold of bullet with `AttributeError: 'DataFrame' object has no attribute 'fold'`. Cause: June has no local-engine sample (the engine validation was registered for the main month only), so the two engine tables were empty frames without columns. Fix: when an engine table is empty, an empty frame with the columns of the resignation table is used (two lines after the tables are loaded). No estimate, model setting, or sample definition changes; September outputs are unaffected because both engine tables exist there. File hash prefix before baf6acb0ea6741b7, after e63c5cd222830477. No June estimate had been produced when the fix was made.

## D4 (2026-11-17, after all confirmatory results and a simulated review): exploratory additions

All of the following were added after every registered result had been seen. They are exploratory and are labelled as such wherever they are reported.

- Move-level resignation hazard (`02_code/chess_hazard.py`): a 10% hash sample of evaluated games; unit = a position at ply 10 or later with the player's evaluation at -3.00 pawns or worse; event = resignation in that position. Linear probability models with board-state cells and player fixed effects estimate the response of the hazard to the rating gap and to the opponent's clock, next to the response of the realised score of positions that were played on.
- Descriptives from the model outputs: implied price of time by rating band and with recorded rating changes above 20 points excluded (likely provisional ratings); composition of the costliest tenth of resignations; resignations at evaluations better than -3.00 pawns as a separate group; forgone score and median evaluation by rating gap within rating band.
- Reason: the simulated review (one editor, three referees) pointed out that the comparison of median evaluations at resignation across rating bands conditions on resigning and cannot show that the resignation decision ignores the opponent.

## D5 (2026-11-18, exploratory, September and June 2026 only): two central claims formulated and withdrawn

- A first draft claimed that players of all ratings resign at the same evaluation and therefore ignore the opponent. The move-level hazard (D4) contradicted it: in the same board state stronger players resign far more often, and the hazard responds strongly to the opponent's clock. Withdrawn.
- A second draft claimed that stronger players' resignations are better aimed (concentrated where the value of playing on is low). Added to `chess_hazard.py` for this purpose: `--skill` (targeting summaries with a continuation value that counts later resignations as losses) and `--rot` (a continuation value V_U trained only on games the player did not end by resigning; band-specific logit profiles; within-player odds ratios; exposure-standardised shares; share of players who never resign). With V_U the rating gradient is a level shift of about the same ratio at every value, not a steeper profile. Withdrawn. A second simulated review had independently pointed to the circularity of the first value.
- What survived on both months is registered as hypotheses K1 to K7 in `preregistration_2_v1.0.md`, to be tested on July and August 2026, which had not been downloaded when that document was registered.

## D6 (2026-11-18 to 2026-11-19, before any July or August 2026 data were downloaded): code changes for the second preregistration

- `chess_stage_a.py` additionally records whether the Event tag names a tournament, swiss, or arena (one extra field per game record; nothing else changes). `chess_hazard.py` carries the flag through; months extracted earlier lack it and are treated as unknown.
- `chess_hazard.py --rot` computes the registered decision rules (K1 to K6), K7 from the stage A cell counts, the robustness subsets, and the calibration gate with isotonic recalibration. The gate was written into the draft before it was coded; it was coded on 2026-11-18 and checked on both exploratory months on 2026-11-19 (not triggered in bullet, blitz, or rapid; triggered in classical).
- Frozen hashes (SHA-256): `chess_hazard.py` 4886dc9bd01391002b67afc8089d0952d74b6baa059ade8b3e773af41e6423f7; `chess_stage_a.py` 988277ceba91ad98ac87174b3bae52c570067ff238745657d02d0b938154ec51.
