#!/usr/bin/env python3
"""E3/E4 LoL pilot collector (Riot API, standard library only).
  export RIOT_API_KEY=RGAPI-...      # development key lasts 24 h
  python3 02_code/lol_collect.py --platform kr --region asia --per-tier 25 --per-player 20 --out 01_raw/lol
Paces requests at 1.25 s (limit: 20/s and 100 per 2 min per region). Safe to stop and rerun (skips saved matches).
Default plan: 6 tiers x 25 players x 20 ranked-solo matches = about 3,000 matches, 2 requests each, about 2 hours.
Raw JSON stays local (Riot policy: no redistribution of raw data; publish aggregates and match ids only)."""
import os, sys, json, gzip, time, argparse, urllib.request, urllib.error, random
ap = argparse.ArgumentParser()
ap.add_argument('--platform', default='kr'); ap.add_argument('--region', default='asia')
ap.add_argument('--tiers', default='IRON,SILVER,GOLD,PLATINUM,EMERALD,DIAMOND')
ap.add_argument('--per-tier', type=int, default=25); ap.add_argument('--per-player', type=int, default=20)
ap.add_argument('--out', default='01_raw/lol'); ap.add_argument('--pace', type=float, default=1.25)
a = ap.parse_args(); KEY = os.environ.get('RIOT_API_KEY') or sys.exit('set RIOT_API_KEY')
KEY = KEY.strip().strip('\u2018\u2019\u201c\u201d\'"').strip()
if not KEY.startswith('RGAPI-') or not KEY.isascii(): sys.exit('RIOT_API_KEY looks wrong (must start with RGAPI-): ' + repr(KEY[:12]))
os.makedirs(a.out, exist_ok=True); random.seed(29)
def get(url):
    while True:
        time.sleep(a.pace)
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'X-Riot-Token': KEY, 'User-Agent': 'curl/8.4.0', 'Accept': 'application/json'}), timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code == 429: w = int(e.headers.get('Retry-After', '30')); print('429, wait', w, file=sys.stderr); time.sleep(w + 1)
            elif e.code in (401, 403): sys.exit(f'HTTP {e.code} at {url.split("?")[0]}\nserver said: {e.read()[:300]!r}\n(401 = key missing/invalid, 403 = key expired OR this endpoint/request refused)')
            elif e.code == 404: return None
            else: print('HTTP', e.code, url, file=sys.stderr); time.sleep(10)
        except Exception as e: print('err', e, file=sys.stderr); time.sleep(10)
P = f'https://{a.platform}.api.riotgames.com'; R = f'https://{a.region}.api.riotgames.com'
tierfile = os.path.join(a.out, '_match_tier.jsonl'); n = 0
for tier in a.tiers.split(','):
    ent = get(f'{P}/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/II?page={random.randint(1, 5)}') or []
    random.shuffle(ent)
    for e in ent[:a.per_tier]:
        pu = e.get('puuid')
        if not pu: continue
        for mid in get(f'{R}/lol/match/v5/matches/by-puuid/{pu}/ids?queue=420&type=ranked&start=0&count={a.per_player}') or []:
            fn = os.path.join(a.out, mid + '.json.gz')
            if os.path.exists(fn): continue
            m = get(f'{R}/lol/match/v5/matches/{mid}'); tl = get(f'{R}/lol/match/v5/matches/{mid}/timeline')
            if not m or not tl: continue
            json.dump({'match': m, 'timeline': tl}, gzip.open(fn, 'wt'))
            open(tierfile, 'a').write(json.dumps({'match': mid, 'tier': tier}) + '\n'); n += 1
            if n % 50 == 0: print(n, 'matches saved', file=sys.stderr)
print('done', n)
