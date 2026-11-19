#!/usr/bin/env python3
"""Move-level resignation hazard (EXPLORATORY, not preregistered; added 2026-11-17 after the simulated review).
Needs python-chess, numpy, pandas, pyarrow.

Question: holding the state of the board fixed, does the probability of resigning at a given position respond to
the opponent's rating and the opponent's clock, and does it respond in proportion to how much those variables
change the value of playing on?

Step 1 (extract; parallel, resumable):
  python3 02_code/chess_hazard.py --dir 03_work/chess_2026-09 --workers 6
Step 2 (tables and regressions):
  python3 02_code/chess_hazard.py --dir 03_work/chess_2026-09 --model --out 04_output/hazard_2026-09
Step 4 (level versus rotation; needs scikit-learn and scipy):
  python3 02_code/chess_hazard.py --dir 03_work/chess_2026-09 --rot --out 04_output/hazard_rot_2026-09
Step 3 (is resignation well targeted? needs scikit-learn):
  python3 02_code/chess_hazard.py --dir 03_work/chess_2026-09 --skill --out 04_output/hazard_skill_2026-09

Risk set: a 10% hash sample of evaluated games. Unit = a position at ply 10 or later in which the player's
evaluation is -3.00 pawns or worse (or a forced mate against). Event = the player resigns in that position
(it is the last evaluated position of a game that ended by the player's resignation)."""
import os, sys, re, gzip, json, zlib, argparse, glob, math
from multiprocessing import Pool
import numpy as np, pandas as pd

PAIR = re.compile(r'([^\s{}]+)\s*\{([^}]*)\}'); EVAL = re.compile(r'%eval (#?-?\d+(?:\.\d+)?)'); CLK = re.compile(r'%clk (\d+):(\d+):(\d+)')
COLS = ['gid', 'player', 'speed', 'ply', 'cp', 'mate_against', 'mate_dist', 'elo', 'elo_diff', 'clk', 'clk_opp', 'clk_share', 'clk_opp_share',
        'inc', 'base', 'stm', 'mat', 'mat_opp', 'drop1', 'drop2', 'dur', 'event', 'cls', 'y', 'rd_abs', 'berserk', 'plies_left', 'arena']
SAMPLE_MOD = int(os.environ.get('HAZARD_SAMPLE_MOD', '10'))

def clip(x): return max(-2000, min(2000, x))

def do_chunk(args):
    import chess
    VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    def material(b, color): return sum(v * chess.popcount(b.pieces_mask(pt, color)) for pt, v in VAL.items())
    k, lines, outdir = args
    done = os.path.join(outdir, f'hdone_{k:06d}')
    if os.path.exists(done): return k, 0, 0, 0
    rows = []; bad = 0; ngames = 0; nres = 0; nres_in = 0
    for line in lines:
        try:
            rec = json.loads(line)
            gid, wh, bh, we, be, res, cls, sp, base, inc, ts, pw, pb, mt = rec[:14]
            if zlib.crc32((gid + 'h').encode()) % SAMPLE_MOD != 0: continue
            rdw, rdb = (rec[14], rec[15]) if len(rec) >= 16 else (None, None); arena = int(rec[16]) if len(rec) >= 17 and rec[16] is not None else -1
            pairs = PAIR.findall(mt); n = len(pairs); ngames += 1
            ev = []; md = []; ck = []
            for _, c in pairs:
                m = EVAL.search(c)
                if not m: ev.append(None); md.append(0)
                elif m.group(1)[0] == '#':
                    d = int(m.group(1)[1:]); ev.append(100000 if d > 0 else -100000); md.append(abs(d))
                else: ev.append(int(round(float(m.group(1)) * 100))); md.append(0)
                m = CLK.search(c); ck.append(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) if m else None)
            last = next((j for j in range(n - 1, -1, -1) if ev[j] is not None), None)
            if last is None or last < 9: continue
            if cls == 'resign': nres += 1
            b = chess.Board(); mw = []; mb = []
            for san, _ in pairs:
                b.push_san(san.rstrip('?!')); mw.append(material(b, chess.WHITE)); mb.append(material(b, chess.BLACK))
            wscore = 1.0 if res == '1-0' else 0.0 if res == '0-1' else 0.5
            bb = max(base, 1)
            bz_w = int(ck[0] is not None and ck[0] < 0.75 * base) if n > 0 else 0
            bz_b = int(ck[1] is not None and ck[1] < 0.75 * base) if n > 1 else 0
            for white_view in (True, False):
                s = 1 if white_view else -1
                loser_resigned = cls == 'resign' and ((res == '0-1') == white_view)
                dur = 0; hit = False
                for i in range(9, last + 1):
                    e = ev[i]
                    if e is None: continue
                    x = s * e
                    if x > -300: dur = 0; continue
                    cw = ck[i] if i % 2 == 0 else (ck[i - 1] if i > 0 else None); cb = ck[i] if i % 2 == 1 else (ck[i - 1] if i > 0 else None)
                    c_own, c_opp = (cw, cb) if white_view else (cb, cw)
                    if c_own is None or c_opp is None: dur += 1; continue
                    ma = int(x <= -100000); cp = -2000 if ma else clip(x)
                    def prev(j):
                        if j < 0 or ev[j] is None: return None
                        v = s * ev[j]; return 2000 if v >= 100000 else -2000 if v <= -100000 else clip(v)
                    p1 = prev(i - 1); p2 = prev(i - 2)
                    event = int(loser_resigned and i == last)
                    if event: hit = True
                    rd = rdw if white_view else rdb
                    rows.append([gid, wh if white_view else bh, sp, i + 1, cp, ma, md[i] if ma else 0, we if white_view else be,
                                 (we - be) if white_view else (be - we), c_own, c_opp, c_own / bb, c_opp / bb, inc, base,
                                 int((i % 2 == 1) == white_view), mw[i] if white_view else mb[i], mb[i] if white_view else mw[i],
                                 (cp - p1) if p1 is not None else 0, (cp - p2) if p2 is not None else 0, dur, event, cls,
                                 wscore if white_view else 1 - wscore, abs(rd) if rd is not None else -1, bz_w if white_view else bz_b, last - i, arena])
                    dur += 1
                if loser_resigned and hit: nres_in += 1
        except Exception:
            bad += 1
    df = pd.DataFrame(rows, columns=COLS)
    for c in ('ply', 'cp', 'mate_dist', 'elo', 'elo_diff', 'clk', 'clk_opp', 'inc', 'base', 'mat', 'mat_opp', 'drop1', 'drop2', 'dur', 'plies_left'): df[c] = df[c].astype('int32')
    for c in ('mate_against', 'stm', 'event', 'berserk', 'arena'): df[c] = df[c].astype('int8')
    for c in ('clk_share', 'clk_opp_share', 'y', 'rd_abs'): df[c] = df[c].astype('float32')
    df['player'] = df['player'].astype('uint64')
    tmp = os.path.join(outdir, f'hazard_{k:06d}.parquet.tmp'); df.to_parquet(tmp, index=False); os.replace(tmp, tmp[:-4])
    open(done, 'w').write(f'{ngames} {bad} {nres} {nres_in}')
    return k, ngames, bad, len(df)

def chunks(path, size):
    buf = []; k = 0
    with gzip.open(path, 'rt') as f:
        for line in f:
            buf.append(line)
            if len(buf) >= size: yield k, buf; buf = []; k += 1
    if buf: yield k, buf

def extract(a):
    outdir = os.path.join(a.dir, 'hazard_parts'); os.makedirs(outdir, exist_ok=True)
    src = os.path.join(a.dir, 'eval_games.jsonl.gz'); tot = bad = rows = 0
    with Pool(a.workers) as pool:
        for k, n, b, r in pool.imap_unordered(do_chunk, ((k, lines, outdir) for k, lines in chunks(src, 20000)), chunksize=1):
            tot += n; bad += b; rows += r
            if k % 25 == 0: print(f'[hazard] chunk {k}: {tot:,} sampled games, {rows:,} at-risk positions, {bad} unparsable', file=sys.stderr, flush=True)
    print(f'[hazard] extraction done: {tot:,} sampled games this run, {rows:,} at-risk positions, {bad} unparsable', file=sys.stderr)

# ---------------------------------------------------------------- model
SPEEDS = ['bullet', 'blitz', 'rapid', 'classical']
EB = [-2001, -1200, -900, -700, -500, -300]; EBL = ['mate or <-12', '-12 to -9', '-9 to -7', '-7 to -5', '-5 to -3']
def ebin(d): return np.select([(d.mate_against == 1) | (d.cp < -1200), d.cp < -900, d.cp < -700, d.cp < -500], [0, 1, 2, 3], 4)
def band(e): return np.select([e < 1200, e < 1600, e < 2000], [0, 1, 2], 3)
BL = ['<1200', '1200-1599', '1600-1999', '2000+']

def fe_ols(d, ycol, xcols, cell, fe=True):
    """Linear probability model. Cell effects (and optional player fixed effects) are absorbed by alternating
    within-group demeaning; standard errors are cluster-robust by player."""
    M = d[[ycol] + xcols].astype('float64').reset_index(drop=True)
    keys = [pd.factorize(d[cell].values)[0]] + ([pd.factorize(d['player'].values)[0]] if fe else [])
    for _ in range(12 if fe else 1):
        for kk in keys: M = M - M.groupby(kk).transform('mean')
    y = M[ycol].values; Xm = M[xcols].values; XtX = Xm.T @ Xm; bread = np.linalg.pinv(XtX); beta = bread @ (Xm.T @ y)
    e = y - Xm @ beta
    S = pd.DataFrame(Xm * e[:, None]).groupby(pd.factorize(d['player'].values)[0]).sum().values
    V = bread @ (S.T @ S) @ bread; se = np.sqrt(np.diag(V))
    return {c: {'b': float(beta[j]), 'se': float(se[j]), 'ci99': [float(beta[j] - 2.576 * se[j]), float(beta[j] + 2.576 * se[j])]} for j, c in enumerate(xcols)}

def model(a):
    fs = sorted(glob.glob(os.path.join(a.dir, 'hazard_parts', 'hazard_*.parquet')))
    D = pd.concat((pd.read_parquet(f) for f in fs), ignore_index=True)
    flow = np.array([list(map(int, open(f).read().split())) for f in glob.glob(os.path.join(a.dir, 'hazard_parts', 'hdone_*'))]).sum(axis=0)
    R = {'note': 'EXPLORATORY. Risk set: positions at ply>=10 with own evaluation <= -3.00 pawns (or mate against), 10% hash sample of evaluated games.',
         'flow': {'sampled_games': int(flow[0]), 'unparsable': int(flow[1]), 'resignations_in_sample': int(flow[2]), 'resignations_inside_risk_set': int(flow[3])},
         'speeds': {}}
    D['eb'] = ebin(D); D['band'] = band(D.elo.values)
    D['opp_weaker_100'] = D.elo_diff / 100.0                    # own rating minus opponent rating, per 100 points
    D['ln_clk_opp'] = np.log(D.clk_opp + 1.0); D['ln_clk'] = np.log(D.clk + 1.0)
    D['drop2_p'] = D.drop2 / 100.0; D['dur10'] = np.minimum(D.dur, 60) / 10.0; D['ply10'] = D.ply / 10.0; D['matdiff'] = (D.mat - D.mat_opp).clip(-15, 5)
    D['elo100'] = D.elo / 100.0
    D['cell'] = D.eb.astype(str) + '_' + D.stm.astype(str) + '_' + D.matdiff.astype(str) + '_' + (D.mat + D.mat_opp > 30).astype(int).astype(str)
    XC = ['opp_weaker_100', 'ln_clk_opp', 'ln_clk', 'drop2_p', 'dur10', 'ply10']
    for sp in SPEEDS:
        d = D[D.speed == sp]
        if len(d) < 5000: continue
        S = {'n_positions': int(len(d)), 'n_events': int(d.event.sum()), 'n_players': int(d.player.nunique()), 'hazard': float(d.event.mean())}
        # 1. raw hazard and realised score of non-event positions, by evaluation bin and own rating band
        S['hazard_by_eval_band'] = {EBL[e]: {BL[b]: [int(len(x)), float(x.event.mean()), float(x.y[x.event == 0].mean()) if (x.event == 0).any() else None]
                                             for b, x in g.groupby('band')} for e, g in d.groupby('eb')}
        # 2. by opponent clock share (all evaluation bins pooled within the -9 to -5 range) and by rating gap
        mid = d[d.eb.isin([2, 3])]
        mid = mid.assign(ocb=pd.cut(mid.clk_opp_share, [-1, 0.05, 0.10, 0.25, 0.50, 10], labels=['<5%', '5-10%', '10-25%', '25-50%', '>50%']),
                         gap=pd.cut(mid.elo_diff, [-5000, -150, -50, 50, 150, 5000], labels=['opp stronger by 150+', '50-150 stronger', 'within 50', '50-150 weaker', 'opp weaker by 150+']))
        S['mid_eval_by_opp_clock'] = {str(k): [int(len(x)), float(x.event.mean()), float(x.y[x.event == 0].mean())] for k, x in mid.groupby('ocb', observed=True)}
        S['mid_eval_by_rating_gap'] = {str(k): [int(len(x)), float(x.event.mean()), float(x.y[x.event == 0].mean())] for k, x in mid.groupby('gap', observed=True)}
        S['mid_eval_by_band_and_gap'] = {BL[b]: {str(k): [int(len(x)), float(x.event.mean()), float(x.y[x.event == 0].mean())] for k, x in g.groupby('gap', observed=True)} for b, g in mid.groupby('band')}
        # 3. sudden drop versus grind
        d2 = d.assign(kind=np.select([d.dur == 0, d.dur <= 4], ['first position at <= -3', '2 to 5 positions in'], 'more than 5 positions in'))
        S['by_time_in_losing_state'] = {k: [int(len(x)), float(x.event.mean()), float(x.event.sum() / max(d.event.sum(), 1))] for k, x in d2.groupby('kind')}
        S['events_with_drop2_le_-3'] = float(((d.event == 1) & (d.drop2 <= -300)).sum() / max(d.event.sum(), 1))
        # 4. regressions: hazard (all positions) and value of playing on (non-event positions), same specification
        keep = d.groupby('player').player.transform('size') >= 5; dfe = d[keep]
        S['lpm_hazard_player_fe'] = fe_ols(dfe, 'event', XC, 'cell', fe=True); S['lpm_hazard_pooled'] = fe_ols(d, 'event', XC + ['elo100'], 'cell', fe=False)
        ne = d[d.event == 0]; S['lpm_value_pooled'] = fe_ols(ne, 'y', XC + ['elo100'], 'cell', fe=False)
        nefe = dfe[dfe.event == 0]; S['lpm_value_player_fe'] = fe_ols(nefe, 'y', XC, 'cell', fe=True)
        S['mean_value_non_event'] = float(ne.y.mean()); S['n_fe'] = int(len(dfe))
        # 5. robustness: drop berserk games and likely provisional ratings (recorded rating change above 20 points or missing)
        cl = dfe[(dfe.berserk == 0) & (dfe.rd_abs >= 0) & (dfe.rd_abs <= 20)]
        S['lpm_hazard_player_fe_clean'] = fe_ols(cl, 'event', XC, 'cell', fe=True); S['n_clean'] = int(len(cl))
        # 6. implied proportional responses
        hz = S['hazard']; mv = S['mean_value_non_event']
        S['relative_response'] = {
            'opp_200_weaker': {'hazard_change_rel': 2 * S['lpm_hazard_player_fe']['opp_weaker_100']['b'] / hz, 'value_change_rel': 2 * S['lpm_value_pooled']['opp_weaker_100']['b'] / mv},
            'opp_clock_halved': {'hazard_change_rel': -math.log(2) * S['lpm_hazard_player_fe']['ln_clk_opp']['b'] / hz, 'value_change_rel': -math.log(2) * S['lpm_value_pooled']['ln_clk_opp']['b'] / mv}}
        R['speeds'][sp] = S
        print(f'[hazard] {sp}: {len(d):,} positions, {int(d.event.sum()):,} resignations', file=sys.stderr, flush=True)
    json.dump(R, open(a.out + '.json', 'w'), indent=1)
    L = ['# Resignation hazard (exploratory)\n', R['note'] + '\n', '```\n' + json.dumps(R['flow']) + '\n```\n']
    for sp, S in R['speeds'].items():
        L += [f"## {sp}: {S['n_positions']:,} at-risk positions, {S['n_events']:,} resignations, hazard per position {S['hazard']:.4f}\n",
              '### Hazard by evaluation and own rating (n, hazard, realised score when play continued)\n', '| evaluation | ' + ' | '.join(BL) + ' |', '|---|' + '---|' * 4]
        for e in EBL:
            if e in S['hazard_by_eval_band']:
                L.append(f'| {e} | ' + ' | '.join((lambda v: f'{v[1]:.4f} / {v[2]:.3f} (n={v[0]:,})' if v and v[2] is not None else '-')(S['hazard_by_eval_band'][e].get(b)) for b in BL) + ' |')
        for title, key in (('Evaluation -9 to -5: by opponent clock (share of initial time)', 'mid_eval_by_opp_clock'), ('Evaluation -9 to -5: by rating gap', 'mid_eval_by_rating_gap')):
            L += [f'\n### {title}\n', '| group | n | hazard | realised score when play continued |', '|---|---|---|---|'] + [f'| {k} | {v[0]:,} | {v[1]:.4f} | {v[2]:.3f} |' for k, v in S[key].items()]
        L += ['\n### Time in the losing state (n, hazard, share of all resignations)\n'] + [f'- {k}: n={v[0]:,}, hazard {v[1]:.4f}, share of resignations {v[2]:.3f}' for k, v in S['by_time_in_losing_state'].items()]
        L += [f"- resignations right after a drop of 3 pawns or more over the last two plies: {S['events_with_drop2_le_-3']:.3f}\n", '### Linear probability models (coefficient [99% CI])\n',
              '| regressor | hazard, player FE | hazard, pooled | hazard, player FE, clean sample | value of playing on, pooled | value, player FE |', '|---|---|---|---|---|---|']
        f = lambda r, c: (lambda v: f"{v['b']:.5f} [{v['ci99'][0]:.5f}, {v['ci99'][1]:.5f}]")(r[c]) if c in r else '-'
        for c in XC: L.append(f"| {c} | {f(S['lpm_hazard_player_fe'], c)} | {f(S['lpm_hazard_pooled'], c)} | {f(S['lpm_hazard_player_fe_clean'], c)} | {f(S['lpm_value_pooled'], c)} | {f(S['lpm_value_player_fe'], c)} |")
        rr = S['relative_response']
        L += ['', f"Relative responses. Opponent 200 points weaker: value of playing on {rr['opp_200_weaker']['value_change_rel']:+.1%}, hazard {rr['opp_200_weaker']['hazard_change_rel']:+.1%}. "
                  f"Opponent clock halved: value {rr['opp_clock_halved']['value_change_rel']:+.1%}, hazard {rr['opp_clock_halved']['hazard_change_rel']:+.1%}.\n"]
    open(a.out + '.md', 'w').write('\n'.join(L)); print(f'[hazard] wrote {a.out}.json and .md', file=sys.stderr)


# ---------------------------------------------------------------- skill: is resignation well targeted?
VF = ['cp', 'mate_against', 'mate_dist', 'elo', 'elo_diff', 'clk', 'clk_opp', 'clk_share', 'clk_opp_share', 'inc', 'ply', 'stm', 'mat', 'mat_opp', 'drop2', 'dur']
def auc_low_value(v, e):
    """Probability that a resigned position has a lower continuation value than a position that was played on."""
    r = pd.Series(v).rank(method='average').values; n1 = int(e.sum()); n0 = len(e) - n1
    if n1 == 0 or n0 == 0: return None
    return float(1 - (r[e == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def skill(a):
    from sklearn.ensemble import HistGradientBoostingRegressor
    fs = sorted(glob.glob(os.path.join(a.dir, 'hazard_parts', 'hazard_*.parquet')))
    R = {'note': 'EXPLORATORY. Continuation value V: cross-fitted gradient-boosted regression of the final score on the state, trained on at-risk positions '
                 'that were played on (5 folds by game). Targeting efficiency = (mean V of all at-risk positions - mean V at resignations) / '
                 '(mean V of all at-risk positions - mean V of the lowest-V positions, taking as many as there are resignations), within speed and rating band.', 'speeds': {}}
    rng = np.random.default_rng(29)
    for sp in SPEEDS:
        d = pd.concat((pd.read_parquet(f, filters=[('speed', '==', sp)]) for f in fs), ignore_index=True)
        if len(d) < 5000: continue
        d['fold'] = d.gid.map(lambda g: zlib.crc32(g.encode()) % 5) if len(d) < 200000 else pd.factorize(d.gid)[0] % 5
        d['V'] = np.float32(np.nan); X = d[VF].astype('float32')
        for k in range(5):
            tr = np.flatnonzero(((d.fold != k) & (d.event == 0)).values)
            if len(tr) > 1500000: tr = rng.choice(tr, 1500000, replace=False)
            m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, max_leaf_nodes=63, min_samples_leaf=200, l2_regularization=1.0, random_state=29).fit(X.iloc[tr], d.y.values[tr])
            te = np.flatnonzero((d.fold == k).values); d.iloc[te, d.columns.get_loc('V')] = np.clip(m.predict(X.iloc[te]), 0, 1).astype('float32')
        d['band'] = band(d.elo.values); S = {'n_positions': int(len(d)), 'n_events': int(d.event.sum())}
        ne = d[d.event == 0]; b10 = np.minimum((ne.V.values * 10).astype(int), 9)
        S['value_model_calibration'] = [[int(k), int((b10 == k).sum()), float(ne.V.values[b10 == k].mean()), float(ne.y.values[b10 == k].mean())] for k in range(10) if (b10 == k).any()]
        qs = np.quantile(d.V.values, np.linspace(0.1, 0.9, 9)); d['vdec'] = np.searchsorted(qs, d.V.values)
        S['by_band'] = {}
        for b, g in d.groupby('band'):
            v = g.V.values.astype('float64'); e = g.event.values; n1 = int(e.sum())
            if n1 < 50: continue
            A = float(v[e == 1].mean()); M = float(v.mean()); O = float(np.sort(v)[:n1].mean())
            hz_dec = [[int(k), int(len(x)), float(x.event.mean()), float(x.V.mean())] for k, x in g.groupby('vdec')]
            lo = g[g.vdec <= 1]; hi = g[g.vdec >= 5]
            S['by_band'][BL[b]] = {'n_positions': int(len(g)), 'n_resignations': n1, 'hazard': float(e.mean()), 'mean_V_at_risk': M, 'mean_V_at_resignation': A,
                                   'mean_V_if_perfectly_targeted': O, 'targeting_efficiency': (M - A) / (M - O) if M > O else None, 'auc': auc_low_value(v, e),
                                   'hazard_lowest_two_value_deciles': float(lo.event.mean()) if len(lo) else None, 'hazard_upper_half_of_value': float(hi.event.mean()) if len(hi) else None,
                                   'share_of_resignations_in_upper_half_of_value': float(hi.event.sum() / n1), 'hazard_by_value_decile': hz_dec,
                                   'excess_forgone_per_resignation': A - O}
        # calibration of V by rating band (positions that were played on), and the same summaries after isotonic recalibration within band
        from sklearn.isotonic import IsotonicRegression
        S['calibration_by_band'] = {}; d['Vr'] = d.V.astype('float64')
        for b, g in d.groupby('band'):
            gn = g[g.event == 0]
            S['calibration_by_band'][BL[b]] = {'overall': [int(len(gn)), float(gn.V.mean()), float(gn.y.mean())],
                                               'by_value_decile': [[int(k), int(len(x)), float(x.V.mean()), float(x.y.mean())] for k, x in gn.groupby('vdec')]}
            if len(gn) > 1000:
                iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds='clip').fit(gn.V.values.astype('float64'), gn.y.values.astype('float64'))
                d.loc[g.index, 'Vr'] = iso.predict(g.V.values.astype('float64'))
        qr = np.quantile(d.Vr.values, np.linspace(0.1, 0.9, 9)); d['vdec_r'] = np.searchsorted(qr, d.Vr.values, side='right').clip(0, 9)
        S['recalibrated_by_band'] = {}
        for b, g in d.groupby('band'):
            v = g.Vr.values; e = g.event.values; n1 = int(e.sum())
            if n1 < 50: continue
            A = float(v[e == 1].mean()); M = float(v.mean()); O = float(np.sort(v)[:n1].mean()); hi = g[g.vdec_r >= 5]
            S['recalibrated_by_band'][BL[b]] = {'mean_V_at_risk': M, 'mean_V_at_resignation': A, 'mean_V_if_perfectly_targeted': O, 'targeting_efficiency': (M - A) / (M - O) if M > O else None,
                                                'auc': auc_low_value(v, e), 'share_of_resignations_in_upper_half_of_value': float(hi.event.sum() / n1),
                                                'hazard_by_value_decile': [[int(k), int(len(x)), float(x.event.mean()), float(x.Vr.mean()), float(x.y[x.event == 0].mean()) if (x.event == 0).any() else None] for k, x in g.groupby('vdec_r')]}
        # own rating versus opponent rating, same specification for the hazard and for the value of playing on
        d['own100'] = d.elo / 100.0; d['opp100'] = (d.elo - d.elo_diff) / 100.0
        d['ln_clk_opp'] = np.log(d.clk_opp + 1.0); d['ln_clk'] = np.log(d.clk + 1.0); d['drop2_p'] = d.drop2 / 100.0; d['dur10'] = np.minimum(d.dur, 60) / 10.0; d['ply10'] = d.ply / 10.0
        d['eb'] = ebin(d); d['matdiff'] = (d.mat - d.mat_opp).clip(-15, 5)
        d['cell'] = d.eb.astype(str) + '_' + d.stm.astype(str) + '_' + d.matdiff.astype(str) + '_' + (d.mat + d.mat_opp > 30).astype(int).astype(str)
        XC = ['own100', 'opp100', 'ln_clk_opp', 'ln_clk', 'drop2_p', 'dur10', 'ply10']
        S['lpm_hazard_own_vs_opp'] = fe_ols(d, 'event', XC, 'cell', fe=False); S['lpm_value_own_vs_opp'] = fe_ols(d[d.event == 0], 'y', XC, 'cell', fe=False)
        S['hazard'] = float(d.event.mean()); S['mean_value_non_event'] = float(d.y[d.event == 0].mean())
        # same comparison among mismatched pairings only (rating gap of 100 points or more), where own and opponent rating are less collinear
        mm = d[d.elo_diff.abs() >= 100]
        S['lpm_hazard_own_vs_opp_mismatched'] = fe_ols(mm, 'event', XC, 'cell', fe=False); S['lpm_value_own_vs_opp_mismatched'] = fe_ols(mm[mm.event == 0], 'y', XC, 'cell', fe=False); S['n_mismatched'] = int(len(mm))
        R['speeds'][sp] = S
        print(f'[skill] {sp}: {len(d):,} positions done', file=sys.stderr, flush=True)
    json.dump(R, open(a.out + '.json', 'w'), indent=1)
    L = ['# Is resignation well targeted? (exploratory)\n', R['note'] + '\n']
    for sp, S in R['speeds'].items():
        L += [f"## {sp}\n", '| rating | hazard | mean V at risk | mean V at resignation | if perfectly targeted | targeting efficiency | AUC | hazard, lowest 2 value deciles | hazard, upper half | resignations in upper half |', '|---|---|---|---|---|---|---|---|---|---|']
        for b in BL:
            if b in S['by_band']:
                v = S['by_band'][b]; L.append(f"| {b} | {v['hazard']:.4f} | {v['mean_V_at_risk']:.3f} | {v['mean_V_at_resignation']:.3f} | {v['mean_V_if_perfectly_targeted']:.3f} | {v['targeting_efficiency']:.3f} | {v['auc']:.3f} | {v['hazard_lowest_two_value_deciles']:.4f} | {v['hazard_upper_half_of_value']:.4f} | {v['share_of_resignations_in_upper_half_of_value']:.3f} |")
        f = lambda r, c: f"{r[c]['b']:.5f} [{r[c]['ci99'][0]:.5f}, {r[c]['ci99'][1]:.5f}]"
        L += ['', f"Mean hazard {S['hazard']:.4f}; mean realised score when play continued {S['mean_value_non_event']:.3f}.\n", '| per 100 rating points | hazard | value of playing on | hazard, mismatched pairings | value, mismatched pairings |', '|---|---|---|---|---|']
        for c in ('own100', 'opp100'): L.append(f"| {c} | {f(S['lpm_hazard_own_vs_opp'], c)} | {f(S['lpm_value_own_vs_opp'], c)} | {f(S['lpm_hazard_own_vs_opp_mismatched'], c)} | {f(S['lpm_value_own_vs_opp_mismatched'], c)} |")
        L += ['', '### Calibration of V by rating band (decile: predicted/realised) and results after isotonic recalibration within band\n']
        for b in BL:
            if b in S['calibration_by_band']:
                c = S['calibration_by_band'][b]; L.append(f"- {b}: overall {c['overall'][1]:.3f}/{c['overall'][2]:.3f}; " + '; '.join(f'{k}: {p_:.3f}/{o:.3f}' for k, n, p_, o in c['by_value_decile']))
        L += ['', '| rating (recalibrated V) | mean V at resignation | targeting efficiency | AUC | resignations in upper half | hazard by decile of recalibrated V |', '|---|---|---|---|---|---|']
        for b in BL:
            if b in S['recalibrated_by_band']:
                v = S['recalibrated_by_band'][b]; L.append(f"| {b} | {v['mean_V_at_resignation']:.3f} | {v['targeting_efficiency']:.3f} | {v['auc']:.3f} | {v['share_of_resignations_in_upper_half_of_value']:.3f} | " + ' '.join(f'{h[2]:.4f}' for h in v['hazard_by_value_decile']) + ' |')
        L += ['', 'Value model calibration on positions that were played on (decile, n, predicted, realised): ' + '; '.join(f'{k}: {p_:.3f}/{o:.3f}' for k, n, p_, o in S['value_model_calibration']), '']
    open(a.out + '.md', 'w').write('\n'.join(L)); print(f'[skill] wrote {a.out}.json and .md', file=sys.stderr)


# ---------------------------------------------------------------- rotation tests (added after the second simulated review)
def rot(a):
    """Level versus rotation with (i) a continuation value that does not count later resignations as losses,
    (ii) a logit with band-specific intercepts and slopes, with and without a common floor, (iii) controls for the
    expected number of remaining plies and for forced mates, (iv) within-player odds ratios."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from scipy.optimize import minimize
    fs = sorted(glob.glob(os.path.join(a.dir, 'hazard_parts', 'hazard_*.parquet')))
    NB = 50; NG = 40; rng = np.random.default_rng(29)
    R = {'note': 'EXPLORATORY. V_U: cross-fitted value of playing on, trained on at-risk positions of games that the player did not end by resigning. '
                 'x = ln(V_U + 0.02). Logit: h = floor + (1 - floor) * Lambda(a_band + s_band * x [+ controls]). Cells: rating band x 50 quantile bins of V_U. '
                 'Intervals: 99%, bootstrap over 40 hash groups of players (500 replications).', 'speeds': {}}
    sig = lambda z: 1 / (1 + np.exp(-z))
    def fit(n, e, x, nb, slopes='band', floor=False, extra=None, init=None):
        """n, e, x: arrays [band, bin(, k)]; returns params and deviance. extra: number of additive shift groups along the last axis."""
        B = n.shape[0]; K = n.shape[2] if n.ndim == 3 else 1
        n3 = n.reshape(B, -1, K); e3 = e.reshape(B, -1, K); x3 = x.reshape(B, -1, K)
        ns = B if slopes == 'band' else 1; npar = B + ns + (K - 1 if extra else 0) + (1 if floor else 0)
        def unpack(t):
            ab = t[:B]; sl = t[B:B + ns] if ns == B else np.repeat(t[B], B); k0 = B + ns
            sh = np.r_[0.0, t[k0:k0 + K - 1]] if extra else np.zeros(K); k0 += (K - 1 if extra else 0)
            fl = sig(t[k0]) * 0.05 if floor else 0.0; return ab, sl, sh, fl
        def nll(t):
            ab, sl, sh, fl = unpack(t); z = ab[:, None, None] + sl[:, None, None] * x3 + sh[None, None, :]
            h = np.clip(fl + (1 - fl) * sig(z), 1e-12, 1 - 1e-12); return -(e3 * np.log(h) + (n3 - e3) * np.log(1 - h)).sum()
        t0 = init if init is not None else np.r_[np.full(B, -6.0), np.full(ns, -1.0), np.zeros(K - 1 if extra else 0), ([-3.0] if floor else [])]
        r = minimize(nll, t0, method='L-BFGS-B'); ab, sl, sh, fl = unpack(r.x)
        return {'a': ab, 's': sl, 'shift': sh, 'floor': float(fl), 'nll': float(r.fun), 'x': r.x}
    for sp in SPEEDS:
        d = pd.concat((pd.read_parquet(f, filters=[('speed', '==', sp)]) for f in fs), ignore_index=True)
        if len(d) < 5000: continue
        d['fold'] = pd.factorize(d.gid)[0] % 5; X = d[VF].astype('float32')
        if 'arena' not in d.columns: d['arena'] = -1          # months extracted before the tournament flag existed
        own_res = ((d.cls == 'resign') & (d.y == 0)).values           # the game ended by this player's resignation
        d['VU'] = np.float32(np.nan); d['VL'] = np.float32(np.nan); d['That'] = np.float32(np.nan)
        for k in range(5):
            te = np.flatnonzero((d.fold == k).values)
            for col, mask, target in (('VU', (d.fold != k).values & ~own_res, 'y'), ('VL', (d.fold != k).values & (d.event == 0).values, 'y'), ('That', (d.fold != k).values & ~own_res, 'plies_left')):
                tr = np.flatnonzero(mask)
                if len(tr) > 1200000: tr = rng.choice(tr, 1200000, replace=False)
                m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.1, max_leaf_nodes=63, min_samples_leaf=200, l2_regularization=1.0, random_state=29).fit(X.iloc[tr], d[target].values[tr])
                pr = m.predict(X.iloc[te]); d.iloc[te, d.columns.get_loc(col)] = (np.clip(pr, 0, 1) if target == 'y' else np.clip(pr, 0, None)).astype('float32')
        d['band'] = band(d.elo.values); S = {'n_positions': int(len(d)), 'n_events': int(d.event.sum())}
        nr = d[~own_res]; S['VU_calibration_by_band'] = {BL[b]: [[int(k), int(len(x)), float(x.VU.mean()), float(x.y.mean())] for k, x in g.groupby(pd.qcut(g.VU, 10, labels=False, duplicates='drop'))] for b, g in nr.groupby('band')}
        S['mean_VU_by_band'] = {BL[b]: float(g.VU.mean()) for b, g in d.groupby('band')}; S['mean_VL_by_band'] = {BL[b]: float(g.VL.mean()) for b, g in d.groupby('band')}
        # registered calibration gate: if any of the 10 bins in any band is off by more than 0.03, V_U is recalibrated by isotonic regression within band and that version decides
        gap = max(abs(p_ - y_) for v_ in S['VU_calibration_by_band'].values() for k_, n_, p_, y_ in v_); S['calibration_gate'] = {'max_gap': float(gap), 'threshold': 0.03, 'tripped': bool(gap > 0.03)}
        if gap > 0.03:
            from sklearn.isotonic import IsotonicRegression
            d['VUr'] = d.VU.astype('float64')
            for b, g in nr.groupby('band'):
                iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds='clip').fit(g.VU.values.astype('float64'), g.y.values.astype('float64'))
                mb = (d.band == b).values; d.loc[mb, 'VUr'] = iso.predict(d.VU.values[mb].astype('float64'))
        NREP = int(os.environ.get('HAZARD_BOOT', '500'))
        def run(dd, vname):
            v = dd[vname].values.astype('float64'); qb = np.quantile(v, np.linspace(0, 1, NB + 1)[1:-1]); vb = np.searchsorted(qb, v, side='right')
            tb = np.searchsorted(np.quantile(dd.That.values, [1 / 3, 2 / 3]), dd.That.values, side='right'); grp = (dd.player.values % np.uint64(NG)).astype(int)
            idx = ((((grp * 4 + dd.band.values) * NB + vb) * 3 + tb) * 2 + dd.mate_against.values).astype(np.int64); size = NG * 4 * NB * 3 * 2
            n = np.bincount(idx, minlength=size).reshape(NG, 4, NB, 3, 2).astype('float64'); e = np.bincount(idx, weights=dd.event.values, minlength=size).reshape(NG, 4, NB, 3, 2)
            sx = np.bincount(idx, weights=np.log(v + 0.02), minlength=size).reshape(NG, 4, NB, 3, 2)
            def models(w, ws=None):
                g_ = (lambda k: ws[k]['x']) if ws is not None else (lambda k: None)
                nn = np.tensordot(w, n, 1); ee = np.tensordot(w, e, 1); xx = np.tensordot(w, sx, 1)
                def agg(axes): N = nn.sum(axes); return N, ee.sum(axes), xx.sum(axes) / np.maximum(N, 1)
                N, E, Xm = agg((2, 3)); out = {}
                m0 = fit(N, E, Xm, NB, slopes='common', init=g_('level_only')); m1 = fit(N, E, Xm, NB, init=g_('rotation'))
                m2 = fit(N, E, Xm, NB, floor=True, init=g_('rotation_floor') if ws is not None else np.r_[m1['x'], -3.0])
                out['level_only'] = m0; out['rotation'] = m1; out['rotation_floor'] = m2
                N3, E3, X3 = agg(3); out['rotation_T_control'] = fit(N3, E3, X3, NB, extra=True, init=g_('rotation_T_control'))
                Nm, Em, Xs = nn[..., 0].sum(2), ee[..., 0].sum(2), xx[..., 0].sum(2); out['rotation_no_mate'] = fit(Nm, Em, Xs / np.maximum(Nm, 1), NB, init=g_('rotation_no_mate'))
                out['rotation_1200plus'] = fit(N[1:], E[1:], Xm[1:], NB, init=g_('rotation_1200plus'))
                return out
            hr = lambda m, vv: float(sig(m['a'][3] + m['s'][3] * math.log(vv + 0.02)) / sig(m['a'][0] + m['s'][0] * math.log(vv + 0.02)))
            # exposure-standardised share of resignations in the upper half of value; never-resigning players
            dec = np.searchsorted(np.quantile(v, np.linspace(0.1, 0.9, 9)), v, side='right'); wts = np.bincount(dec, minlength=10) / len(v)
            i2 = (grp * 4 + dd.band.values) * 10 + dec; dn = np.bincount(i2, minlength=NG * 40).reshape(NG, 4, 10).astype('float64'); de_ = np.bincount(i2, weights=dd.event.values, minlength=NG * 40).reshape(NG, 4, 10)
            def std_share(w):
                hz = np.tensordot(w, de_, 1) / np.maximum(np.tensordot(w, dn, 1), 1); return (hz[:, 5:] * wts[5:]).sum(1) / np.maximum((hz * wts).sum(1), 1e-12), hz
            pl = dd.groupby('player').agg(ev=('event', 'sum'), n=('event', 'size'), b=('band', 'first')); pl = pl[pl.n >= 100]; pg = (pl.index.values % np.uint64(NG)).astype(int)
            pn = np.bincount(pg * 4 + pl.b.values, minlength=NG * 4).reshape(NG, 4).astype('float64'); p0 = np.bincount(pg * 4 + pl.b.values, weights=(pl.ev.values == 0), minlength=NG * 4).reshape(NG, 4)
            never = lambda w: (w @ p0) / np.maximum(w @ pn, 1)
            one = np.ones(NG); base = models(one); bs = {k: [] for k in base}; bfl = []; bhr = {0.05: [], 0.40: []}; bss = []; bnv = []
            for r_ in range(NREP):
                w = np.bincount(rng.integers(0, NG, NG), minlength=NG).astype('float64'); mm = models(w, base)
                for k in base: bs[k].append(mm[k]['s'])
                bfl.append(mm['rotation_floor']['floor'])
                for vv in bhr: bhr[vv].append(hr(mm['rotation'], vv))
                bss.append(std_share(w)[0]); bnv.append(never(w))
            ci = lambda x: [float(q) for q in np.percentile(x, [0.5, 99.5])]
            o = {'n_positions': int(len(dd)), 'n_events': int(dd.event.sum())}
            for k, m in base.items():
                arr = np.array(bs[k]); names = BL[1:] if k == 'rotation_1200plus' else BL
                o[k] = {'nll': m['nll'], 'floor': m['floor'], 'intercepts': [float(z) for z in m['a']],
                        'slopes': {names[j]: {'s': float(m['s'][j]), 'ci99': ci(arr[:, j])} for j in range(len(m['s']))}}
                if arr.shape[1] > 1: o[k]['slope_top_minus_bottom'] = {'d': float(m['s'][-1] - m['s'][0]), 'ci99': ci(arr[:, -1] - arr[:, 0])}
            o['rotation_floor']['floor_ci99'] = ci(bfl)
            m1 = base['rotation']; o['fitted_hazard_at_V'] = {str(vv): [float(sig(m1['a'][b] + m1['s'][b] * math.log(vv + 0.02))) for b in range(4)] for vv in (0.01, 0.05, 0.15, 0.40)}
            o['hazard_ratio_top_vs_bottom'] = {str(vv): {'ratio': hr(m1, vv), 'ci99': ci(bhr[vv])} for vv in bhr}
            ss, hz = std_share(one); bss = np.array(bss); bnv = np.array(bnv); nv = never(one)
            o['standardised_share_upper_half'] = {BL[b]: {'share': float(ss[b]), 'ci99': ci(bss[:, b])} for b in range(4)}
            o['standardised_share_bottom_minus_top'] = {'d': float(ss[0] - ss[3]), 'ci99': ci(bss[:, 0] - bss[:, 3])}
            o['never_resigning_share_100plus'] = {BL[b]: {'share': float(nv[b]), 'ci99': ci(bnv[:, b]), 'players': int(pn[:, b].sum())} for b in range(4)}
            o['never_resigning_bottom_minus_top'] = {'d': float(nv[0] - nv[3]), 'ci99': ci(bnv[:, 0] - bnv[:, 3])}
            o['hazard_by_value_decile'] = {BL[b]: [float(q) for q in hz[b]] for b in range(4)}
            o['auc'] = {BL[bb]: auc_low_value(v[gi], dd.event.values[gi]) for bb, gi in dd.groupby('band').indices.items()}
            # within-player Mantel-Haenszel odds ratio: resigning in the lowest fifth of value versus the upper half
            lowq, med = np.quantile(v, [0.2, 0.5]); z = pd.DataFrame({'p': dd.player.values, 'b': dd.band.values, 'low': v <= lowq, 'high': v > med, 'e': dd.event.values}); z = z[z.low | z.high]
            g = z.groupby(['b', 'p', 'low']).e.agg(['sum', 'size']).unstack('low').dropna()
            a_ = g[('sum', True)]; n1 = g[('size', True)]; c_ = g[('sum', False)]; n0 = g[('size', False)]; b_ = n1 - a_; d_ = n0 - c_; tot = n1 + n0; mh = {}
            for bb in range(4):
                if bb not in a_.index.get_level_values(0): continue
                A_, B_, C_, D_, T_ = (q.loc[bb].values for q in (a_, b_, c_, d_, tot)); num = A_ * D_ / T_; den = B_ * C_ / T_; gp = (a_.loc[bb].index.values % np.uint64(NG)).astype(int)
                nu = np.bincount(gp, weights=num, minlength=NG); dn_ = np.bincount(gp, weights=den, minlength=NG); bsr = []
                for r_ in range(NREP):
                    w = np.bincount(rng.integers(0, NG, NG), minlength=NG); bsr.append((w @ nu) / max(w @ dn_, 1e-12))
                mh[BL[bb]] = {'or': float(num.sum() / den.sum()), 'ci99': ci(bsr), 'players': int(len(A_))}
            o['within_player_or_low_vs_high_value'] = mh
            return o
        res = {'VU': run(d, 'VU'), 'VL': run(d, 'VL')}
        if 'VUr' in d.columns: res['VU_recal'] = run(d, 'VUr')
        if (d.arena == 1).any(): res['VU_no_arena'] = run(d[d.arena == 0].reset_index(drop=True), 'VU')
        res['VU_eval_le_-4'] = run(d[d.cp <= -400].reset_index(drop=True), 'VU')
        clean = d[(d.berserk == 0) & (d.rd_abs >= 0) & (d.rd_abs <= 20)].reset_index(drop=True); res['VU_no_berserk_no_provisional'] = run(clean, 'VU')
        # K6: opponent clock, player fixed effects
        d['opp_weaker_100'] = d.elo_diff / 100.0; d['ln_clk_opp'] = np.log(d.clk_opp + 1.0); d['ln_clk'] = np.log(d.clk + 1.0); d['drop2_p'] = d.drop2 / 100.0; d['dur10'] = np.minimum(d.dur, 60) / 10.0; d['ply10'] = d.ply / 10.0
        d['eb'] = ebin(d); d['matdiff'] = (d.mat - d.mat_opp).clip(-15, 5); d['cell'] = d.eb.astype(str) + '_' + d.stm.astype(str) + '_' + d.matdiff.astype(str) + '_' + (d.mat + d.mat_opp > 30).astype(int).astype(str)
        dfe = d[d.groupby('player').player.transform('size') >= 5]; f6 = fe_ols(dfe, 'event', ['opp_weaker_100', 'ln_clk_opp', 'ln_clk', 'drop2_p', 'dur10', 'ply10'], 'cell', fe=True); hz_ = float(d.event.mean())
        res['clock'] = {'coef_ln_clk_opp': f6['ln_clk_opp'], 'hazard': hz_, 'relative_effect_of_halving': -math.log(2) * f6['ln_clk_opp']['b'] / hz_,
                        'relative_effect_ci99': sorted([-math.log(2) * f6['ln_clk_opp']['ci99'][0] / hz_, -math.log(2) * f6['ln_clk_opp']['ci99'][1] / hz_])}
        # registered decisions (confirmatory months only; computed for every month for transparency)
        o = res['VU_recal'] if 'VU_recal' in res else res['VU']; D = {}; S['calibration_gate']['decisions_based_on'] = 'VU_recal' if 'VU_recal' in res else 'VU'
        D['K1_level'] = bool(all(o['hazard_ratio_top_vs_bottom'][k]['ci99'][0] > 1.3 for k in ('0.05', '0.4')))
        D['K2_no_steeper_slope_for_strong'] = bool(o['rotation']['slope_top_minus_bottom']['ci99'][0] > -0.10)
        D['K3_everyone_discriminates'] = bool(all(q['ci99'][0] > 5 for q in o['within_player_or_low_vs_high_value'].values()) and len(o['within_player_or_low_vs_high_value']) == 4)
        D['K4_no_targeting_gradient'] = bool(-0.05 < o['standardised_share_bottom_minus_top']['ci99'][0] and o['standardised_share_bottom_minus_top']['ci99'][1] < 0.05)
        D['K5_extensive_margin'] = bool(o['never_resigning_bottom_minus_top']['ci99'][0] > 0.15)
        D['K6_clock'] = bool(res['clock']['relative_effect_ci99'][1] < -0.15)
        res['decisions'] = D
        S.update(res); R['speeds'][sp] = S
        print(f'[rot] {sp}: {len(d):,} positions done', file=sys.stderr, flush=True)
    json.dump(R, open(a.out + '.json', 'w'), indent=1)
    cc = None
    try:
        c = pd.read_csv(os.path.join(a.dir, 'cell_counts.csv')); t = c[c.cls != 'draw'].groupby(['speed', 'band']).n.sum(); r = c[c.cls == 'resign'].groupby(['speed', 'band']).n.sum()
        cc = {sp: {b: float(r.get((sp, b), 0) / t[(sp, b)]) for b in BL if (sp, b) in t.index} for sp in SPEEDS}
        R['K7_share_of_decisive_games_ending_by_resignation'] = cc; R['K7_monotone'] = {sp: bool(all(np.diff([v[b] for b in BL if b in v]) > 0)) for sp, v in cc.items()}
        json.dump(R, open(a.out + '.json', 'w'), indent=1)
    except Exception as ex: print('[rot] cell_counts.csv not usable:', ex, file=sys.stderr)
    f2 = lambda q, k='ci99': f"[{q[k][0]:.3f}, {q[k][1]:.3f}]"
    L = ['# Level versus rotation\n', R['note'] + '\n']
    if cc: L += ['## K7: share of decisive games ending by resignation, by rating band (all games)\n'] + [f"- {sp}: " + ', '.join(f'{b} {v:.3f}' for b, v in cc[sp].items()) + f" (monotone: {R['K7_monotone'][sp]})" for sp in cc] + ['']
    for sp, S in R['speeds'].items():
        L += [f'## {sp}\n', 'Decisions: ' + ', '.join(f'{k}={v}' for k, v in S['decisions'].items()), '',
              f"Opponent clock halved: hazard {S['clock']['relative_effect_of_halving']:+.1%} of its mean, 99% interval [{S['clock']['relative_effect_ci99'][0]:+.1%}, {S['clock']['relative_effect_ci99'][1]:+.1%}]\n"]
        for vname in [k for k in ('VU', 'VU_recal', 'VL', 'VU_no_arena', 'VU_eval_le_-4', 'VU_no_berserk_no_provisional') if k in S]:
            o = S[vname]; L += [f"### {vname} ({o['n_positions']:,} positions, {o['n_events']:,} resignations)\n", '| model | NLL | floor | slope <1200 | 1200-1599 | 1600-1999 | 2000+ | top minus bottom |', '|---|---|---|---|---|---|---|---|']
            for k in ('level_only', 'rotation', 'rotation_floor', 'rotation_T_control', 'rotation_no_mate', 'rotation_1200plus'):
                m = o[k]; sl = [f"{m['slopes'][b]['s']:.3f} {f2(m['slopes'][b])}" if b in m['slopes'] else '-' for b in BL]
                tb = f"{m['slope_top_minus_bottom']['d']:.3f} {f2(m['slope_top_minus_bottom'])}" if 'slope_top_minus_bottom' in m else '-'
                L.append(f"| {k} | {m['nll']:.0f} | {m['floor']:.5f} | " + ' | '.join(sl) + f' | {tb} |')
            L += ['', 'Hazard ratio 2000+ versus <1200 (rotation model): ' + '; '.join(f"V={vv}: {q['ratio']:.2f} {f2(q)}" for vv, q in o['hazard_ratio_top_vs_bottom'].items()),
                  'Fitted hazard at V = 0.01, 0.05, 0.15, 0.40 by band: ' + '; '.join(f"{vv}: " + ' '.join(f'{q:.4f}' for q in hz) for vv, hz in o['fitted_hazard_at_V'].items()),
                  'Within-player odds ratio, lowest fifth of value versus upper half: ' + '; '.join(f"{b}: {q['or']:.1f} {f2(q)} ({q['players']:,} players)" for b, q in o['within_player_or_low_vs_high_value'].items()),
                  'Standardised share of resignations in the upper half of value: ' + '; '.join(f"{b}: {q['share']:.3f} {f2(q)}" for b, q in o['standardised_share_upper_half'].items()) + f"; bottom minus top {o['standardised_share_bottom_minus_top']['d']:.3f} {f2(o['standardised_share_bottom_minus_top'])}",
                  'Players with 100+ at-risk positions who never resign: ' + '; '.join(f"{b}: {q['share']:.3f} {f2(q)} (n={q['players']:,})" for b, q in o['never_resigning_share_100plus'].items()) + f"; bottom minus top {o['never_resigning_bottom_minus_top']['d']:.3f} {f2(o['never_resigning_bottom_minus_top'])}",
                  'AUC: ' + '; '.join(f'{b}: {q:.3f}' for b, q in o['auc'].items()), '']
        L += [f"Calibration gate: largest gap {S['calibration_gate']['max_gap']:.3f} (threshold 0.03, tripped: {S['calibration_gate']['tripped']}); decisions based on {S['calibration_gate']['decisions_based_on']}", '', 'V_U calibration by band, largest gap over 10 quantile bins: ' + '; '.join(f"{b}: {max(abs(p_ - y_) for k, n, p_, y_ in v):.3f}" for b, v in S['VU_calibration_by_band'].items()), '']
    open(a.out + '.md', 'w').write('\n'.join(L)); print(f'[rot] wrote {a.out}.json and .md', file=sys.stderr)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--model', action='store_true'); ap.add_argument('--skill', action='store_true'); ap.add_argument('--rot', action='store_true'); ap.add_argument('--out', default='04_output/hazard')
    a = ap.parse_args()
    rot(a) if a.rot else skill(a) if a.skill else model(a) if a.model else extract(a)
