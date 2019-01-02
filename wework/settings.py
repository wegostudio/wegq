from .helpers import BaseHelper
from .wechat import WorkWechatApi
from .ierror import InitError


class Settings(object):
    def __init__(self, data):
        self.data = data

    def __getattr__(self, item):
        return self.data[item]


def init(**kwargs):
    check(kwargs)
    settings = Settings(kwargs)
    return WorkWechatApi(settings)


def check(settings):
    required_list = [
        'REGISTER_URL',
        'HELPER',
    ]
    for key in required_list:
        if key not in settings:
            raise InitError('缺少必须的参数 {}'.format(key))

    if not settings['REGISTER_URL'].endswith('/'):
        raise InitError('REGISTER_URL 必须以 "/" 结尾。')

    if type(settings['HELPER']) is str:
        modules = settings['HELPER'].split('.')
        settings['HELPER'] = getattr(__import__('.'.join(modules[:-1]), fromlist=['']), modules[-1])

    if not issubclass(settings['HELPER'], BaseHelper):
        raise InitError('Helper 必须继承至 helper.BaseHelper')
