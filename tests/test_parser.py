import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'scripts'/'canonical_build.py')
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class ParserTests(unittest.TestCase):
    def test_surge_strips_policy_but_keeps_modifier(self):
        r=b.parse_surge('DOMAIN-SUFFIX,example.com,Proxy,extended-matching\nIP-CIDR,1.2.3.4/32,DIRECT,no-resolve\n')
        self.assertEqual(r[0],'DOMAIN-SUFFIX,example.com,extended-matching')
        self.assertEqual(r[1],'IP-CIDR,1.2.3.4/32,no-resolve')

    def test_clash_classical(self):
        r=b.parse_clash_classical("payload:\n  - DOMAIN-SUFFIX , chase.com # bank\n  - IP-CIDR,1.2.3.0/24,no-resolve\n")
        self.assertEqual(r,['DOMAIN-SUFFIX,chase.com','IP-CIDR,1.2.3.0/24,no-resolve'])

    def test_domainset(self):
        r=b.parse_domainset('.example.com\n+.example.org\nexample.net\n')
        self.assertEqual(r,['DOMAIN-SUFFIX,example.com','DOMAIN-SUFFIX,example.org','DOMAIN,example.net'])

    def test_filter(self):
        rules=['DOMAIN-SUFFIX,paypal.com','DOMAIN-SUFFIX,segment.com','IP-CIDR,1.1.1.1/32,no-resolve']
        r=b.apply_filter(rules,{'allow_domain_roots':['paypal.com']})
        self.assertEqual(r,['DOMAIN-SUFFIX,paypal.com'])

    def test_cross_client_aliases(self):
        r=b.parse_clash_classical("payload:\n  - HOST-SUFFIX,example.com\n  - HOST,api.example.com\n  - IP6-CIDR,2001:db8::/32,no-resolve\n")
        self.assertEqual(r,['DOMAIN-SUFFIX,example.com','DOMAIN,api.example.com','IP-CIDR6,2001:db8::/32,no-resolve'])


    def test_domain_wildcard_and_url_regex_are_preserved(self):
        r=b.parse_surge('DOMAIN-WILDCARD,p2p*.qq.com\nURL-REGEX,https://example\\.com/.*\n')
        self.assertEqual(r,['DOMAIN-WILDCARD,p2p*.qq.com',r'URL-REGEX,https://example\.com/.*'])

    def test_logical_rule_is_preserved_in_ruleset_form(self):
        r=b.parse_surge('AND,((PROTOCOL,UDP), (DOMAIN-SUFFIX,googlevideo.com))\n')
        self.assertEqual(r,['AND,((PROTOCOL,UDP), (DOMAIN-SUFFIX,googlevideo.com))'])

    def test_split(self):
        ni,ip=b.split_rules(['DOMAIN-SUFFIX,a.com','IP-ASN,123','IP-CIDR6,::1/128,no-resolve'])
        self.assertEqual(ni,['DOMAIN-SUFFIX,a.com'])
        self.assertEqual(len(ip),2)

if __name__=='__main__':
    unittest.main()
