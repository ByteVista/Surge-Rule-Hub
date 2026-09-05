#!/usr/bin/env python3
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'config'/'services.json'
data=json.loads(p.read_text(encoding='utf-8'))
services={s['id']:s for s in data['services']}
ap=argparse.ArgumentParser(description='Select an upstream candidate for a service')
ap.add_argument('service', nargs='?')
ap.add_argument('candidate', nargs='?')
ap.add_argument('--list', action='store_true')
a=ap.parse_args()
if a.list or not a.service:
    for sid,s in services.items():
        print(f'{sid}: active={s["active"]}; candidates={", ".join(s["candidates"].keys())}')
    raise SystemExit(0)
if a.service not in services:
    raise SystemExit(f'Unknown service: {a.service}')
s=services[a.service]
if not a.candidate:
    print(f'{a.service}: active={s["active"]}; candidates={", ".join(s["candidates"].keys())}')
    raise SystemExit(0)
if a.candidate not in s['candidates']:
    raise SystemExit(f'Unknown candidate {a.candidate}; choose: {", ".join(s["candidates"])}')
s['active']=a.candidate
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Selected {a.service} -> {a.candidate}')
