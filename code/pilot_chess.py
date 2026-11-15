#!/usr/bin/env python3
"""E4 chess pilot: resignation calibration on a Lichess monthly dump (stdin, PGN).

Usage (streamed, nothing large is written to disk):
  curl -sL https://database.lichess.org/standard/lichess_db_standard_rated_2026-10.pgn.zst \
    | head -c 1000000000 | zstdcat 2>/dev/null \
    | python3 02_code/pilot_chess.py --out 04_output/pilot_chess --rows 03_work/chess_resign_rows.csv

Standard library only. Resignation is INFERRED:
  Termination == "Normal" and decisive result and last SAN has no '#'.
Check the inference with validate_termination.py (Lichess API `status`).
"""
import sys, re, json, math, csv, argparse, collections, datetime, os

HDR = re.compile(r'\[(\w+) "(.*)"\]')
PAIR = re.compile(r'([^\s{}]+)\s*\{([^}]*)\}')
EVAL = re.compile(r'%eval (#?-?\d+(?:\.\d+)?)')
CLK = re.compile(r'%clk (\d+):(\d+):(\d+)')
MATE = 100000

def speed_of(tc):
    if not tc or tc == '-': return None
    try:
        b, i = tc.split('+'); est = int(b) + 40 * int(i)
    except Exception: return None
    if est < 30: return 'ultrabullet'
    if est < 180: return 'bullet'
    if est < 480: return 'blitz'
    if est < 1500: return 'rapid'
    return 'classical'

def band_of(e):
    return '<1200' if e < 1200 else '1200-1599' if e < 1600 else '1600-1999' if e < 2000 else '2000+'

def bin_of(cp):
    if cp >= MATE: return 'M+'
    if cp <= -MATE: return 'M-'
    c = max(-2000, min(1999, cp))
    return int(math.floor(c / 100.0)) * 100

def lichess_win(cp):
    if cp >= MATE: return 1.0
    if cp <= -MATE: return 0.0
    return 0.5 + 0.5 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='04_output/pilot_chess')
    ap.add_argument('--rows', default='03_work/chess_resign_rows.csv')
    ap.add_argument('--ids', default='03_work/chess_ids_for_validation.csv')
    ap.add_argument('--minply', type=int, default=10)
    a = ap.parse_args()
    for p in (a.out, a.rows, a.ids):
        d = os.path.dirname(p)
        if d: os.makedirs(d, exist_ok=True)

    comp = collections.Counter()          # (has_eval, speed, cls) -> n
    comp_elo = collections.Counter(); comp_ply = collections.Counter()
    loss = collections.Counter()          # (speed, band, prev, resigned?) all games
    cA = collections.defaultdict(lambda: [0.0, 0]); cB = collections.defaultdict(lambda: [0.0, 0])
    rows = []; pers = collections.defaultdict(list)   # trailing hopeless plies by (speed, cls)
    last = {}; ids = collections.defaultdict(list)
    n_games = 0; first_dt = last_dt = None

    def game(h, mt):
        nonlocal n_games, first_dt, last_dt
        sp = speed_of(h.get('TimeControl'))
        if sp is None: return
        try: we, be = int(h['WhiteElo']), int(h['BlackElo'])
        except Exception: return
        res = h.get('Result'); term = h.get('Termination', '')
        pairs = PAIR.findall(mt); nply = len(pairs)
        if nply == 0: return
        n_games += 1
        dt = h.get('UTCDate', '') + ' ' + h.get('UTCTime', '')
        try: t = datetime.datetime.strptime(dt, '%Y.%m.%d %H:%M:%S').timestamp()
        except Exception: t = None
        if first_dt is None: first_dt = dt
        last_dt = dt
        lastsan = pairs[-1][0]
        if res == '1/2-1/2': cls = 'draw'
        elif res not in ('1-0', '0-1'): cls = 'other'
        elif term == 'Time forfeit': cls = 'time'
        elif term == 'Normal': cls = 'mate' if '#' in lastsan else 'resign'
        else: cls = 'other'
        has_eval = '%eval' in mt
        k = (has_eval, sp, cls); comp[k] += 1; comp_elo[k] += (we + be) / 2; comp_ply[k] += nply
        gid = h.get('Site', '').rsplit('/', 1)[-1]
        if len(ids[cls]) < 1000 and n_games % 37 == 0: ids[cls].append(gid)
        band = band_of((we + be) / 2)
        wscore = 1.0 if res == '1-0' else 0.0 if res == '0-1' else 0.5
        # previous-game outcome within 60 min (any speed), then update
        prev = {}
        for name, lost in ((h.get('White'), res == '0-1'), (h.get('Black'), res == '1-0')):
            p = last.get(name)
            prev[name] = 'none' if (p is None or t is None or t - p[0] > 3600) else ('prevloss' if p[1] else 'prevnonloss')
            if t is not None: last[name] = (t, lost)
        loser = None
        if cls in ('resign', 'mate', 'time'):
            loser = 'w' if res == '0-1' else 'b'
            lname = h.get('White') if loser == 'w' else h.get('Black')
            if nply >= a.minply: loss[(sp, band, prev[lname], cls == 'resign')] += 1
        if not has_eval: return
        evs = []
        for _, c in pairs:
            m = EVAL.search(c)
            if not m: evs.append(None); continue
            s = m.group(1)
            if s[0] == '#': evs.append(-MATE if '-' in s else MATE)
            else: evs.append(int(round(float(s) * 100)))
        for i in range(8, nply, 3):
            e = evs[i]
            if e is None: continue
            for x, y in ((e, wscore), (-e, 1 - wscore)):
                kk = (sp, band, bin_of(x)); cA[kk][0] += y; cA[kk][1] += 1
                if cls != 'resign': cB[kk][0] += y; cB[kk][1] += 1
        if loser is None or nply < a.minply: return
        sgn = 1 if loser == 'w' else -1
        trail = 0
        for e in reversed(evs):
            if e is None: continue
            if sgn * e <= -700: trail += 1
            else: break
        pers[(sp, cls)].append(trail)
        if cls != 'resign': return
        fe = next((e for e in reversed(evs) if e is not None), None)
        if fe is None: return
        cpl = sgn * fe
        clk = {}
        for i in range(nply - 1, max(nply - 3, -1), -1):
            m = CLK.search(pairs[i][1])
            if m: clk['w' if i % 2 == 0 else 'b'] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        lelo, oelo = (we, be) if loser == 'w' else (be, we)
        rows.append([gid, sp, band, lelo, oelo, nply, cpl, clk.get(loser), clk.get('b' if loser == 'w' else 'w'),
                     prev[lname], trail, 1 if (nply % 2 == 0) == (loser == 'w') else 0])

    h = {}
    for line in sys.stdin:
        if line.startswith('['):
            m = HDR.match(line)
            if m: h[m.group(1)] = m.group(2)
        elif line.startswith('1.'):
            try: game(h, line)
            except Exception: pass
            h = {}
        elif line.strip() and not line[0].isdigit():
            h = {}

    def es(curve, sp, band, cp):
        v = curve.get((sp, band, bin_of(cp)))
        return (v[0] / v[1]) if v and v[1] >= 30 else None

    out = []
    for r in rows:
        out.append(r + [round(lichess_win(r[6]), 4), es(cA, r[1], r[2], r[6]), es(cB, r[1], r[2], r[6])])
    with open(a.rows, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['game_id', 'speed', 'band', 'loser_elo', 'opp_elo', 'nply', 'cp_loser', 'clk_loser', 'clk_opp',
                    'prev', 'trail_hopeless_plies', 'loser_to_move', 'lichess_win', 'es_all', 'es_played_on'])
        w.writerows(out)
    with open(a.ids, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['game_id', 'inferred'])
        for c, lst in ids.items():
            for g in lst: w.writerow([g, c])

    def share(xs, f):
        xs = [x for x in xs if x is not None]
        return (sum(1 for x in xs if f(x)) / len(xs)) if xs else float('nan')
    def med(xs):
        xs = sorted(xs); return xs[len(xs) // 2] if xs else float('nan')
    def block(rs):
        return {
            'n': len(rs),
            'median_cp_loser': med([r[6] for r in rs if abs(r[6]) < MATE]),
            'share_mate_against': share([r[6] for r in rs], lambda x: x <= -MATE),
            'share_cp_ge_-300': share([r[6] for r in rs], lambda x: x >= -300),
            'share_cp_ge_-100': share([r[6] for r in rs], lambda x: x >= -100),
            'mean_lichess_win': sum(r[12] for r in rs) / len(rs) if rs else float('nan'),
            'ES_played_on>=0.05': share([r[14] for r in rs], lambda x: x >= 0.05),
            'ES_played_on>=0.10': share([r[14] for r in rs], lambda x: x >= 0.10),
            'ES_played_on>=0.20': share([r[14] for r in rs], lambda x: x >= 0.20),
            'ES_all>=0.10': share([r[13] for r in rs], lambda x: x >= 0.10),
            'ES_all>=0.20': share([r[13] for r in rs], lambda x: x >= 0.20),
            'n_with_curve': sum(1 for r in rs if r[14] is not None),
        }
    S = {'n_games': n_games, 'first': first_dt, 'last': last_dt, 'minply': a.minply}
    tot = sum(comp.values()); ev = sum(v for k, v in comp.items() if k[0])
    S['eval_share'] = ev / tot if tot else None
    S['composition'] = [{'has_eval': k[0], 'speed': k[1], 'cls': k[2], 'n': v,
                         'mean_elo': round(comp_elo[k] / v), 'mean_ply': round(comp_ply[k] / v, 1)} for k, v in sorted(comp.items(), key=str)]
    S['resign_overall'] = block(out)
    S['resign_by_speed'] = {s: block([r for r in out if r[1] == s]) for s in sorted({r[1] for r in out})}
    S['resign_by_band'] = {b: block([r for r in out if r[2] == b]) for b in sorted({r[2] for r in out})}
    S['resign_by_prev'] = {p: block([r for r in out if r[9] == p]) for p in sorted({r[9] for r in out})}
    S['resign_by_clock'] = {lab: block([r for r in out if r[7] is not None and lo <= r[7] < hi])
                            for lab, lo, hi in (('<10s', 0, 10), ('10-29s', 10, 30), ('30s+', 30, 10**9))}
    pl = collections.defaultdict(lambda: [0, 0])
    for (sp, band, prev, rz), v in loss.items():
        pl[(sp, prev)][0] += v if rz else 0; pl[(sp, prev)][1] += v
    S['p_resign_given_loss_all_games'] = {f'{k[0]}|{k[1]}': {'n_loss': v[1], 'p_resign': round(v[0] / v[1], 4)} for k, v in sorted(pl.items())}
    S['hopeless_persistence'] = {f'{k[0]}|{k[1]}': {'n': len(v), 'share_trail>=10plies': round(share(v, lambda x: x >= 10), 4),
                                                   'share_trail>=20plies': round(share(v, lambda x: x >= 20), 4),
                                                   'median_trail': med(v)} for k, v in sorted(pers.items())}
    json.dump(S, open(a.out + '.json', 'w'), indent=1, default=str)
    with open(a.out + '.md', 'w') as f:
        f.write(f"# Chess pilot summary\n\ngames parsed: {n_games} ({first_dt} .. {last_dt}); eval share: {S['eval_share']:.4f}\n\n")
        f.write("## Composition (eval vs no eval)\n\n| eval | speed | class | n | mean Elo | mean plies |\n|---|---|---|---|---|---|\n")
        for c in S['composition']:
            f.write(f"| {c['has_eval']} | {c['speed']} | {c['cls']} | {c['n']} | {c['mean_elo']} | {c['mean_ply']} |\n")
        for title, key in (('Resignations, overall', None), ('by speed', 'resign_by_speed'), ('by rating band', 'resign_by_band'),
                           ('by previous game (60 min)', 'resign_by_prev'), ('by loser clock', 'resign_by_clock')):
            d = {'all': S['resign_overall']} if key is None else S[key]
            f.write(f"\n## {title}\n\n")
            cols = list(S['resign_overall'].keys())
            f.write('| group | ' + ' | '.join(cols) + ' |\n|' + '---|' * (len(cols) + 1) + '\n')
            for g, b in d.items():
                f.write(f'| {g} | ' + ' | '.join(f'{b[c]:.3f}' if isinstance(b[c], float) else str(b[c]) for c in cols) + ' |\n')
        f.write("\n## P(resign | loss), all games\n\n```\n" + json.dumps(S['p_resign_given_loss_all_games'], indent=1) + "\n```\n")
        f.write("\n## Trailing plies at loser eval <= -7.00 before the end\n\n```\n" + json.dumps(S['hopeless_persistence'], indent=1) + "\n```\n")
    print(open(a.out + '.md').read())

if __name__ == '__main__':
    main()
