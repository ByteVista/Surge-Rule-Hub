#!/usr/bin/env python3
import difflib
import json
import re
import sys
from pathlib import Path

from readme_sync import extract_block_snippet, normalize_text

ROOT = Path(__file__).resolve().parents[1]
services = json.loads((ROOT / 'config' / 'services.json').read_text(encoding='utf-8'))['services']
errors = []

for s in services:
    for phase in ('non_ip', 'ip'):
        p = ROOT / 'rules' / f'{s["id"]}.{phase}.list'
        if not p.exists():
            errors.append(f'missing {p.relative_to(ROOT)}')
            continue
        for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            t = line.strip()
            if not t or t.startswith('#'):
                continue
            if phase == 'non_ip' and re.match(r'^(IP-CIDR6?|IP-ASN|GEOIP6?),', t, re.I):
                errors.append(f'IP rule in non_ip: {p.name}:{n}:{t}')
            if phase == 'ip' and not re.match(r'^(IP-CIDR6?|IP-ASN|GEOIP6?),', t, re.I):
                errors.append(f'non-IP rule in ip: {p.name}:{n}:{t}')

sn = ROOT / 'dist' / 'RuleSnippet.conf'
canonical = None
if not sn.exists():
    errors.append('RuleSnippet.conf missing')
else:
    canonical = normalize_text(sn.read_text(encoding='utf-8'))
    if '[Rule]' not in canonical:
        errors.append('RuleSnippet.conf invalid: [Rule] missing')

# README must expose the exact canonical file generated in this run.
readme = ROOT / 'README.md'
if not readme.exists():
    errors.append('README.md missing')
elif canonical is not None:
    embedded = extract_block_snippet(readme.read_text(encoding='utf-8'))
    if embedded is None:
        errors.append('README generated Surge rule markers/code block missing')
    elif embedded != canonical:
        errors.append('README Surge rule block does not match dist/RuleSnippet.conf')
        diff = list(difflib.unified_diff(
            canonical.splitlines(), embedded.splitlines(),
            fromfile='dist/RuleSnippet.conf', tofile='README embedded block', lineterm=''
        ))
        if diff:
            errors.append('First README diff:\n' + '\n'.join(diff[:20]))

# Docs raw copy should be the same canonical payload too.
docs_sn = ROOT / 'docs' / 'RuleSnippet.conf'
if canonical is not None:
    if not docs_sn.exists():
        errors.append('docs/RuleSnippet.conf missing')
    elif normalize_text(docs_sn.read_text(encoding='utf-8')) != canonical:
        errors.append('docs/RuleSnippet.conf does not match dist/RuleSnippet.conf')

if errors:
    print('\n\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f'OK: {len(services)} services structurally verified; README/docs match canonical RuleSnippet.conf')
