#!/usr/bin/env python3
"""Stage A of the confirmatory chess pipeline (preregistration v1.0, section 3). Standard library only.

Reads one Lichess monthly dump (PGN on stdin) once and writes compact intermediates, so the 30 GB dump
never has to be parsed again:
  eval_games.jsonl.gz        every game with server evaluations that passes the exclusions (all ending classes);
                             the last two fields are the recorded rating changes of White and Black
  losses_sample.csv.gz       every decisive game (any evaluation status) lost by a 10% hash sample of players (H4a)
  cell_counts.csv            game counts by speed x rating band x ending class x length bin x evaluation status (reweighting)
  noeval_resign_sample.jsonl.gz   reservoir sample of resignations without server evaluation (local-engine validation)
  validation_ids.csv         1,000 game ids per ending class for the Lichess API check
  manifest.json              counts, time span, options

Usage:  zstdcat 01_raw/lichess_db_standard_rated_2026-09.pgn.zst | python3 02_code/chess_stage_a.py --out 03_work/chess_2026-09
Player names are stored only as 64-bit hashes. Ending classes follow section 3.2 of the preregistration."""
import sys, os, re, json, gzip, csv, time, random, argparse, collections, datetime, hashlib
ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True); ap.add_argument('--minply', type=int, default=10)
ap.add_argument('--reservoir', type=int, default=60000); ap.add_argument('--seed', type=int, default=29)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); rng = random.Random(a.seed)
HDR = re.compile(r'\[(\w+) "(.*)"\]'); SPEEDS = ['bullet', 'blitz', 'rapid', 'classical']
def speed_of(tc):
    try: b, i = tc.split('+'); b = int(b); i = int(i)
    except Exception: return None, 0, 0
    est = b + 40 * i
    return (None if est < 30 else 'bullet' if est < 180 else 'blitz' if est < 480 else 'rapid' if est < 1500 else 'classical'), b, i
def band_of(e): return '<1200' if e < 1200 else '1200-1599' if e < 1600 else '1600-1999' if e < 2000 else '2000+'
def ph(name): return int.from_bytes(hashlib.blake2b(name.lower().encode(), digest_size=8).digest(), 'big')
ev_f = gzip.open(os.path.join(a.out, 'eval_games.jsonl.gz'), 'wt', compresslevel=3)
ls_f = gzip.open(os.path.join(a.out, 'losses_sample.csv.gz'), 'wt', compresslevel=3, newline=''); ls_w = csv.writer(ls_f)
ls_w.writerow(['loser', 'ts', 'speed', 'loser_elo', 'opp_elo', 'cls', 'nply', 'prev', 'has_eval'])
cells = collections.Counter(); last = {}; resv = []; n_noeval_res = 0; vids = collections.defaultdict(list); vseen = collections.Counter()
N = collections.Counter(); first = lastdt = None; t0 = time.time()
def game(h, mt):
    global n_noeval_res, first, lastdt
    N['seen'] += 1
    sp, base, inc = speed_of(h.get('TimeControl', ''))
    if sp is None: N['excl_speed'] += 1; return
    if h.get('WhiteTitle') == 'BOT' or h.get('BlackTitle') == 'BOT': N['excl_bot'] += 1; return
    try: we = int(h['WhiteElo']); be = int(h['BlackElo'])
    except Exception: N['excl_rating'] += 1; return
    term = h.get('Termination', ''); res = h.get('Result')
    if term not in ('Normal', 'Time forfeit'): N['excl_termination'] += 1; return
    nply = mt.count('{')
    i = mt.rfind('{')
    if i < 2: N['excl_nomoves'] += 1; return
    lastsan = mt[mt.rfind(' ', 0, i - 1) + 1:i - 1]
    if res == '1/2-1/2': cls = 'draw'
    elif res not in ('1-0', '0-1'): N['excl_result'] += 1; return
    elif term == 'Time forfeit': cls = 'time'
    else: cls = 'mate' if '#' in lastsan else 'resign'
    dt = h.get('UTCDate', '') + ' ' + h.get('UTCTime', '')
    try: ts = int(datetime.datetime.strptime(dt, '%Y.%m.%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp())
    except Exception: N['excl_date'] += 1; return
    if first is None: first = dt
    lastdt = dt
    si = SPEEDS.index(sp); wh = ph(h.get('White', '')); bh = ph(h.get('Black', ''))
    prev = []
    for p, lost in ((wh, res == '0-1'), (bh, res == '1-0')):      # previous game in the same speed class, started within 60 min
        k = p * 4 + si; v = last.get(k)
        prev.append('-' if v is None or ts - (v >> 1) > 3600 else ('L' if v & 1 else 'N'))
        last[k] = (ts << 1) | int(lost)
    if nply < a.minply: N['excl_short'] += 1; return
    N['kept'] += 1
    has_eval = '%eval' in mt
    cells[(sp, band_of((we + be) / 2), cls, min(nply // 10, 30), int(has_eval))] += 1
    gid = h.get('Site', '').rsplit('/', 1)[-1]
    vseen[cls] += 1
    if len(vids[cls]) < 1000: vids[cls].append(gid)
    else:
        j = rng.randrange(vseen[cls])
        if j < 1000: vids[cls][j] = gid
    if cls != 'draw':
        lw = res == '0-1'; lh = wh if lw else bh
        if lh % 10 == 0:
            ls_w.writerow([lh, ts, sp, we if lw else be, be if lw else we, cls, nply, prev[0] if lw else prev[1], int(has_eval)])
    def rd(k):
        try: return int(h.get(k, ''))
        except Exception: return None
    ev_tag = h.get('Event', '').lower(); arena = int(('tournament' in ev_tag) or ('swiss' in ev_tag) or ('arena' in ev_tag))     # added 2026-11-18: tournament games
    rec = [gid, wh, bh, we, be, res, cls, sp, base, inc, ts, prev[0], prev[1], mt.strip(), rd('WhiteRatingDiff'), rd('BlackRatingDiff'), arena]
    if has_eval:
        N['eval'] += 1; ev_f.write(json.dumps(rec, separators=(',', ':')) + '\n')
    elif cls == 'resign':
        n_noeval_res += 1
        if len(resv) < a.reservoir: resv.append(rec)
        else:
            j = rng.randrange(n_noeval_res)
            if j < a.reservoir: resv[j] = rec
h = {}
for line in sys.stdin:
    c = line[0]
    if c == '[':
        m = HDR.match(line)
        if m: h[m.group(1)] = m.group(2)
    elif c == '1' and line.startswith('1.'):
        try: game(h, line)
        except Exception: N['error'] += 1
        h = {}
        if N['seen'] % 2000000 == 0:
            el = time.time() - t0
            print(f"[stage A] {N['seen']:,} games, {N['eval']:,} with eval, {N['seen'] / el:,.0f} games/s, {el / 3600:.2f} h elapsed, at {lastdt}", file=sys.stderr, flush=True)
    elif line.strip(): h = {}                     # game without moves (result only)
ev_f.close(); ls_f.close()
with gzip.open(os.path.join(a.out, 'noeval_resign_sample.jsonl.gz'), 'wt') as f:
    for r in resv: f.write(json.dumps(r, separators=(',', ':')) + '\n')
with open(os.path.join(a.out, 'cell_counts.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['speed', 'band', 'cls', 'len_bin10', 'has_eval', 'n'])
    for k, v in sorted(cells.items()): w.writerow(list(k) + [v])
with open(os.path.join(a.out, 'validation_ids.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['game_id', 'inferred'])
    for c, lst in vids.items():
        for g in lst: w.writerow([g, c])
json.dump({'counts': dict(N), 'first': first, 'last': lastdt, 'noeval_resignations': n_noeval_res, 'reservoir': len(resv),
           'minply': a.minply, 'seed': a.seed, 'players_tracked': len(last), 'hours': round((time.time() - t0) / 3600, 3),
           'prev_rule': 'previous game of the same player in the same speed class that started within 3600 s',
           'loss_sample_rule': 'loser hash % 10 == 0'}, open(os.path.join(a.out, 'manifest.json'), 'w'), indent=1)
print(f"[stage A] done: {dict(N)}", file=sys.stderr)
