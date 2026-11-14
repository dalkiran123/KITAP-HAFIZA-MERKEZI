import io
import json
import os
import tempfile
import unittest
import web_app

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        web_app.DB_PATH=os.path.join(self.temp.name,'users.db')
        web_app.SESSIONS=web_app.SessionManager()
    def tearDown(self): self.temp.cleanup()
    def call(self,method,path,data=None):
        body=json.dumps(data).encode() if data is not None else b''
        status=[]; headers=[]
        def start(s,h): status.append(s); headers.extend(h)
        response=b''.join(web_app.app({'REQUEST_METHOD':method,'PATH_INFO':path,'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body)},start))
        return int(status[0].split()[0]),json.loads(response),dict(headers)
    def test_register_and_login(self):
        account={'username':'reader1','password':'a long safe password'}
        code,_,headers=self.call('POST','/register',account)
        self.assertEqual(code,200)
        self.assertIn('HttpOnly',headers['Set-Cookie'])
        self.assertIn('Secure',headers['Set-Cookie'])
        self.assertEqual(self.call('POST','/login',account)[0],200)
        self.assertEqual(self.call('POST','/login',{'username':'reader1','password':'wrong'})[0],401)
    def test_duplicate(self):
        p={'username':'reader1','password':'a long safe password'}
        self.assertEqual(self.call('POST','/register',p)[0],200)
        self.assertEqual(self.call('POST','/register',p)[0],400)
    def test_health(self):
        self.assertEqual(self.call('GET','/health')[0],200)

if __name__=='__main__': unittest.main()
