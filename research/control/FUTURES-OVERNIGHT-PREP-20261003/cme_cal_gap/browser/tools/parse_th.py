import json, sys, subprocess
def load(base):
    raw = open(base + '.body','rb').read()
    try:
        return json.loads(raw)
    except Exception:
        return json.loads(subprocess.run(['python3','tools/dechunk.py'], input=raw, capture_output=True).stdout)
# normal Globex weekday pattern (times CT): weekdays close 16:00/16:45 preopen/17:00 open (equities)
def summarize(base):
    d = load(base)
    p = d['products'][0]
    out = {'symbol': p.get('globex'), 'name': p.get('name'), 'schedules': []}
    for s in p['tradingHours']['schedules']:
        ev = s.get('events', [])
        out['schedules'].append({'eventDate': s['eventDate'], 'events': [
            {'tradingDate': e['tradingDate'], 'eventTime': e['eventTime'], 'type': e['marketEventType']} for e in ev]})
    return out
if __name__ == '__main__':
    r = summarize(sys.argv[1])
    print(json.dumps(r, indent=1))
