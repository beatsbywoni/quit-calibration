#!/usr/bin/env python3
"""Check the inferred termination class against Lichess API `status` (ground truth).
Usage: python3 02_code/validate_termination.py 03_work/chess_ids_for_validation.csv 04_output/termination_validation.md
About 4,000 ids = 14 requests of 300 ids; a few minutes. Standard library only."""
import sys, csv, json, time, urllib.request, collections
EXPECT = {'resign': {'resign'}, 'mate': {'mate'}, 'time': {'outoftime', 'timeout'},
          'draw': {'draw', 'stalemate', 'outoftime', 'timeout'}, 'other': {'aborted', 'noStart', 'cheat', 'unknownFinish', 'timeout'}}
rows = list(csv.DictReader(open(sys.argv[1]))); inf = {r['game_id']: r['inferred'] for r in rows}
ids = list(inf); tab = collections.Counter(); got = 0
for i in range(0, len(ids), 300):
    req = urllib.request.Request('https://lichess.org/api/games/export/_ids?moves=false&tags=false',
                                 data=','.join(ids[i:i + 300]).encode(), method='POST',
                                 headers={'Accept': 'application/x-ndjson', 'Content-Type': 'text/plain',
                                          'User-Agent': 'quit-calibration-pilot (research; contact in repo)'})
    for attempt in range(5):
        try:
            body = urllib.request.urlopen(req, timeout=120).read().decode(); break
        except Exception as e:
            print('retry', e, file=sys.stderr); time.sleep(60)
    for line in body.splitlines():
        if not line.strip(): continue
        g = json.loads(line); tab[(inf.get(g['id'], '?'), g.get('status'))] += 1; got += 1
    time.sleep(2)
with open(sys.argv[2], 'w') as f:
    f.write(f'# Termination inference vs Lichess API status\n\nrequested {len(ids)}, returned {got}\n\n| inferred | api status | n | consistent |\n|---|---|---|---|\n')
    for (a, b), n in sorted(tab.items()):
        f.write(f'| {a} | {b} | {n} | {"yes" if b in EXPECT.get(a, set()) else "NO"} |\n')
    for c in ('resign', 'mate', 'time'):
        tot = sum(n for (a, b), n in tab.items() if a == c); ok = sum(n for (a, b), n in tab.items() if a == c and b in EXPECT[c])
        if tot: f.write(f'\nprecision of inferred "{c}": {ok}/{tot} = {ok / tot:.4f}\n')
print(open(sys.argv[2]).read())
