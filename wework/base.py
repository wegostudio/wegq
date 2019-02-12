from .ierror import GetAccessTokenError, CacheNotExistError
import time


class BaseWechatAPI(object):
    def __get_cache_access_token_and_expires(self):
        g = self._global_access_token
        access_token_name, expires_name = g['name']
        helper = self.settings.HELPER
        access_token = helper.cache_get(access_token_name)
        expires_time = helper.cache_get(expires_name)
        if access_token is None:
            raise CacheNotExistError('Access Token 不存在于缓存中。')
        return access_token, expires_time

    def __set_cache_access_token_and_expires(self, g):
        helper = self.settings.HELPER
        access_token, expires_in = self._get_access_token()
        access_token_name, expires_name = g['name']
        helper.cache_set(access_token_name, access_token)
        helper.cache_set(expires_name, expires_in + int(time.time()))
        return access_token

    @property
    def access_token(self):
        g = self._global_access_token
        try:
            access_token, expires_time = self.__get_cache_access_token_and_expires()
        except CacheNotExistError:
            access_token = self.__set_cache_access_token_and_expires(g)
        else:
            if time.time() >= expires_time:
                access_token = self.__set_cache_access_token_and_expires(g)
        return access_token

    @access_token.setter
    def access_token(self, value):
        raise ValueError('禁止对 access_token 进行赋值操作')

    def _get_access_token(self):
        raise GetAccessTokenError('无法获取 access_token')
