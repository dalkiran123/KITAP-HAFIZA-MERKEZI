import io
import json
import os
import tempfile
import unittest
import web_app

class ShelfAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        web_app.DB_PATH=os.path.join(self.tmp.name,'db.sqlite3')
        web_app.SESSIONS=web_app.SessionManager()
    def tearDown(self): self.tmp.cleanup()
    def request(self,method,path,data=None,cookie=''):
        body=json.dumps(data).encode() if data is not None else b''
        result={}
        def start(status,headers):
            result['status']=int(status.split()[0])
            result['headers']=dict(headers)
        out=b''.join(web_app.app({'REQUEST_METHOD':method,'PATH_INFO':path,'CONTENT_LENGTH':str(len(body)),
          'wsgi.input':io.BytesIO(body),'HTTP_COOKIE':cookie},start))
        return result['status'],json.loads(out),result['headers']
    def test_two_users_cannot_read_each_others_books(self):
        _,_,a=self.request('POST','/register',{'username':'alice','password':'a secure long password'})
        _,_,b=self.request('POST','/register',{'username':'bobby','password':'another secure password'})
        ca=a['Set-Cookie'].split(';')[0]
        cb=b['Set-Cookie'].split(';')[0]
        self.assertEqual(self.request('POST','/my/books',{'book_id':'novel-1','state':{'done':True,'notes':'alice secret'}},ca)[0],200)
        self.assertEqual(self.request('GET','/my/books',cookie=cb)[1]['books'],[])
        self.assertEqual(self.request('POST','/my/books',{'book_id':'novel-1','state':{'done':False}},cb)[0],200)
        self.assertEqual(self.request('GET','/my/books',cookie=ca)[1]['books'][0]['state']['notes'],'alice secret')
        self.assertEqual(self.request('GET','/my/books',cookie=cb)[1]['books'][0]['state']['done'],False)
        self.assertEqual(self.request('GET','/my/books')[0],401)
        self.assertEqual(self.request('POST','/my/books',{'book_id':'x','state':{} })[0],401)

if __name__=='__main__': unittest.main()
