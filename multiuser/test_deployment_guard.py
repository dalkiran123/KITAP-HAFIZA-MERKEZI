import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch
import web_app
from deployment_guard import validate_public_origin


class DeploymentGuardTests(unittest.TestCase):
    def test_host_validation(self):
        self.assertTrue(validate_public_origin({'HTTP_HOST':'books.example.test'},'https://books.example.test'))
        self.assertFalse(validate_public_origin({'HTTP_HOST':'evil.example.test'},'https://books.example.test'))
        self.assertFalse(validate_public_origin({'HTTP_HOST':'books.example.test,evil.test'},'https://books.example.test'))
        self.assertFalse(validate_public_origin({'HTTP_HOST':'books.example.test'},'http://books.example.test'))
        self.assertFalse(validate_public_origin({'HTTP_HOST':'books.example.test'},'https://books.example.test/path'))

    def test_configured_host_rejects_wrong_host_and_origin(self):
        with patch.dict(os.environ,{'BOOK_PUBLIC_ORIGIN':'https://books.example.test'}):
            def request(host,origin=None):
                env={'REQUEST_METHOD':'POST','PATH_INFO':'/register',
                     'HTTP_HOST':host,'CONTENT_LENGTH':'2',
                     'wsgi.input':io.BytesIO(b'{}')}
                if origin: env['HTTP_ORIGIN']=origin
                out={}
                def start(status,headers): out['code']=int(status.split()[0])
                out['data']=json.loads(b''.join(web_app.app(env,start)))
                return out['code']
            self.assertEqual(request('evil.example.test'),400)
            self.assertEqual(request('books.example.test','https://evil.example.test'),403)
            self.assertEqual(request('books.example.test','https://books.example.test'),400)


if __name__=='__main__':
    unittest.main()
