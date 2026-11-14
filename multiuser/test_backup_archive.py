import json
import unittest
from user_store import connect,create_user
from backup_archive import stage_backup,restore_bytes

def sample():
    return json.dumps({'version':3,'books':[{'id':'b1','name':'Book','author':'Author',
      'summary':'Summary','read':True,'done':True,'notes':'important note'}],
      'requests':['requested title'],'requestHistory':[],
      'localStorage':{'kitap-hafiza-v1':'original raw value'}},ensure_ascii=False).encode()

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:')
        self.a=create_user(self.db,'alice','a secure long password')
        self.b=create_user(self.db,'bobby','another secure password')
    def tearDown(self): self.db.close()
    def test_exact_restore_and_isolation(self):
        raw=sample()
        result=stage_backup(self.db,self.a,raw)
        self.assertEqual(restore_bytes(self.db,self.a,result['fingerprint']),raw)
        self.assertIsNone(restore_bytes(self.db,self.b,result['fingerprint']))
        stage_backup(self.db,self.a,raw)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM backup_archives').fetchone()[0],1)
    def test_reject_invalid(self):
        with self.assertRaises(ValueError): stage_backup(self.db,self.a,b'not json')
        with self.assertRaises(ValueError): stage_backup(self.db,self.a,b'')
        with self.assertRaises(ValueError): stage_backup(self.db,999,sample())

if __name__=='__main__': unittest.main()
