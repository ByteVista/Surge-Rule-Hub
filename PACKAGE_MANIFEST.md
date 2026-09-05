# Package Manifest

- 48 logical services with per-service candidate selection.
- 73 upstream definitions including manual iFAST source (Quixotic crypto remains audit-only/private-output-blocked).
- Formats: Surge, Clash classical, domain-set, V2Fly data, QX/Loon common aliases, manual rules, full Surge profile inventory-only.
- GitHub Actions: push-on-config/script + every 6 hours + manual dispatch.
- Fail-safe: first active-source fetch failure aborts instead of publishing partial rules; later failures use last-known-good mirror.
- Output: per-service active rules, candidate rules, portable RuleSnippet, macOS Telegram fail-closed RuleSnippet, recommended/strict General keys, Pages index.
- Local parser unit tests: 6.
- Structural verifier checks IP/non-IP phase separation.

### Pages copy panel update
- `scripts/build.py` now embeds the freshly generated `RuleSnippet.conf` directly into `docs/index.html` on every build.
- `docs/index.html` includes a Copy [Rule] button, build time, source commit / Actions run metadata, and service table.
- `docs/rule-snippet.txt` is generated alongside `docs/RuleSnippet.conf` as a plain-text copy target.
