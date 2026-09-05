#!/usr/bin/env bash
set -euo pipefail
EXPECTED="surge-rule-hub v9 canonical-builder"
VERSION="$(python3 scripts/canonical_build.py --version)"
printf 'Builder: %s\n' "$VERSION"
[ "$VERSION" = "$EXPECTED" ] || { echo "ERROR: wrong canonical builder" >&2; exit 1; }
[ ! -e scripts/build.py ] || { echo "ERROR: legacy scripts/build.py exists; remove it" >&2; exit 1; }
! cmp -s scripts/canonical_build.py scripts/select.py || { echo "ERROR: canonical_build.py equals select.py" >&2; exit 1; }
grep -q 'SURGE_RULE_HUB_CANONICAL_BUILDER_V9' scripts/canonical_build.py
grep -q 'python3 scripts/canonical_build.py' .github/workflows/sync-rules.yml
python3 -m py_compile scripts/canonical_build.py scripts/select.py scripts/readme_sync.py scripts/verify.py
echo 'V9 package identity: OK'
