import unittest
import web_app


class MobilePreviewTests(unittest.TestCase):
    def request(self,path):
        result={}
        def start(status,headers):
            result['status']=status
            result['headers']=dict(headers)
        body=b''.join(web_app.app({'REQUEST_METHOD':'GET','PATH_INFO':path,'HTTP_COOKIE':''},start))
        return result,body

    def test_mobile_page_served(self):
        meta,body=self.request('/mobile')
        self.assertEqual(meta['status'],'200 OK')
        self.assertIn('text/html',meta['headers']['Content-Type'])
        self.assertIn(b'/mobile/mobile_client.js',body)
        self.assertIn(b'viewport',body)

    def test_script_served(self):
        meta,body=self.request('/mobile/mobile_client.js')
        self.assertEqual(meta['status'],'200 OK')
        self.assertIn('javascript',meta['headers']['Content-Type'])
        self.assertIn(b'expected_revision',body)
        self.assertIn(b'credentials',body)


if __name__=='__main__':
    unittest.main()
