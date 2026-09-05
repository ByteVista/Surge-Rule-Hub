"""Exercise a fresh interpreter so stdlib module shadowing is caught."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class BuilderCliTests(unittest.TestCase):
    def test_builder_identity_from_script_entrypoint(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/canonical_build.py'), '--version'],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'surge-rule-hub v9 canonical-builder')
