# Package Manifest

- 48 logical services with per-service candidate selection.
- 75 upstream definitions including manual iFAST source (Quixotic crypto remains audit-only/private-output-blocked).
- Formats: Surge, Clash classical, domain-set, V2Fly data, QX/Loon common aliases, manual rules, full Surge profile inventory-only.
- GitHub Actions: push-on-config/script + every 6 hours + manual dispatch.
- Fail-safe: first active-source fetch failure aborts instead of publishing partial rules; later failures use last-known-good mirror.
- Output: per-service active rules, candidate rules, portable RuleSnippet, macOS Telegram fail-closed RuleSnippet, recommended/strict General keys, Pages index.
- Local/unit tests: 11.
- Structural verifier checks IP/non-IP phase separation.

### Pages copy panel update
- `scripts/build.py` now embeds the freshly generated `RuleSnippet.conf` directly into `docs/index.html` on every build.
- `docs/index.html` includes a Copy [Rule] button, build time, source commit / Actions run metadata, and service table.
- `docs/rule-snippet.txt` is generated alongside `docs/RuleSnippet.conf` as a plain-text copy target.

### README auto-sync update
- `scripts/build.py` refreshes a marker-delimited section in `README.md` from the exact same `RuleSnippet.conf` generated in that run.
- The generated README section includes the complete Surge `[Rule]` block plus build / commit / Actions metadata when available.
- `scripts/verify.py` fails the workflow if the README code block is missing or differs from `dist/RuleSnippet.conf`.
- The existing `git add -A -- .` step commits the refreshed README automatically after every successful build.
## README sync hardening (v5)

- `scripts/readme_sync.py`: treats `dist/RuleSnippet.conf` as the single canonical source for README.
- Actions explicitly sync README after build and before verification.
- `scripts/verify.py`: normalizes line endings and prints a unified diff on mismatch.
- `tests/test_readme_sync.py`: regression tests for replacement, extraction, and CRLF normalization.


## Remote-build safety hardening (v6)

- The ZIP no longer ships a fake/empty generated ruleset tree; initial Pages/README explicitly say they are awaiting the first successful Actions build.
- Active upstream fetches now retry transient network failures and report byte/rule counts.
- Every active upstream must parse to at least one supported Surge rule; otherwise the build aborts before generated output is touched.
- Every active service must produce at least one final rule; otherwise the build aborts and Pages is not deployed.
- Generated `rules/`, `dist/`, and `docs/` are wiped and rebuilt only after source health checks pass, preventing stale empty preview files from surviving a successful build.
- Pages shows `Active sources: N/N OK` and `Services: 48/48 non-empty`, and publishes `build-report.json` for diagnostics.
- Parser now preserves `DOMAIN-WILDCARD`, `URL-REGEX`, and external RULE-SET logical `AND/OR/NOT` lines instead of silently dropping them.
- Local unit tests: 11.

## V7 changes
- canonical build guard requires non-empty `dist/RuleSnippet.conf` before README sync
- removed duplicate README synchronization from `build.py`; workflow owns the sequence explicitly
- Action logs pipeline version and script SHA-256 hashes
- build outputs `pipeline-version.txt` to `dist/` and `docs/`
