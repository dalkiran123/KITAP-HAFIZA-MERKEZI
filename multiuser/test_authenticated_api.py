import io
import json
import os
import tempfile
import unittest
import web_app

class AuthenticatedAPITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        web_app.DB_PATH=os.path.join(self.temp.name,'users.sqlite3')
        web_app.SESSIONS=web_app.SessionManager()
    def tearDown(self): self.temp.cleanup()
    def request(self,method,path,data=None,cookie=''):
        body=json.dumps(data).encode() if data is not None else b''
        result={}
        def start(status,headers):
            result['status']=int(status.split()[0])
            result['headers']=dict(headers)
        output=b''.join(web_app.app({'REQUEST_METHOD':method,'PATH_INFO':path,'CONTENT_LENGTH':str(len(body)),'wsgi.input':io.BytesIO(body),'HTTP_COOKIE':cookie,
          'HTTP_X_CSRF_TOKEN': web_app.csrf_for(cookie.split('=',1)[1]) if cookie.startswith('session=') else ''},start))
        return result['status'],json.loads(output),result['headers']
    def test_isolated_ratings_and_logout(self):
        a={'username':'alice','password':'a secure long password'}
        b={'username':'bobby','password':'another secure password'}
        _,_,ha=self.request('POST','/register',a)
        _,_,hb=self.request('POST','/register',b)
        ca=ha['Set-Cookie'].split(';')[0]
        cb=hb['Set-Cookie'].split(';')[0]
        self.assertEqual(self.request('POST','/my/ratings',{'book_id':'b1','score':10},ca)[0],200)
        self.assertEqual(self.request('POST','/my/ratings',{'book_id':'b1','score':3},cb)[0],200)
        self.assertEqual(self.request('GET','/my/ratings',cookie=ca)[1]['ratings'][0]['score'],10)
        self.assertEqual(self.request('GET','/my/ratings',cookie=cb)[1]['ratings'][0]['score'],3)
        self.assertEqual(self.request('GET','/my/ratings')[0],401)
        self.assertEqual(self.request('POST','/logout',cookie=ca)[0],200)
        self.assertEqual(self.request('GET','/me',cookie=ca)[0],401)
        self.assertEqual(self.request('GET','/me',cookie=cb)[0],200)
    def test_bad_rating_and_leaderboard(self):
        p={'username':'alice','password':'a secure long password'}
        _,_,h=self.request('POST','/register',p)
        cookie=h['Set-Cookie'].split(';')[0]
        self.assertEqual(self.request('POST','/my/ratings',{'book_id':'b1','score':11},cookie)[0],400)
        self.assertEqual(self.request('GET','/leaderboard',cookie=cookie)[0],200)

if __name__=='__main__': unittest.main()
