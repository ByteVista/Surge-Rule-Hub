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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config'
MIRROR = ROOT / 'mirror'
RULES = ROOT / 'rules'
DOCS = ROOT / 'docs'
DIST = ROOT / 'dist'

DOMAIN_TYPES = {'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','DOMAIN-REGEX'}
IP_TYPES = {'IP-CIDR','IP-CIDR6','IP-ASN','GEOIP','GEOIP6'}
PASS_TYPES = DOMAIN_TYPES | IP_TYPES | {'DEST-PORT','PROTOCOL','SRC-IP','SRC-IP-CIDR'}
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


def fetch_url(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent':'surge-rule-hub/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')


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
        if s.startswith('+.'):
            s=s[2:]
        elif s.startswith('.'):
            s=s[1:]
        if '*' in s:
            # DOMAIN-SET wildcard semantics are not converted automatically.
            continue
        if s:
            out.append(f'DOMAIN-SUFFIX,{s}')
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


README_RULE_START = '<!-- SURGE_RULE_BLOCK:START -->'
README_RULE_END = '<!-- SURGE_RULE_BLOCK:END -->'


def update_readme(snippet):
    """Replace only the generated Surge [Rule] block in README.md."""
    path = ROOT / 'README.md'
    original = path.read_text(encoding='utf-8') if path.exists() else '# Surge Rule Hub\n'

    build_time = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    sha = os.environ.get('GITHUB_SHA', '').strip()
    repo = os.environ.get('GITHUB_REPOSITORY', '').strip()
    run_id = os.environ.get('GITHUB_RUN_ID', '').strip()
    server = os.environ.get('GITHUB_SERVER_URL', 'https://github.com').rstrip('/')

    meta = [f'最后构建：`{build_time}`']
    if sha and repo:
        short_sha = sha[:7]
        meta.append(f'来源 Commit：[`{short_sha}`]({server}/{repo}/commit/{sha})')
    if run_id and repo:
        meta.append(f'[Actions Run #{run_id}]({server}/{repo}/actions/runs/{run_id})')

    block = (
        f'{README_RULE_START}\n'
        '## 最新 Surge `[Rule]` 配置（Actions 自动更新）\n\n'
        '> 本区域由 `scripts/build.py` 在每次 Actions 构建时自动刷新，内容与 '
        '`dist/RuleSnippet.conf` 完全一致。请不要手动编辑本区域。\n\n'
        + '> ' + ' · '.join(meta) + '\n\n'
        'GitHub 代码块右上角可直接复制；也可打开 [`docs/RuleSnippet.conf`](docs/RuleSnippet.conf) 查看纯文本。\n\n'
        '```ini\n'
        + snippet.rstrip() + '\n'
        '```\n'
        f'{README_RULE_END}'
    )

    pattern = re.compile(
        re.escape(README_RULE_START) + r'.*?' + re.escape(README_RULE_END),
        flags=re.S,
    )
    if pattern.search(original):
        updated = pattern.sub(lambda _: block, original)
    else:
        updated = original.rstrip() + '\n\n' + block + '\n'
    atomic_write(path, updated if updated.endswith('\n') else updated + '\n')


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
<div class="meta"><span>Built: <strong>{html.escape(build_time)}</strong></span><span>Source commit: {commit_html}</span><span>{run_html}</span></div>

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
    ap=argparse.ArgumentParser()
    ap.add_argument('--offline', action='store_true', help='use existing mirrors only')
    args=ap.parse_args()

    sources_cfg=load_json(CONFIG/'sources.json')
    services_cfg=load_json(CONFIG/'services.json')
    custom=load_json(CONFIG/'custom_rules.json')
    sources={x['id']:x for x in sources_cfg['sources']}

    MIRROR.mkdir(parents=True,exist_ok=True)
    RULES.mkdir(parents=True,exist_ok=True)
    (RULES/'candidates').mkdir(parents=True,exist_ok=True)
    (DOCS/'rules').mkdir(parents=True,exist_ok=True)
    DIST.mkdir(parents=True,exist_ok=True)

    parsed={}
    fetch_status={}
    for sid, src in sources.items():
        text=mirror_source(src, offline=args.offline)
        fetch_status[sid]='ok' if text is not None else 'missing'
        parsed[sid]=parse_source(src,text,sources,offline=args.offline) if text is not None else []

    active_source_ids=set()
    for service in services_cfg['services']:
        active_source_ids.update(candidate_source_ids(service, service['active']))
    blocked_active=sorted(sid for sid in active_source_ids if sources[sid].get('public_output') is False)
    if blocked_active:
        raise RuntimeError('active candidates use sources marked public_output=false: ' + ', '.join(blocked_active))
    missing_active=sorted(sid for sid in active_source_ids if fetch_status.get(sid) == 'missing')
    if missing_active and not args.offline:
        raise RuntimeError('active upstream fetch failed with no last-known-good mirror: ' + ', '.join(missing_active))

    report={'sources':fetch_status,'services':{}}
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
        report['services'][s['id']]={'active':active,'non_ip':len(ni),'ip':len(ip)}

    snippet=build_snippet(services_cfg, custom, report)
    mac_snippet=build_snippet(services_cfg, custom, report, mac_telegram_failclosed=True)
    atomic_write(DIST/'RuleSnippet.conf', snippet)
    atomic_write(DOCS/'RuleSnippet.conf', snippet)
    atomic_write(DOCS/'rule-snippet.txt', snippet)
    atomic_write(DIST/'RuleSnippet-Mac.conf', mac_snippet)
    atomic_write(DOCS/'RuleSnippet-Mac.conf', mac_snippet)
    update_readme(snippet)
    write_general_presets()
    atomic_write(DIST/'build-report.json', json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    generate_index(services_cfg, report, snippet)

    missing=[k for k,v in fetch_status.items() if v=='missing' and sources[k]['format']!='surge-profile']
    if missing:
        print('[WARN] missing sources: ' + ', '.join(missing), file=sys.stderr)
    print(f'Built {len(services_cfg["services"])} services; missing sources={len(missing)}')

if __name__=='__main__':
    main()
