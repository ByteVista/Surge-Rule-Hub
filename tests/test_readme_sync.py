import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from readme_sync import START, END, extract_block_snippet, normalize_text, replace_block


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


if __name__ == '__main__':
    unittest.main()
