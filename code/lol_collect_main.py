#!/usr/bin/env python3
"""Main LoL collection for the confirmatory sample (Riot personal key). Standard library only.

Run ONE process per platform, each in its own terminal tab (rate limits are per region):
  export RIOT_API_KEY=RGAPI-...
  caffeinate -i python3 02_code/lol_collect_main.py --platform kr   --region asia
  caffeinate -i python3 02_code/lol_collect_main.py --platform euw1 --region europe
  caffeinate -i python3 02_code/lol_collect_main.py --platform na1  --region americas

Design (rate limiter, Retry-After, 5xx backoff and resume logic follow tilt-transfer/src/lol/collector.py):
  10 strata per platform: IRON..DIAMOND (divisions I-IV, random pages) + MASTER, GRANDMASTER, CHALLENGER
  --per-stratum accounts (default 200) x --per-player most recent ranked-solo matches (default 20)
  = about 40,000 matches per platform before de-duplication, 2 requests per match, about 1.2 days.
Resume: rerun the same command; saved matches and finished accounts are skipped. Seeds are fixed (seed 29).
Pilot matches listed in --exclude-dir are skipped so the confirmatory sample does not reuse them.
Raw JSON stays local (Riot policy). Never print or commit the key."""
import os, sys, json, gzip, time, argparse, random, collections, urllib.request, urllib.error
ap = argparse.ArgumentParser()
ap.add_argument('--platform', required=True); ap.add_argument('--region', required=True)
ap.add_argument('--per-stratum', type=int, default=200); ap.add_argument('--per-player', type=int, default=20)
ap.add_argument('--out', default='01_raw/lol_main'); ap.add_argument('--exclude-dir', default='01_raw/lol')
ap.add_argument('--mock', action='store_true', help='offline self-test with fake responses')
a = ap.parse_args()
KEY = (os.environ.get('RIOT_API_KEY') or ('RGAPI-mock' if a.mock else '')).strip().strip('‘’“”\'"').strip()
if not KEY.startswith('RGAPI-') or not KEY.isascii(): sys.exit('RIOT_API_KEY missing or malformed (must start with RGAPI-)')
OUT = os.path.join(a.out, a.platform); os.makedirs(OUT, exist_ok=True)
rng = random.Random(f'29-{a.platform}')
P = f'https://{a.platform}.api.riotgames.com'; R = f'https://{a.region}.api.riotgames.com'
ENTRY_TIERS = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND']
APEX = {'MASTER': 'masterleagues', 'GRANDMASTER': 'grandmasterleagues', 'CHALLENGER': 'challengerleagues'}

class Bucket:                      # sliding-window limiter: at most `cap` calls per `win` seconds
    def __init__(s, cap, win): s.cap, s.win, s.t = cap, win, collections.deque()
    def wait(s):
        now = time.monotonic()
        while s.t and now - s.t[0] >= s.win: s.t.popleft()
        if len(s.t) >= s.cap: time.sleep(s.win - (now - s.t[0]) + 0.05); return s.wait()
        s.t.append(time.monotonic())
LIM = [Bucket(18, 1.0), Bucket(95, 120.0)]     # a little under 20/s and 100/2min
nreq = 0
def mock(url):
    h = abs(hash(url))
    if '/entries/' in url: return [{'puuid': f'p{h % 100000}-{i}'} for i in range(205)] if 'page=9' not in url else []
    if 'leagues/by-queue' in url: return {'entries': [{'puuid': f'a{h % 1000}-{i}'} for i in range(300)]}
    if '/ids?' in url: return [f'{a.platform.upper()}_{(h + i) % 5000}' for i in range(a.per_player)]
    return {'metadata': {'matchId': url.rsplit('/', 2)[-1]}, 'info': {'frames': []}}
def get(url):
    global nreq
    if a.mock: nreq += 1; return mock(url)
    for attempt in range(8):
        for b in LIM: b.wait()
        nreq += 1
        try:
            req = urllib.request.Request(url, headers={'X-Riot-Token': KEY, 'User-Agent': 'curl/8.4.0', 'Accept': 'application/json'})
            return json.loads(urllib.request.urlopen(req, timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code == 429: w = float(e.headers.get('Retry-After', '10')); print(f'429, wait {w:.0f}s', file=sys.stderr); time.sleep(w + 1)
            elif e.code in (401, 403): sys.exit(f'HTTP {e.code} at {url.split("?")[0]}\nserver said: {e.read()[:300]!r}\nkey invalid or expired; fix the key and rerun (progress is saved)')
            elif e.code == 404: return None
            else: time.sleep(min(2 ** attempt + random.random(), 60))
        except Exception as e:
            print('network error, retrying:', type(e).__name__, file=sys.stderr); time.sleep(min(2 ** attempt + random.random(), 60))
    return None

def seeds(stratum):
    fn = os.path.join(OUT, f'_seeds_{stratum}.json')
    if os.path.exists(fn): return json.load(open(fn))
    pu = []
    if stratum in APEX:
        d = get(f'{P}/lol/league/v4/{APEX[stratum]}/by-queue/RANKED_SOLO_5x5') or {}
        pu = [e['puuid'] for e in d.get('entries', []) if e.get('puuid')]
    else:
        for div in ('I', 'II', 'III', 'IV'):
            got = [];  pages = list(range(1, 9)); rng.shuffle(pages)
            for pg in pages[:3]:
                got += [e['puuid'] for e in (get(f'{P}/lol/league/v4/entries/RANKED_SOLO_5x5/{stratum}/{div}?page={pg}') or []) if e.get('puuid')]
            rng.shuffle(got); pu += got[: a.per_stratum // 4 + 10]
    pu = sorted(set(pu)); rng.shuffle(pu); pu = pu[: a.per_stratum]
    json.dump(pu, open(fn, 'w')); return pu

excl = {f[:-8] for f in os.listdir(a.exclude_dir) if f.endswith('.json.gz')} if os.path.isdir(a.exclude_dir) else set()
donef = os.path.join(OUT, '_accounts_done.txt'); done = set(open(donef).read().split()) if os.path.exists(donef) else set()
tierf = os.path.join(OUT, '_match_tier.jsonl'); saved = sum(1 for f in os.listdir(OUT) if f.endswith('.json.gz')); t0 = time.time(); new = 0
for stratum in ENTRY_TIERS + list(APEX):
    for pu in seeds(stratum):
        if pu in done: continue
        for mid in get(f'{R}/lol/match/v5/matches/by-puuid/{pu}/ids?queue=420&type=ranked&start=0&count={a.per_player}') or []:
            fn = os.path.join(OUT, mid + '.json.gz')
            if mid in excl or os.path.exists(fn): continue
            m = get(f'{R}/lol/match/v5/matches/{mid}'); tl = get(f'{R}/lol/match/v5/matches/{mid}/timeline')
            if not m or not tl: continue
            with gzip.open(fn + '.tmp', 'wt') as f: json.dump({'match': m, 'timeline': tl}, f)
            os.replace(fn + '.tmp', fn)
            with open(tierf, 'a') as f: f.write(json.dumps({'match': mid, 'tier': stratum}) + '\n')
            new += 1
            if new % 100 == 0:
                print(f'[{a.platform}] {stratum}: {saved + new} matches saved, {new / max((time.time() - t0) / 3600, 1e-9):.0f}/hour, {nreq} requests', file=sys.stderr)
        with open(donef, 'a') as f: f.write(pu + '\n')
    print(f'[{a.platform}] stratum {stratum} finished', file=sys.stderr)
print(f'[{a.platform}] done: {saved + new} matches in {OUT}')
