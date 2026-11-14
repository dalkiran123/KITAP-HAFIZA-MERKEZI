import json
import tempfile
import unittest
from pathlib import Path
from validate_backup import inspect

class BackupTests(unittest.TestCase):
    def check(self, data):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'backup.json'
            p.write_text(json.dumps(data),encoding='utf-8')
            return inspect(p)
    def test_valid_v3(self):
        r=self.check({'version':3,'books':[{'id':'a','name':'A','author':'B','summary':'C'}],'requests':[],'requestHistory':[],'localStorage':{'kitap-hafiza-v1':'{}'}})
        self.assertEqual(r['books'],1)
    def test_duplicate_book_rejected(self):
        b={'id':'a','name':'A','author':'B','summary':'C'}
        with self.assertRaises(ValueError): self.check({'books':[b,b]})
    def test_unexpected_key_rejected(self):
        with self.assertRaises(ValueError): self.check({'books':[],'localStorage':{'password':'secret'}})
    def test_legacy(self):
        self.assertEqual(self.check([])['format'],'legacy-list')

if __name__=='__main__': unittest.main()
