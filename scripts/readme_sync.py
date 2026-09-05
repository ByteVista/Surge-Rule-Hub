#!/usr/bin/env python3
"""Keep README's generated Surge [Rule] block in sync with dist/RuleSnippet.conf."""
import datetime
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- SURGE_RULE_BLOCK:START -->'
END = '<!-- SURGE_RULE_BLOCK:END -->'


def normalize_text(text: str) -> str:
    """Normalize only transport-level line endings/trailing final newlines."""
    return text.replace('\r\n', '\n').replace('\r', '\n').rstrip('\n')


def build_metadata() -> list[str]:
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
    return meta


def render_block(snippet: str) -> str:
    snippet = normalize_text(snippet)
    meta = build_metadata()
    return (
        f'{START}\n'
        '## 最新 Surge `[Rule]` 配置（Actions 自动更新）\n\n'
        '> 本区域由 GitHub Actions 自动刷新，唯一内容来源是 '
        '`dist/RuleSnippet.conf`。请不要手动编辑本区域。\n\n'
        + '> ' + ' · '.join(meta) + '\n\n'
        'GitHub 代码块右上角可直接复制；也可打开 [`docs/RuleSnippet.conf`](docs/RuleSnippet.conf) 查看纯文本。\n\n'
        '```ini\n'
        + snippet + '\n'
        '```\n'
        f'{END}'
    )


def replace_block(readme_text: str, snippet: str) -> str:
    block = render_block(snippet)
    pattern = re.compile(re.escape(START) + r'.*?' + re.escape(END), flags=re.S)
    if pattern.search(readme_text):
        updated = pattern.sub(lambda _: block, readme_text)
    else:
        updated = readme_text.rstrip() + '\n\n' + block + '\n'
    return updated if updated.endswith('\n') else updated + '\n'


def extract_block_snippet(readme_text: str) -> str | None:
    """Extract only the generated ini block located between our sentinels."""
    if START not in readme_text or END not in readme_text:
        return None
    section = readme_text.split(START, 1)[1].split(END, 1)[0]
    open_fence = '```ini\n'
    start_pos = section.find(open_fence)
    if start_pos < 0:
        return None
    body_start = start_pos + len(open_fence)
    close_pos = section.find('\n```', body_start)
    if close_pos < 0:
        return None
    return normalize_text(section[body_start:close_pos])


def sync_readme(root: Path = ROOT) -> None:
    snippet_path = root / 'dist' / 'RuleSnippet.conf'
    readme_path = root / 'README.md'
    if not snippet_path.exists():
        raise FileNotFoundError(f'missing canonical snippet: {snippet_path}')
    snippet = snippet_path.read_text(encoding='utf-8')
    original = readme_path.read_text(encoding='utf-8') if readme_path.exists() else '# Surge Rule Hub\n'
    updated = replace_block(original, snippet)
    readme_path.write_text(updated, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    sync_readme()
    print('README synced from dist/RuleSnippet.conf')
