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

# README must expose the exact latest Surge [Rule] block generated in this run.
readme=ROOT/'README.md'
if not readme.exists():
    errors.append('README.md missing')
else:
    rt=readme.read_text(encoding='utf-8')
    start='<!-- SURGE_RULE_BLOCK:START -->'
    end='<!-- SURGE_RULE_BLOCK:END -->'
    if start not in rt or end not in rt:
        errors.append('README generated Surge rule markers missing')
    else:
        section=rt.split(start,1)[1].split(end,1)[0]
        m=re.search(r'```ini\n(.*?)\n```', section, re.S)
        if not m:
            errors.append('README generated Surge rule code block missing')
        elif sn.exists() and m.group(1).rstrip() != sn.read_text(encoding='utf-8').rstrip():
            errors.append('README Surge rule block does not match dist/RuleSnippet.conf')

if errors:
    print('\n'.join(errors),file=sys.stderr)
    raise SystemExit(1)
print(f'OK: {len(services)} services structurally verified')
