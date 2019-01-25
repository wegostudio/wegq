from .ierror import GetAccessTokenError


class BaseWechatAPI(object):
    @property
    def access_token(self):
        g = self._global_access_token
        if 'access_token' not in g or time.time() >= g['expires_time']:
            self._get_access_token()
        return self._global_access_token['access_token']

    @access_token.setter
    def access_token(self, value):
        raise ValueError('禁止对 access_token 进行赋值操作')

    def _get_access_token(self):
        raise GetAccessTokenError('无法获取 access_token')
