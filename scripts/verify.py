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
    if '<GITHUB_USER>' in canonical or '<REPO>' in canonical:
        errors.append('RuleSnippet.conf still contains a placeholder URL; PUBLIC_BASE_URL was not resolved')
    base = json.loads((ROOT / 'config' / 'services.json').read_text(encoding='utf-8'))['default_public_base_url']
    for line in canonical.splitlines():
        if line.startswith('RULE-SET,http'):
            url = line.split(',')[1]
            if not url.startswith(base.rstrip('/') + '/rules/'):
                errors.append(f'RuleSnippet.conf uses an unexpected rule URL: {url}')
    if 'PRE-ACTION LOCAL BUILD' in canonical or 'WAITING_FOR_FIRST_SUCCESSFUL_ACTIONS_BUILD' in canonical:
        errors.append('RuleSnippet.conf contains pre-build placeholder content')


# Active service outputs must not be silently empty.
for s in services:
    non_ip = ROOT / 'rules' / f'{s["id"]}.non_ip.list'
    ip = ROOT / 'rules' / f'{s["id"]}.ip.list'
    def payload_count(path):
        if not path.exists():
            return 0
        return sum(1 for line in path.read_text(encoding='utf-8').splitlines()
                   if line.strip() and not line.lstrip().startswith('#'))
    total = payload_count(non_ip) + payload_count(ip)
    if total == 0 and not s.get('allow_empty', False):
        errors.append(f'active service generated zero rules: {s["id"]} [{s["active"]}]')

# Build report must also show successful, non-empty active upstream parsing.
report_path = ROOT / 'dist' / 'build-report.json'
if not report_path.exists():
    errors.append('dist/build-report.json missing')
else:
    report = json.loads(report_path.read_text(encoding='utf-8'))
    source_states = report.get('sources', {})
    for sid in report.get('active_sources', []):
        state = source_states.get(sid, {})
        if state.get('status') != 'ok':
            errors.append(f'active source is not OK: {sid} ({state.get("status", "missing")})')
        elif state.get('format') != 'surge-profile' and state.get('parsed_rules', 0) == 0:
            errors.append(f'active source fetched but parsed zero rules: {sid}')

# The final configuration must combine the General preset and canonical rules.
final_path = ROOT / 'dist' / 'Final-Recommended.conf'
final = None
if not final_path.exists():
    errors.append('dist/Final-Recommended.conf missing')
else:
    final = normalize_text(final_path.read_text(encoding='utf-8'))
    general_path = ROOT / 'dist' / 'General-Recommended.conf'
    if not general_path.exists():
        errors.append('dist/General-Recommended.conf missing')
    elif canonical is not None:
        expected = normalize_text(general_path.read_text(encoding='utf-8') + '\n' + canonical)
        if final != expected:
            errors.append('Final-Recommended.conf does not match General-Recommended.conf + RuleSnippet.conf')

# README must expose the complete final configuration generated in this run.
readme = ROOT / 'README.md'
if not readme.exists():
    errors.append('README.md missing')
elif final is not None:
    embedded = extract_block_snippet(readme.read_text(encoding='utf-8'))
    if embedded is None:
        errors.append('README generated Surge rule markers/code block missing')
    elif embedded != final:
        errors.append('README Surge configuration does not match dist/Final-Recommended.conf')
        diff = list(difflib.unified_diff(
            final.splitlines(), embedded.splitlines(),
            fromfile='dist/Final-Recommended.conf', tofile='README embedded block', lineterm=''
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
print(f'OK: {len(services)} services verified; Raw rule URLs and complete README configuration verified')
