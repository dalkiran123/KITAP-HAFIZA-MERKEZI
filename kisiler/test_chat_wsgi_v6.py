import io
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
try:
    from .chat_wsgi_v6 import make_application
except ImportError:
    from chat_wsgi_v6 import make_application

class ChatWSGITests(unittest.TestCase):
    def setUp(self):
        fd,self.path=tempfile.mkstemp(suffix=".sqlite3");os.close(fd)
        db=sqlite3.connect(self.path)
        db.execute("CREATE TABLE people(id INTEGER PRIMARY KEY,name TEXT,simulated INTEGER)")
        db.execute("INSERT INTO people VALUES(1,'Beril',1)")
        db.close()
    def tearDown(self):os.unlink(self.path)
    def call(self,user="owner",method="GET",origin=None,message=None):
        payload=json.dumps(message or {}).encode()
        env={"PATH_INFO":"/api/people/chat","REQUEST_METHOD":method,
             "QUERY_STRING":"person_id=1","CONTENT_LENGTH":str(len(payload)),
             "wsgi.input":io.BytesIO(payload)}
        if origin:env["HTTP_ORIGIN"]=origin
        result=[]
        def start(code,headers):result.append(code)
        with patch.dict(os.environ,{"BOOKCENTER_PEOPLE_DB":self.path}):
            data=b"".join(make_application(lambda e:user)(env,start))
        return result[0],json.loads(data)
    def test_requires_session(self):
        self.assertTrue(self.call(user=None)[0].startswith("401"))
    def test_reject_cross_origin_post(self):
        self.assertTrue(self.call(method="POST",origin="https://evil.example")[0].startswith("403"))
    def test_reply_and_history(self):
        status,data=self.call(method="POST",origin="https://dalkiran123.github.io",message={"person_id":1,"message":"Merhaba"})
        self.assertTrue(status.startswith("200"))
        self.assertIn("reply",data)
        self.assertEqual(len(self.call()[1]["messages"]),2)
        self.assertEqual(len(self.call(user="other")[1]["messages"]),0)

if __name__=="__main__":unittest.main()
