import io
import json
import os
import tempfile
import unittest
import web_app

class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        web_app.DB_PATH=os.path.join(self.tmp.name,'users.sqlite3')
        web_app.SESSIONS.clear()
    def tearDown(self): self.tmp.cleanup()
    def call(self,method,path,data=None,cookie=''):
        body=json.dumps(data).encode() if data is not None else b''
        state={}
        def start(status,headers): state['status']=int(status.split()[0]);state['headers']=dict(headers)
        output=b''.join(web_app.app({'REQUEST_METHOD':method,'PATH_INFO':path,
          'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body),
          'HTTP_COOKIE':cookie},start))
        return state['status'],json.loads(output),state['headers']
    def test_separate_user_ratings(self):
        a={'username':'alice','password':'a secure long password'}
        b={'username':'bobby','password':'another long password'}
        _,_,h1=self.call('POST','/register',a)
        _,_,h2=self.call('POST','/register',b)
        c1=h1['Set-Cookie'].split(';')[0]
        c2=h2['Set-Cookie'].split(';')[0]
        self.assertEqual(self.call('POST','/my/ratings',{'book_id':'abc','score':10},c1)[0],200)
        self.assertEqual(self.call('POST','/my/ratings',{'book_id':'abc','score':3},c2)[0],200)
        self.assertEqual(self.call('GET','/my/ratings',cookie=c1)[1]['ratings'][0]['score'],10)
        self.assertEqual(self.call('GET','/my/ratings',cookie=c2)[1]['ratings'][0]['score'],3)
        self.assertEqual(self.call('GET','/my/ratings')[0],401)
    def test_logout(self):
        p={'username':'reader','password':'a secure long password'}
        _,_,h=self.call('POST','/register',p)
        cookie=h['Set-Cookie'].split(';')[0]
        self.assertEqual(self.call('GET','/me',cookie=cookie)[0],200)
        self.assertEqual(self.call('POST','/logout',cookie=cookie)[0],200)
        self.assertEqual(self.call('GET','/me',cookie=cookie)[0],401)

if __name__=='__main__': unittest.main()
