import io
import json
import os
import tempfile
import unittest
import web_app


class LoginThrottleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_db,self.old_sessions=web_app.DB_PATH,web_app.SESSIONS
        web_app.DB_PATH=os.path.join(self.tmp.name,'users.sqlite3')
        web_app.SESSIONS=web_app.SessionManager()
        with web_app.LOGIN_LOCK:
            web_app.LOGIN_ATTEMPTS.clear()

    def tearDown(self):
        web_app.DB_PATH,web_app.SESSIONS=self.old_db,self.old_sessions
        with web_app.LOGIN_LOCK:
            web_app.LOGIN_ATTEMPTS.clear()
        self.tmp.cleanup()

    def call(self,method,path,data,ip='192.0.2.1'):
        body=json.dumps(data).encode()
        result={}
        def start(status,headers):
            result['status']=int(status.split()[0])
        result['data']=json.loads(b''.join(web_app.app({
            'REQUEST_METHOD':method,'PATH_INFO':path,
            'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body),
            'REMOTE_ADDR':ip},start)))
        return result

    def test_five_failed_attempts_block_sixth_even_correct_password(self):
        self.assertEqual(self.call('POST','/register',{'username':'alice','password':'a secure long password'})['status'],200)
        for _ in range(5):
            self.assertEqual(self.call('POST','/login',{'username':'alice','password':'wrong password'})['status'],401)
        self.assertEqual(self.call('POST','/login',{'username':'alice','password':'a secure long password'})['status'],429)
        self.assertEqual(self.call('POST','/login',{'username':'alice','password':'a secure long password'},'192.0.2.2')['status'],200)

    def test_success_clears_failed_attempts(self):
        self.call('POST','/register',{'username':'alice','password':'a secure long password'})
        self.call('POST','/login',{'username':'alice','password':'wrong password'})
        self.assertEqual(self.call('POST','/login',{'username':'alice','password':'a secure long password'})['status'],200)
        with web_app.LOGIN_LOCK:
            self.assertNotIn('192.0.2.1',web_app.LOGIN_ATTEMPTS)


if __name__=='__main__':
    unittest.main()
