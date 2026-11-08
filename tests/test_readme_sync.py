import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from readme_sync import START, END, extract_block_snippet, normalize_text, replace_block, sync_readme


class ReadmeSyncTests(unittest.TestCase):
    def test_replace_and_extract_round_trip(self):
        snippet='[Rule]\nDOMAIN-SUFFIX,example.com,Proxy\n'
        readme='# Title\n\nBody\n'
        updated=replace_block(readme, snippet)
        self.assertIn(START, updated)
        self.assertIn(END, updated)
        self.assertEqual(extract_block_snippet(updated), normalize_text(snippet))

    def test_existing_block_is_replaced_not_duplicated(self):
        old=replace_block('# Title\n', '[Rule]\nDOMAIN,old.example,DIRECT\n')
        new=replace_block(old, '[Rule]\nDOMAIN,new.example,Proxy\n')
        self.assertEqual(new.count(START), 1)
        self.assertEqual(new.count(END), 1)
        self.assertIn('DOMAIN,new.example,Proxy', new)
        self.assertNotIn('DOMAIN,old.example,DIRECT', new)

    def test_crlf_normalization(self):
        self.assertEqual(normalize_text('[Rule]\r\nA\r\n'), '[Rule]\nA')

    def test_sync_uses_complete_final_configuration_and_preserves_other_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'dist').mkdir()
            final = '[General]\ndns-server = 223.5.5.5\n\n[Rule]\nFINAL,Proxy\n'
            (root / 'dist' / 'Final-Recommended.conf').write_text(final)
            (root / 'dist' / 'RuleSnippet.conf').write_text('[Rule]\nFINAL,Proxy\n')
            old = replace_block('# Title\n\nKeep this introduction.\n', '[Rule]\nFINAL,DIRECT\n')
            (root / 'README.md').write_text(old + '\nKeep this footer.\n')
            sync_readme(root)
            readme = (root / 'README.md').read_text()
            self.assertEqual(extract_block_snippet(readme), normalize_text(final))
            self.assertIn('Keep this introduction.', readme)
            self.assertIn('Keep this footer.', readme)
            self.assertIn('dist/Final-Recommended.conf', readme)

    def test_sync_requires_final_configuration_even_when_rules_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'dist').mkdir()
            (root / 'dist' / 'RuleSnippet.conf').write_text('[Rule]\nFINAL,Proxy\n')
            with self.assertRaises(FileNotFoundError):
                sync_readme(root)


if __name__ == '__main__':
    unittest.main()
