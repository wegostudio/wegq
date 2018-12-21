import json
import time
import requests


class WechatUser(object):
    def __init__(self, data):
        self.data = data

    def __getattr__(self, item):
        return self.data['user_info'][item]


class WorkWechatApi(object):
    def __init__(self, settings):
        self.settings = settings
        self._global_access_token = {}

    def get_login_url(self, login_path):
        app_id = self.settings.CROP_ID
        register_url = self.settings.REGISTER_URL
        # TODO 搞懂state的作用。
        url = 'https://open.work.weixin.qq.com/wwopen/sso/3rd_qrConnect?' \
              'appid={app_id}&redirect_uri={register_url}{login_path}&usertype=member'
        return url.format(
            app_id=app_id,
            register_url=register_url,
            login_path=login_path
        )

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
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_provider_token'
        data = requests.post(url, data=json.dumps({
            'corpid': self.settings.CROP_ID,
            'provider_secret': self.settings.PROVIDER_SECRET
        })).json()
        self._global_access_token['access_token'] = data['provider_access_token']
        self._global_access_token['expires_time'] = data['expires_in'] + int(time.time())

    def get_user_info(self, code):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_login_info?access_token={}'.format(self.access_token)
        data = requests.post(url, data=json.dumps({
            'auth_code': code,
        })).json()
        if data.get('errcode', 0) != 0:
            raise ValueError(data)
        return WechatUser(data)

    def login_required(self, func):
        def get_wx_user(request, *args, **kwargs):
            helper = self.settings.HELPER(request)
            code = helper.get_params().get('auth_code', '')
            if code:
                work_wx_user = self.get_user_info(code)
                request.work_wx_user = work_wx_user
                return func(request, *args, **kwargs)
            path = helper.get_current_path()
            return helper.redirect(self.get_login_url(path))
        return get_wx_user