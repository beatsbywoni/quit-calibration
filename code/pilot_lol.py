#!/usr/bin/env python3
"""E4 LoL pilot: win probability of the surrendering team at the moment of surrender.
  python3 02_code/pilot_lol.py 01_raw/lol 04_output/pilot_lol.md       (needs numpy)
Model: logistic regression on per-minute states (gold, xp, towers, dragons, barons, inhibitors, kills, minute).
  B = fitted on games that did NOT end in surrender (upper bound for the surrendering side)
  A = fitted on all games, surrenders counted as losses (lower bound)"""
import sys, os, json, gzip, glob, collections, zlib
import numpy as np
src, outp = sys.argv[1], sys.argv[2]
tier = {}
tf = os.path.join(src, '_match_tier.jsonl')
if os.path.exists(tf):
    for l in open(tf): d = json.loads(l); tier[d['match']] = d['tier']
def feats(fr, cum, minute):
    g = x = 0
    for pid, pf in fr['participantFrames'].items():
        s = 1 if int(pid) <= 5 else -1; g += s * pf.get('totalGold', 0); x += s * pf.get('xp', 0)
    return [1.0, g / 1000, x / 1000, cum['tower'], cum['dragon'], cum['baron'], cum['inhib'], cum['kill'], minute / 10, g / 1000 * minute / 10]
X = {'A': [], 'B': []}; Y = {'A': [], 'B': []}; H = []; sur = []; etypes = collections.Counter(); cross = collections.Counter(); ng = 0
for fn in glob.glob(os.path.join(src, '*.json.gz')):
    try: d = json.load(gzip.open(fn, 'rt'))
    except Exception: continue
    info = d['match']['info']; ps = info['participants']; dur = info.get('gameDuration', 0)
    fs = any(p.get('gameEndedInSurrender') for p in ps); fe = any(p.get('gameEndedInEarlySurrender') for p in ps)
    cross[(fs, fe, 'dur<5m' if dur < 300 else '5-15m' if dur < 900 else '15-20m' if dur < 1200 else '20m+')] += 1
    if info.get('queueId') != 420 or dur < 300 or fe: continue
    ng += 1
    w100 = 1.0 if any(p['teamId'] == 100 and p['win'] for p in ps) else 0.0
    cum = dict(tower=0, dragon=0, baron=0, inhib=0, kill=0); frames = d['timeline']['info']['frames']; mid = d['match']['metadata']['matchId']
    hold = zlib.crc32(mid.encode()) % 5 == 0; last = None
    for i, fr in enumerate(frames):
        for ev in fr.get('events', []):
            t = ev.get('type'); etypes[t] += 1
            if t == 'BUILDING_KILL':
                s = 1 if ev.get('teamId') == 200 else -1
                if ev.get('buildingType') == 'TOWER_BUILDING': cum['tower'] += s
                elif ev.get('buildingType') == 'INHIBITOR_BUILDING': cum['inhib'] += s
            elif t == 'ELITE_MONSTER_KILL':
                s = 1 if ev.get('killerTeamId') == 100 else -1
                if ev.get('monsterType') == 'DRAGON': cum['dragon'] += s
                elif ev.get('monsterType') == 'BARON_NASHOR': cum['baron'] += s
            elif t == 'CHAMPION_KILL':
                k = ev.get('killerId', 0)
                if k: cum['kill'] += 1 if k <= 5 else -1
        f = feats(fr, cum, i); last = f
        if i >= 5 and i < len(frames) - 1:
            if hold and not fs: H.append((f, w100))
            elif not hold:
                X['A'].append(f); Y['A'].append(w100)
                if not fs: X['B'].append(f); Y['B'].append(w100)
    if fs and last is not None: sur.append((last, w100, dur, tier.get(mid, '?')))
def fit(Xm, y, it=50):
    Xm = np.array(Xm); y = np.array(y); mu = Xm.mean(0); sd = Xm.std(0); mu[0] = 0; sd[0] = 1; sd[sd == 0] = 1
    Z = (Xm - mu) / sd; b = np.zeros(Z.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-Z @ b)); W = p * (1 - p) + 1e-9
        b = b + np.linalg.solve(Z.T @ (Z * W[:, None]) + 1e-3 * np.eye(Z.shape[1]), Z.T @ (y - p))
    return lambda F: 1 / (1 + np.exp(-((np.array(F) - mu) / sd) @ b))
L = [f'# LoL pilot summary\n\nranked-solo games used: {ng}; surrendered: {len(sur)} ({len(sur) / max(ng, 1):.3f})\n',
     '## Flags x duration (all files; check what gameEndedInEarlySurrender means)\n', '| surrender | earlySurrender | duration | n |', '|---|---|---|---|']
L += [f'| {k[0]} | {k[1]} | {k[2]} | {v} |' for k, v in sorted(cross.items(), key=str)]
L += ['\n## Timeline event types seen (is there any surrender-vote event?)\n', '```', json.dumps(dict(etypes.most_common()), indent=1), '```']
if len(X['B']) > 500 and sur:
    for name in ('B', 'A'):
        m = fit(X[name], Y[name]); F = [s[0] for s in sur]; p100 = m(F)
        ps = np.array([p if s[1] == 0 else 1 - p for p, s in zip(p100, sur)])   # P(win) of the surrendering (losing) side
        L += [f'\n## Model {name} ({"non-surrender games only" if name == "B" else "all games"}): P(win) of surrendering team at the last frame\n',
              f'n = {len(ps)}; mean = {ps.mean():.4f}; median = {np.median(ps):.4f}',
              f'share >= 0.05: {(ps >= .05).mean():.4f}; >= 0.10: {(ps >= .10).mean():.4f}; >= 0.20: {(ps >= .20).mean():.4f}; >= 0.30: {(ps >= .30).mean():.4f}\n',
              '| group | n | mean p | share>=0.10 | share>=0.20 |', '|---|---|---|---|---|']
        grp = collections.defaultdict(list)
        for p, s in zip(ps, sur):
            grp['dur ' + ('<20m' if s[2] < 1200 else '20-25m' if s[2] < 1500 else '25m+')].append(p); grp['tier ' + s[3]].append(p)
        L += [f'| {g} | {len(v)} | {np.mean(v):.3f} | {np.mean(np.array(v) >= .1):.3f} | {np.mean(np.array(v) >= .2):.3f} |' for g, v in sorted(grp.items())]
        if H and name == 'B':
            ph = m([h[0] for h in H]); yh = np.array([h[1] for h in H]); L += ['\nHeld-out calibration (non-surrender games, team 100):\n', '| predicted | n | observed |', '|---|---|---|']
            for lo in np.arange(0, 1, .1):
                k = (ph >= lo) & (ph < lo + .1)
                if k.sum(): L.append(f'| {lo:.1f}-{lo + .1:.1f} | {k.sum()} | {yh[k].mean():.3f} |')
else: L.append('\nNot enough data to fit the model yet.')
open(outp, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
