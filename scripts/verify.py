#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
services=json.loads((ROOT/'config'/'services.json').read_text(encoding='utf-8'))['services']
errors=[]
for s in services:
    for phase in ('non_ip','ip'):
        p=ROOT/'rules'/f'{s["id"]}.{phase}.list'
        if not p.exists():
            errors.append(f'missing {p.relative_to(ROOT)}')
            continue
        for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
            t=line.strip()
            if not t or t.startswith('#'):
                continue
            if phase=='non_ip' and re.match(r'^(IP-CIDR6?|IP-ASN|GEOIP6?),',t,re.I):
                errors.append(f'IP rule in non_ip: {p.name}:{n}:{t}')
            if phase=='ip' and not re.match(r'^(IP-CIDR6?|IP-ASN|GEOIP6?),',t,re.I):
                errors.append(f'non-IP rule in ip: {p.name}:{n}:{t}')
# Structural validation only: an upstream can legitimately produce an empty IP half.
sn=ROOT/'dist'/'RuleSnippet.conf'
if not sn.exists() or '[Rule]' not in sn.read_text(encoding='utf-8'):
    errors.append('RuleSnippet.conf missing or invalid')
if errors:
    print('\n'.join(errors),file=sys.stderr)
    raise SystemExit(1)
print(f'OK: {len(services)} services structurally verified')
