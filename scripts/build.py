#!/usr/bin/env python3
import argparse
import datetime
import html
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_VERSION = 'v7'
CONFIG = ROOT / 'config'
MIRROR = ROOT / 'mirror'
RULES = ROOT / 'rules'
DOCS = ROOT / 'docs'
DIST = ROOT / 'dist'

DOMAIN_TYPES = {'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-WILDCARD','DOMAIN-REGEX','URL-REGEX'}
IP_TYPES = {'IP-CIDR','IP-CIDR6','IP-ASN','GEOIP','GEOIP6'}
PASS_TYPES = DOMAIN_TYPES | IP_TYPES | {
    'DEST-PORT','SRC-PORT','PROTOCOL','SRC-IP','SRC-IP-CIDR','PROCESS-NAME','USER-AGENT',
    'SUBNET','CELLULAR-RADIO','CELLULAR-CARRIER'
}
LOGICAL_TYPES = {'AND','OR','NOT'}
TYPE_ALIASES = {
    'HOST':'DOMAIN',
    'HOST-SUFFIX':'DOMAIN-SUFFIX',
    'HOST-KEYWORD':'DOMAIN-KEYWORD',
    'IP6-CIDR':'IP-CIDR6',
}
ALLOWED_MODIFIERS = {'no-resolve','extended-matching','hybrid=off','hybrid=on'}


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(text, encoding='utf-8', newline='\n')
    tmp.replace(path)


def fetch_url(url, timeout=30, attempts=3):
    """Fetch an upstream with small retries for transient GitHub/CDN failures."""
    last = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'surge-rule-hub/2.0 (+GitHub-Actions)',
                'Accept': 'text/plain,*/*;q=0.8',
                'Cache-Control': 'no-cache',
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                if not data:
                    raise RuntimeError('empty HTTP response body')
                return data.decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            last = e
            # Permanent/not-found errors should be surfaced immediately.
            if e.code in (400, 401, 403, 404, 410):
                raise
        except Exception as e:
            last = e
        if attempt < attempts:
            time.sleep(2 ** (attempt - 1))
    raise last if last else RuntimeError(f'fetch failed: {url}')


def mirror_source(src, offline=False):
    sid = src['id']
    if src['format'] == 'manual':
        return '\n'.join(src.get('rules', [])) + '\n'
    path = MIRROR / f'{sid}.raw'
    if offline:
        if path.exists():
            return path.read_text(encoding='utf-8', errors='replace')
        return None
    try:
        text = fetch_url(src['url'])
        atomic_write(path, text)
        return text
    except Exception as e:
        print(f'[WARN] fetch failed {sid}: {e}', file=sys.stderr)
        if path.exists():
            print(f'[WARN] using last-known-good mirror for {sid}', file=sys.stderr)
            return path.read_text(encoding='utf-8', errors='replace')
        return None


def strip_inline_comment(line):
    line = line.strip()
    if not line:
        return ''
    if line.startswith('#') or line.startswith('//'):
        return ''
    # Most rule sources use spaces before inline comments.
    line = re.split(r'\s+#', line, maxsplit=1)[0].strip()
    line = re.split(r'\s+//', line, maxsplit=1)[0].strip()
    return line


def normalize_rule(raw):
    line = strip_inline_comment(raw)
    if not line:
        return None
    line = line.strip().strip('"').strip("'")
    if line.startswith('- '):
        line = line[2:].strip().strip('"').strip("'")
    logical = line.split(',', 1)[0].strip().upper()
    if logical in LOGICAL_TYPES:
        # External RULE-SET logical rules intentionally have no policy component.
        # Preserve the expression as written by the upstream.
        return line
    parts = [p.strip().strip('"').strip("'") for p in line.split(',')]
    if len(parts) < 2:
        return None
    rtype = TYPE_ALIASES.get(parts[0].upper(), parts[0].upper())
    if rtype not in PASS_TYPES:
        return None
    value = parts[1].strip()
    if not value:
        return None
    mods = []
    for x in parts[2:]:
        low = x.lower()
        if low in ALLOWED_MODIFIERS:
            mods.append(low)
    out = f'{rtype},{value}'
    if mods:
        out += ',' + ','.join(mods)
    return out


def parse_surge(text):
    out=[]
    in_rule = True
    saw_section = False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith('[') and s.endswith(']'):
            saw_section = True
            in_rule = (s.lower() == '[rule]')
            continue
        if saw_section and not in_rule:
            continue
        r = normalize_rule(raw)
        if r:
            out.append(r)
    return out


def parse_clash_classical(text):
    out=[]
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith('#') or s == 'payload:':
            continue
        if s.startswith('-'):
            s=s[1:].strip().strip('"').strip("'")
        r=normalize_rule(s)
        if r:
            out.append(r)
    return out


def parse_domainset(text):
    """Convert DOMAIN-SET semantics exactly: plain=DOMAIN, leading dot=suffix."""
    out=[]
    for raw in text.splitlines():
        s=strip_inline_comment(raw)
        if not s:
            continue
        s=s.strip().strip('"').strip("'")
        if ',' in s:
            r=normalize_rule(s)
            if r:
                out.append(r)
            continue
        suffix=False
        if s.startswith('+.'):
            s=s[2:]
            suffix=True
        elif s.startswith('.'):
            s=s[1:]
            suffix=True
        if '*' in s:
            # A DOMAIN-SET wildcard cannot be mapped losslessly to DOMAIN/DOMAIN-SUFFIX.
            continue
        if s:
            out.append(f'{"DOMAIN-SUFFIX" if suffix else "DOMAIN"},{s}')
    return out


def v2_base_url(src):
    url=src['url']
    return url.rsplit('/',1)[0] + '/'


def parse_v2fly(src, text, source_map, offline=False, visited=None):
    if visited is None:
        visited=set()
    sid=src['id']
    if sid in visited:
        return []
    visited.add(sid)
    excluded=set(x.lower().lstrip('@') for x in src.get('exclude_attrs', []))
    out=[]
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith('#'):
            continue
        body=s.split('#',1)[0].strip()
        if not body:
            continue
        toks=body.split()
        spec=toks[0]
        attrs={x.lower().lstrip('@') for x in toks[1:] if x.startswith('@')}
        if attrs & excluded:
            continue
        if spec.startswith('include:'):
            name=spec.split(':',1)[1]
            child_id=f'v2include__{name}'
            child={'id':child_id,'format':'v2fly','url':urllib.parse.urljoin(v2_base_url(src), name),'upstream':src.get('upstream','v2fly'),'exclude_attrs':list(excluded)}
            child_text=mirror_source(child, offline=offline)
            if child_text:
                out.extend(parse_v2fly(child, child_text, source_map, offline=offline, visited=visited))
            elif not offline:
                raise RuntimeError(f'v2fly include fetch failed: {src.get("id")} -> {name}')
            continue
        if spec.startswith('full:'):
            out.append('DOMAIN,' + spec[5:])
        elif spec.startswith('domain:'):
            out.append('DOMAIN-SUFFIX,' + spec[7:])
        elif spec.startswith('keyword:'):
            out.append('DOMAIN-KEYWORD,' + spec[8:])
        elif spec.startswith('regexp:'):
            # Regex conversion across geosite engines is not guaranteed. Skip deliberately.
            continue
        else:
            out.append('DOMAIN-SUFFIX,' + spec)
    return out


def parse_source(src, text, source_map, offline=False):
    fmt=src['format']
    if text is None:
        return []
    if fmt in ('surge','manual'):
        return parse_surge(text)
    if fmt == 'clash-classical':
        return parse_clash_classical(text)
    if fmt == 'domainset':
        return parse_domainset(text)
    if fmt == 'v2fly':
        return parse_v2fly(src, text, source_map, offline=offline)
    if fmt == 'surge-profile':
        # Inventory-only source. It is mirrored but never treated as a service ruleset.
        return []
    raise ValueError(f'Unsupported source format: {fmt}')


def rule_type(rule):
    return rule.split(',',1)[0].upper()


def rule_value(rule):
    p=rule.split(',')
    return p[1] if len(p)>1 else ''


def match_root(value, root):
    v=value.lower().strip('.')
    r=root.lower().strip('.')
    return v == r or v.endswith('.'+r)


def apply_filter(rules, flt):
    if not flt:
        return rules
    allow_roots=flt.get('allow_domain_roots', [])
    deny_roots=flt.get('deny_domain_roots', [])
    allow_keywords=set(x.lower() for x in flt.get('allow_keywords', []))
    keep_ip=flt.get('keep_ip', False)
    drop_ip=flt.get('drop_ip', False)
    out=[]
    for rule in rules:
        t=rule_type(rule)
        v=rule_value(rule)
        if t in IP_TYPES:
            if drop_ip:
                continue
            if keep_ip or (not allow_roots and not allow_keywords):
                out.append(rule)
            continue
        if t not in DOMAIN_TYPES:
            if not allow_roots and not allow_keywords:
                out.append(rule)
            continue
        lv=v.lower()
        if deny_roots and any(match_root(lv, r) for r in deny_roots):
            continue
        if allow_roots or allow_keywords:
            if t == 'DOMAIN-KEYWORD':
                if lv in allow_keywords:
                    out.append(rule)
            elif any(match_root(lv, r) for r in allow_roots):
                out.append(rule)
        else:
            out.append(rule)
    return out


def dedup(rules):
    seen=set(); out=[]
    for r in rules:
        key=r.lower()
        if key not in seen:
            seen.add(key); out.append(r)
    return out


def split_rules(rules):
    non_ip=[]; ip=[]
    for r in rules:
        if rule_type(r) in IP_TYPES:
            ip.append(r)
        else:
            non_ip.append(r)
    return dedup(non_ip), dedup(ip)


def candidate_source_ids(service, cid, stack=None):
    if stack is None:
        stack=[]
    if cid in stack:
        raise ValueError(f'candidate merge cycle: {stack} -> {cid}')
    c=service['candidates'][cid]
    out=[]
    for mid in c.get('merge', []):
        out.extend(candidate_source_ids(service, mid, stack+[cid]))
    out.extend(ref['id'] for ref in c.get('sources', []))
    return list(dict.fromkeys(out))


def build_candidate(service, cid, parsed, stack=None):
    if stack is None:
        stack=[]
    if cid in stack:
        raise ValueError(f'candidate merge cycle: {stack} -> {cid}')
    c=service['candidates'][cid]
    out=[]
    for mid in c.get('merge', []):
        out.extend(build_candidate(service, mid, parsed, stack+[cid]))
    for ref in c.get('sources', []):
        rr=list(parsed.get(ref['id'], []))
        rr=apply_filter(rr, ref.get('filter'))
        out.extend(rr)
    return dedup(out)


def emit_rule_file(path, header, rules):
    lines=[f'# {header}', '# Generated by surge-rule-hub; do not edit manually.']
    lines.extend(rules)
    atomic_write(path, '\n'.join(lines)+'\n')


def public_base(services_cfg):
    env=os.environ.get('PUBLIC_BASE_URL','').strip().rstrip('/')
    if env:
        return env
    return services_cfg.get('default_public_base_url','https://<GITHUB_USER>.github.io/<REPO>').rstrip('/')


def build_snippet(services_cfg, custom, report, mac_telegram_failclosed=False):
    base=public_base(services_cfg)
    services=sorted(services_cfg['services'], key=lambda x:x.get('order',9999))
    lines=['[Rule]','# Generated order: custom domain rules -> all remote non-IP -> custom IP -> all remote IP/ASN -> tail.']
    lines += custom.get('non_ip_before_remote', [])
    lines += ['', '# ===== Remote non-IP rules =====']
    for s in services:
        stat=report['services'].get(s['id'],{})
        if stat.get('non_ip',0) <= 0:
            continue
        lines.append(f'# > {s["name"]} [{s["active"]}]')
        lines.append(f'RULE-SET,{base}/rules/{s["id"]}.non_ip.list,{s["policy"]},extended-matching')
    lines += ['', '# ===== Local/custom IP rules =====']
    lines += custom.get('ip_phase', [])
    lines += ['', '# ===== Remote IP / ASN rules =====']
    for s in services:
        stat=report['services'].get(s['id'],{})
        if stat.get('ip',0) <= 0:
            continue
        lines.append(f'# > {s["name"]} [{s["active"]}]')
        lines.append(f'RULE-SET,{base}/rules/{s["id"]}.ip.list,{s["policy"]}')
        if mac_telegram_failclosed and s['id']=='telegram':
            lines.append('# macOS optional fail-closed: allow Telegram official rules above, reject other Telegram-process egress')
            lines.append('PROCESS-NAME,Telegram,REJECT-DROP')
    lines += ['', '# ===== Tail =====']
    lines += custom.get('tail', [])
    return '\n'.join(lines)+'\n'


def write_general_presets():
    recommended='''# Merge these keys into your existing [General] section; do NOT add a second [General] section.
hijack-dns = *:53
udp-policy-not-supported-behaviour = REJECT
block-quic = all-proxy
'''
    strict='''# Strict variant. Merge into your existing [General].
# include-all-networks may affect AirDrop, Xcode device discovery and other local-network workflows.
hijack-dns = *:53
udp-policy-not-supported-behaviour = REJECT
block-quic = all-proxy
include-all-networks = true
'''
    atomic_write(DIST/'General-Recommended.conf', recommended)
    atomic_write(DIST/'General-Strict.conf', strict)
    atomic_write(DOCS/'General-Recommended.conf', recommended)
    atomic_write(DOCS/'General-Strict.conf', strict)

def generate_index(services_cfg, report, snippet):
    rows=[]
    for s in sorted(services_cfg['services'], key=lambda x:x.get('order',9999)):
        stat=report['services'].get(s['id'],{})
        non_ip=stat.get('non_ip',0)
        ip=stat.get('ip',0)
        links=[]
        if non_ip > 0:
            links.append(f'<a href="rules/{s["id"]}.non_ip.list">non-IP</a>')
        if ip > 0:
            links.append(f'<a href="rules/{s["id"]}.ip.list">IP</a>')
        link_html=' / '.join(links) if links else '<span class="muted">empty</span>'
        rows.append(
            f'<tr><td>{html.escape(s["name"])}</td>'
            f'<td><code>{html.escape(s["active"])}</code></td>'
            f'<td>{html.escape(s["policy"])}</td>'
            f'<td>{non_ip}</td><td>{ip}</td><td>{link_html}</td></tr>'
        )

    active_sources=report.get('active_sources', [])
    source_states=report.get('sources', {})
    active_ok=sum(1 for sid in active_sources if source_states.get(sid, {}).get('status') == 'ok' and source_states.get(sid, {}).get('parsed_rules', 0) > 0)
    service_total=len(services_cfg['services'])
    service_nonempty=sum(1 for stat in report.get('services', {}).values() if stat.get('total', stat.get('non_ip',0)+stat.get('ip',0)) > 0)

    build_time=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    sha=os.environ.get('GITHUB_SHA','').strip()
    repo=os.environ.get('GITHUB_REPOSITORY','').strip()
    run_id=os.environ.get('GITHUB_RUN_ID','').strip()
    server=os.environ.get('GITHUB_SERVER_URL','https://github.com').rstrip('/')
    short_sha=sha[:7] if sha else 'local'
    if sha and repo:
        commit_html=f'<a href="{server}/{html.escape(repo)}/commit/{html.escape(sha)}"><code>{html.escape(short_sha)}</code></a>'
    else:
        commit_html=f'<code>{html.escape(short_sha)}</code>'
    if run_id and repo:
        run_html=f'<a href="{server}/{html.escape(repo)}/actions/runs/{html.escape(run_id)}">Action #{html.escape(run_id)}</a>'
    else:
        run_html='<span class="muted">local build</span>'

    escaped_snippet=html.escape(snippet)
    html_doc=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Surge Rule Hub</title>
<style>
:root{{color-scheme:light dark;--bg:#fff;--fg:#161616;--muted:#666;--card:#f6f7f8;--border:#d8dadd;--button:#111;--buttonfg:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111315;--fg:#f2f2f2;--muted:#aaa;--card:#1a1d20;--border:#34383d;--button:#f2f2f2;--buttonfg:#111}}}}
*{{box-sizing:border-box}}
body{{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:1180px;margin:36px auto;padding:0 20px;line-height:1.5;background:var(--bg);color:var(--fg)}}
h1,h2{{line-height:1.2}} a{{color:inherit}} .muted{{color:var(--muted)}}
.meta{{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 22px;color:var(--muted);font-size:.93rem}}
.card{{border:1px solid var(--border);background:var(--card);border-radius:14px;padding:16px;margin:18px 0 28px}}
.toolbar{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}}
.toolbar h2{{margin:0;font-size:1.1rem}}
button{{appearance:none;border:0;border-radius:9px;background:var(--button);color:var(--buttonfg);padding:9px 14px;font-weight:650;cursor:pointer}}
button:active{{transform:translateY(1px)}}
pre{{margin:0;max-height:64vh;overflow:auto;border:1px solid var(--border);border-radius:10px;background:var(--bg);padding:16px;white-space:pre;tab-size:2}}
pre code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;background:none;padding:0}}
.links{{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px}}
.table-wrap{{overflow:auto;border:1px solid var(--border);border-radius:12px}}
table{{border-collapse:collapse;width:100%;min-width:820px}} th,td{{border-bottom:1px solid var(--border);padding:9px 10px;text-align:left}} th{{position:sticky;top:0;background:var(--card)}} tr:last-child td{{border-bottom:0}} code{{background:var(--card);padding:2px 5px;border-radius:5px}}
.copy-status{{font-size:.9rem;color:var(--muted);min-width:72px;text-align:right}}
</style>
</head>
<body>
<h1>Surge Rule Hub</h1>
<p class="muted">This page is regenerated by GitHub Actions. The Surge <code>[Rule]</code> block below is always sourced from the same build output as <code>RuleSnippet.conf</code>.</p>
<div class="meta"><span>Built: <strong>{html.escape(build_time)}</strong></span><span>Source commit: {commit_html}</span><span>{run_html}</span><span>Active sources: <strong>{active_ok}/{len(active_sources)} OK</strong></span><span>Services: <strong>{service_nonempty}/{service_total} non-empty</strong></span></div>

<section class="card" id="surge-rule">
  <div class="toolbar">
    <h2>Latest Surge [Rule] block</h2>
    <div style="display:flex;align-items:center;gap:10px"><span id="copy-status" class="copy-status"></span><button type="button" id="copy-rule">Copy [Rule]</button></div>
  </div>
  <pre><code id="rule-code">{escaped_snippet}</code></pre>
  <div class="links">
    <a href="RuleSnippet.conf">Open raw RuleSnippet.conf</a>
    <a href="rule-snippet.txt">Open plain-text copy</a>
    <a href="RuleSnippet-Mac.conf">macOS Telegram fail-closed variant</a>
    <a href="General-Recommended.conf">Recommended [General]</a>
    <a href="General-Strict.conf">Strict [General]</a>
    <a href="build-report.json">Build health report</a>
  </div>
</section>

<h2>Generated service rules</h2>
<div class="table-wrap"><table><thead><tr><th>Service</th><th>Candidate</th><th>Policy</th><th>non-IP</th><th>IP</th><th>Links</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>

<script>
(function(){{
  const btn=document.getElementById('copy-rule');
  const status=document.getElementById('copy-status');
  const code=document.getElementById('rule-code');
  async function copyText(text){{
    if (navigator.clipboard && window.isSecureContext) {{ await navigator.clipboard.writeText(text); return; }}
    const ta=document.createElement('textarea'); ta.value=text; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select();
    if(!document.execCommand('copy')) throw new Error('copy failed');
    ta.remove();
  }}
  btn.addEventListener('click', async function(){{
    try{{ await copyText(code.textContent); status.textContent='Copied'; btn.textContent='Copied'; setTimeout(()=>{{status.textContent='';btn.textContent='Copy [Rule]';}},1800); }}
    catch(e){{ status.textContent='Copy failed'; }}
  }});
}})();
</script>
</body></html>'''
    atomic_write(DOCS/'index.html', html_doc)


def main():
    print(f'[PIPELINE] Surge Rule Hub {PIPELINE_VERSION}: canonical build')
    ap=argparse.ArgumentParser()
    ap.add_argument('--offline', action='store_true', help='use existing mirrors only')
    args=ap.parse_args()

    sources_cfg=load_json(CONFIG/'sources.json')
    services_cfg=load_json(CONFIG/'services.json')
    custom=load_json(CONFIG/'custom_rules.json')
    sources={x['id']:x for x in sources_cfg['sources']}

    # Mirrors are last-known-good state and are intentionally preserved across builds.
    # Generated output is cleaned only after all active upstreams have fetched/parsed successfully.
    MIRROR.mkdir(parents=True,exist_ok=True)

    parsed={}
    fetch_status={}
    source_report={}
    for sid, src in sources.items():
        text=mirror_source(src, offline=args.offline)
        fetch_status[sid]='ok' if text is not None else 'missing'
        rules=parse_source(src,text,sources,offline=args.offline) if text is not None else []
        parsed[sid]=rules
        source_report[sid]={
            'status': fetch_status[sid],
            'format': src.get('format'),
            'parsed_rules': len(rules),
            'bytes': len(text.encode('utf-8')) if text is not None else 0,
        }
        print(f'[SOURCE] {sid}: status={fetch_status[sid]} parsed={len(rules)} bytes={source_report[sid]["bytes"]}')

    active_source_ids=set()
    for service in services_cfg['services']:
        active_source_ids.update(candidate_source_ids(service, service['active']))
    blocked_active=sorted(sid for sid in active_source_ids if sources[sid].get('public_output') is False)
    if blocked_active:
        raise RuntimeError('active candidates use sources marked public_output=false: ' + ', '.join(blocked_active))
    missing_active=sorted(sid for sid in active_source_ids if fetch_status.get(sid) == 'missing')
    if missing_active:
        mode='offline mirror missing' if args.offline else 'fetch failed with no last-known-good mirror'
        raise RuntimeError(f'active upstream {mode}: ' + ', '.join(missing_active))
    empty_active_sources=sorted(
        sid for sid in active_source_ids
        if sources[sid].get('format') != 'surge-profile' and len(parsed.get(sid, [])) == 0
    )
    if empty_active_sources:
        raise RuntimeError(
            'active upstream fetched but parsed to 0 rules (format/URL changed?): ' + ', '.join(empty_active_sources)
        )

    # At this point source health is good. Remove every previous generated artifact so
    # stale/empty preview files can never survive into a successful build.
    for generated in (RULES, DOCS, DIST):
        if generated.exists():
            shutil.rmtree(generated)
    (RULES/'candidates').mkdir(parents=True,exist_ok=True)
    (DOCS/'rules').mkdir(parents=True,exist_ok=True)
    DIST.mkdir(parents=True,exist_ok=True)

    report={'pipeline_version':PIPELINE_VERSION,'sources':source_report,'active_sources':sorted(active_source_ids),'services':{}}
    for s in services_cfg['services']:
        cand_dir=RULES/'candidates'/s['id']
        cand_dir.mkdir(parents=True,exist_ok=True)
        for cid in s['candidates']:
            rr=build_candidate(s,cid,parsed)
            ni,ip=split_rules(rr)
            emit_rule_file(cand_dir/f'{cid}.non_ip.list', f'{s["name"]} candidate={cid} non-IP', ni)
            emit_rule_file(cand_dir/f'{cid}.ip.list', f'{s["name"]} candidate={cid} IP', ip)
        active=s['active']
        rr=build_candidate(s,active,parsed)
        ni,ip=split_rules(rr)
        emit_rule_file(RULES/f'{s["id"]}.non_ip.list', f'{s["name"]} active={active} non-IP', ni)
        emit_rule_file(RULES/f'{s["id"]}.ip.list', f'{s["name"]} active={active} IP', ip)
        shutil.copy2(RULES/f'{s["id"]}.non_ip.list', DOCS/'rules'/f'{s["id"]}.non_ip.list')
        shutil.copy2(RULES/f'{s["id"]}.ip.list', DOCS/'rules'/f'{s["id"]}.ip.list')
        report['services'][s['id']]={'active':active,'non_ip':len(ni),'ip':len(ip),'total':len(ni)+len(ip)}

    empty_services=[
        s['id'] for s in services_cfg['services']
        if report['services'][s['id']]['total'] == 0 and not s.get('allow_empty', False)
    ]
    if empty_services:
        details=', '.join(f"{sid}[{report['services'][sid]['active']}]" for sid in empty_services)
        raise RuntimeError('refusing to publish empty active service rules: ' + details)

    snippet=build_snippet(services_cfg, custom, report)
    mac_snippet=build_snippet(services_cfg, custom, report, mac_telegram_failclosed=True)
    atomic_write(DIST/'RuleSnippet.conf', snippet)
    atomic_write(DOCS/'RuleSnippet.conf', snippet)
    atomic_write(DOCS/'rule-snippet.txt', snippet)
    atomic_write(DIST/'RuleSnippet-Mac.conf', mac_snippet)
    atomic_write(DOCS/'RuleSnippet-Mac.conf', mac_snippet)
    write_general_presets()
    atomic_write(DOCS/'.nojekyll', '')
    atomic_write(DIST/'pipeline-version.txt', PIPELINE_VERSION+'\n')
    atomic_write(DOCS/'pipeline-version.txt', PIPELINE_VERSION+'\n')
    report_json=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    atomic_write(DIST/'build-report.json', report_json)
    atomic_write(DOCS/'build-report.json', report_json)
    generate_index(services_cfg, report, snippet)

    missing=[k for k,v in fetch_status.items() if v=='missing' and sources[k]['format']!='surge-profile']
    if missing:
        print('[WARN] missing sources: ' + ', '.join(missing), file=sys.stderr)
    nonempty=sum(1 for v in report['services'].values() if v.get('total',0)>0)
    print(f'Built {len(services_cfg["services"])} services; non-empty={nonempty}; missing sources={len(missing)}')

if __name__=='__main__':
    main()
