import unittest
from wework import settings, wechat


class TestSettings(unittest.TestCase):
    def test_init(self):
        t = settings.init(
            CROP_ID='a',
            PROVIDER_SECRET='a',
            REGISTER_URL='www.quseit.com/',
            HELPER='wegq.DjangoHelper'
        )
        self.assertTrue(isinstance(t, wechat.WorkWechatApi))

    def test_error(self):
        with self.assertRaises(settings.InitError):
            settings.init(
                CROP_ID='a',
                PROVIDER_SECRET='a',
                HELPER='wegq.DjangoHelper'
            )

        with self.assertRaises(settings.InitError):
            settings.init(
                CROP_ID='a',
                PROVIDER_SECRET='a',
                REGISTER_URL='www.quseit.com',
                HELPER='wegq.DjangoHelper'
            )

        with self.assertRaises(settings.InitError):
            settings.init(
                CROP_ID='a',
                PROVIDER_SECRET='a',
                REGISTER_URL='www.quseit.com',
                HELPER=type('MyHelper', (object, ), {}),
            )