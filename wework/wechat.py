import json
import time
import requests
from .ierror import InitError, SendMsgError, GetAccessTokenError, GetUserTicketError
from .base import BaseWechatAPI


class WechatUser(object):
    def __init__(self, data):
        self.data = data

    def __getattr__(self, item):
        return self.data[item]


class WorkWechatApi(object):
    def __init__(self, settings):
        self.settings = settings
        self._suite_api = None
        self._provider_api = None

        self.qrcode_login_required = None

    @property
    def web_login_required(self):
        return self.suite_api.web_login_required

    @property
    def suite_api(self):
        if not self._suite_api:
            self.check_settings(['SUITE_ID', 'SUITE_SECRET'])
            self._suite_api = WorkWechatSuiteApi(self.settings)
        return self._suite_api

    @property
    def provider_api(self):
        if not self._provider_api:
            self.check_settings(['CROP_ID', 'PROVIDER_SECRET'])
            self._provider_api = WorkProviderWechatApi(self.settings)
            self.qrcode_login_required = self._provider_api.login_required
        return self._provider_api

    def check_settings(self, keys):
        for key in keys:
            if key not in self.settings.__dict__['data']:
                raise InitError('缺少必须的参数 {}'.format(key))

    def set_suite_ticket(self, value):
        self.suite_api.suite_ticket = value


class WorkWechatSuiteApi(BaseWechatAPI):
    """第三方应用api"""
    def __init__(self, settings):
        self.settings = settings
        self._global_access_token = {}
        self._auth_code = {}

    @property
    def suite_ticket(self):
        try:
            ticket = self.settings.data['SUITE_TICKET']
        except KeyError:
            raise ValueError('suite ticket 为空')
        return ticket

    @suite_ticket.setter
    def suite_ticket(self, value):
        self.settings.data['SUITE_TICKET'] = value

    def _get_access_token(self):
        """获取第三方应用凭证"""
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token'
        suite_id = self.settings.SUITE_ID
        suite_secret = self.settings.SUITE_SECRET
        suite_ticket = self.suite_ticket
        data = requests.post(url, data=json.dumps({
            'suite_id': suite_id,
            'suite_secret': suite_secret,
            'suite_ticket': suite_ticket,
        })).json()
        try:
            self._global_access_token['access_token'] = data['suite_access_token']
            self._global_access_token['expires_time'] = data['expires_in'] + int(time.time())
        except KeyError:
            raise GetAccessTokenError(data)

    def get_web_login_url(self, login_path, scope='snsapi_userinfo'):
        """
        :param scope: 
            应用授权作用域。
            snsapi_base：静默授权，可获取成员的基础信息（UserId与DeviceId）；
            snsapi_userinfo：静默授权，可获取成员的详细信息，但不包含手机、邮箱等敏感信息；
            snsapi_privateinfo：手动授权，可获取成员的详细信息，包含手机、邮箱等敏感信息。
        :return: url
        """
        if scope not in ['snsapi_base', 'snsapi_userinfo', 'snsapi_privateinfo']:
            raise ValueError('scope 值不在 snsapi_base， snsapi_userinfo，snsapi_privateinfo 中')
        url = 'https://open.weixin.qq.com/connect/oauth2/authorize?' \
              'appid={app_id}&' \
              'redirect_uri={redirect_uri}&' \
              'response_type=code&' \
              'scope={scope}#wechat_redirect'.format(app_id=self.settings.SUITE_ID,
                                                     redirect_uri=self.settings.REGISTER_URL + login_path[1:],
                                                     scope=scope)
        return url

    @property
    def pre_auth_code(self):
        """该API用于获取预授权码。预授权码用于企业授权时的第三方服务商安全验证。"""
        g = self._auth_code
        if 'pre_auth_code' not in g or time.time() >= g['expires_time']:
            self._get_pre_auth_code()
        return self._auth_code['pre_auth_code']

    @pre_auth_code.setter
    def pre_auth_code(self, value):
        raise ValueError('禁止对 pre_auth_code 进行赋值操作')

    def _get_pre_auth_code(self):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_pre_auth_code?suite_access_token={}'.format(
            self.access_token)
        data = requests.get(url).json()
        self._auth_code['pre_auth_code'] = data['pre_auth_code']
        self._auth_code['expires_time'] = data['expires_in'] + int(time.time())

    def _get_user_ticket(self, code):
        """获取user_ticket"""
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/getuserinfo3rd?access_token={}&code={}'.format(
            self.access_token, code
        )
        data = requests.get(url).json()
        if 'user_ticket' not in data:
            raise GetUserTicketError(data)
        return data['user_ticket']

    def get_user_info(self, code):
        """
           "corpid":"wwxxxxxxyyyyy",
           "userid":"lisi",
           "name":"李四",
           "mobile":"15913215421",
           "gender":"1",
           "email":"xxx@xx.com",
           "avatar":"http://shp.qpic.cn/bizmp/xxxxxxxxxxx/0",
           "qr_code":"https://open.work.weixin.qq.com/wwopen/userQRCode?vcode=vcfc13b01dfs78e981c"
        """
        user_ticket = self._get_user_ticket(code)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/getuserdetail3rd?access_token={}'.format(self.access_token)
        data = requests.post(url, data=json.dumps({'user_ticket': user_ticket})).json()
        if data['errcode'] != 0:
            raise ValueError('获取用户详细信息失败 <{}>'.format(data))
        del data['errcode']
        del data['errmsg']
        return WechatUser(data)

    def web_login_required(self, scope='snsapi_userinfo'):
        """网页授权登录"""
        def wrapper(func):
            def get_wx_user(request, *args, **kwargs):
                helper = self.settings.HELPER(request)
                code = helper.get_params().get('code', '')
                if code:
                    work_wx_user = self.get_user_info(code)
                    request.work_wx_user = work_wx_user
                    return func(request, *args, **kwargs)
                path = helper.get_current_path()
                return helper.redirect(self.get_web_login_url(path, scope))
            return get_wx_user
        return wrapper


class WorkProviderWechatApi(BaseWechatAPI):
    """服务商api"""
    def __init__(self, settings):
        self.settings = settings
        self._global_access_token = {}

    def get_login_url(self, login_path):
        """扫码登录"""
        app_id = self.settings.CROP_ID
        register_url = self.settings.REGISTER_URL
        url = 'https://open.work.weixin.qq.com/wwopen/sso/3rd_qrConnect?' \
              'appid={app_id}&redirect_uri={register_url}{login_path}&usertype=member'
        return url.format(
            app_id=app_id,
            register_url=register_url,
            login_path=login_path
        )

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
        """第三方应用二维码回调登录"""
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