import json
import time
import requests
from .ierror import (
    InitError,
    GetAccessTokenError,
    SuiteTicketError,
)
from .base import BaseWechatAPI
import wework.rq as rq


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
            self._suite_api = WorkWechatSuiteApi(self.settings, self)
        return self._suite_api

    @property
    def provider_api(self):
        if not self._provider_api:
            self.check_settings(['CROP_ID', 'PROVIDER_SECRET'])
            self._provider_api = WorkProviderWechatApi(self.settings, self)
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
    def __init__(self, settings, wechat_api):
        self.wechat_api = wechat_api
        self.settings = settings
        self._global_access_token = {'name': ('suite_access_token', 'suite_expires_time')}
        self._auth_code = {}

    @property
    def suite_ticket(self):
        helper = self.settings.HELPER
        ticket = helper.cache_get('wework_suite_ticket')
        if ticket is None:
            raise SuiteTicketError('suite ticket 为空')
        return ticket

    @suite_ticket.setter
    def suite_ticket(self, value):
        helper = self.settings.HELPER
        helper.cache_set('wework_suite_ticket', value)

    def _get_access_token(self):
        """获取第三方应用凭证"""
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token'
        data = requests.post(url, json={
            'suite_id': self.settings.SUITE_ID,
            'suite_secret': self.settings.SUITE_SECRET,
            'suite_ticket': self.suite_ticket,
        }).json()
        return data['suite_access_token'], data['expires_in']

    def get_web_login_url(self, login_path, scope='snsapi_userinfo'):
        """
        :param scope: 
            应用授权作用域。
            snsapi_base：静默授权，可获取成员的基础信息（UserId与DeviceId）；
            snsapi_userinfo：静默授权，可获取成员的详细信息，但不包含手机、邮箱等敏感信息；
            snsapi_privateinfo：手动授权，可获取成员的详细信息，包含手机、邮箱等敏感信息。
        :param login_path: 登录地址。
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

    def get_qrcode_login_url(self, login_path, state='', user_type='member'):
        """
        
        :param login_path: 登录地址。 
        :param user_type: 支持登录的类型。admin代表管理员登录（使用微信扫码）,member代表成员登录（使用企业微信扫码）
        :param state: state
        :return: url
        """
        if user_type not in ['member', 'admin']:
            raise ValueError('user_type 值不为 member、admin 任意之一')
        url = 'https://open.work.weixin.qq.com/wwopen/sso/3rd_qrConnect?' \
              'appid={corpid}&' \
              'redirect_uri={redirect_url}&state={state}&' \
              'usertype={user_type}'.format(corpid=self.settings.CROP_ID,
                                            redirect_url=self.settings.REGISTER_URL + login_path[1:],
                                            user_type=user_type,
                                            state=state)
        return url

    def get_install_url(self, path, auth_code):
        url = 'https://open.work.weixin.qq.com/3rdapp/install?' \
              'suite_id={suite_id}&' \
              'pre_auth_code={pre_auth_code}&' \
              'redirect_uri={redirect_uri}&state=STATE'

        return url.format(
            suite_id=self.settings.SUITE_ID,
            pre_auth_code=auth_code,
            redirect_uri=self.settings.REGISTER_URL + path[1:]
        )

    @property
    def pre_auth_code(self):
        """该API用于获取预授权码。预授权码用于企业授权时的第三方服务商安全验证。"""
        g = self._auth_code
        if 'pre_auth_code' not in g or time.time() >= g['expires_time']:
            self._get_pre_auth_code()
        return self._auth_code['pre_auth_code']

    def set_session_info(self, pre_auth_code, test=False):
        """设置授权配置。该接口可对某次授权进行配置。可支持测试模式（应用未发布时）。"""
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/set_session_info?suite_access_token={}'.format(
            self.access_token
        )
        rq.post(url, {
            'pre_auth_code': pre_auth_code,
            'session_info': {
                'auth_type': 1 if test else 0
            }
        })
        return pre_auth_code

    @pre_auth_code.setter
    def pre_auth_code(self, value):
        raise ValueError('禁止对 pre_auth_code 进行赋值操作')

    def _get_pre_auth_code(self):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_pre_auth_code?suite_access_token={}'.format(
            self.access_token)
        data = rq.get(url)
        self._auth_code['pre_auth_code'] = data['pre_auth_code']
        self._auth_code['expires_time'] = data['expires_in'] + int(time.time())

    def _get_user_ticket(self, code):
        """获取user_ticket"""
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/getuserinfo3rd?access_token={}&code={}'.format(
            self.access_token, code
        )
        return rq.get(url)['user_ticket']

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
        data = rq.post(url, {'user_ticket': user_ticket})
        del data['errcode']
        del data['errmsg']
        return WechatUser(data)

    def qrcode_login_required(self, state='state', user_type='member'):
        """企业微信扫码授权登录"""
        def wrapper(func):
            def get_wx_user(request, *args, **kwargs):
                helper = self.settings.HELPER(request)
                code = helper.get_params().get('auth_code', '')
                if code:
                    work_wx_user = self.wechat_api.provider_api.get_user_info(code)
                    request.work_wx_user = work_wx_user
                    return func(request, *args, **kwargs)
                path = helper.get_current_path()
                return helper.redirect(self.get_qrcode_login_url(path, state, user_type))
            return get_wx_user
        return wrapper

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

    def get_corp_access_token_and_info(self, auth_code):
        """
        https://work.weixin.qq.com/api/doc#90001/90143/90603
        该API用于使用临时授权码换取授权方的永久授权码，并换取授权信息、企业access_token，临时授权码一次有效。
        :param auth_code: 临时授权码，通过安装时的回调获得
        """
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_permanent_code?suite_access_token={}'.format(
            self.access_token
        )
        return requests.post(url, json={
            'auth_code': auth_code
        }).json()

    def get_corp_access_token(self, corp_id, permanent_code):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token?suite_access_token={}'.format(
            self.access_token
        )
        data = requests.post(url, json={
            'auth_corpid': corp_id,
            'permanent_code': permanent_code,
        }).json()
        if 'access_token' not in data:
            raise GetAccessTokenError(data)
        return data['access_token']

    def get_corp_info(self, corp_id, permanent_code):
        """
        https://work.weixin.qq.com/api/doc#90001/90143/90604
        :param permanent_code: 永久授权码
        :param corp_id: 企业id
        :return: 
        {
            "errcode":0 ,
            "errmsg":"ok" ,
            "dealer_corp_info": 
            {
                "corpid": "xxxx",
                "corp_name": "name"
            },
            "auth_corp_info":  # 授权方企业信息
            {
                "corpid": "xxxx", # 授权方企业微信id
                "corp_name": "name", # 授权方企业名称
                "corp_type": "verified", # 授权方企业类型，认证号：verified, 注册号：unverified
                "corp_square_logo_url": "yyyyy", # 授权方企业方形头像
                "corp_user_max": 50,# 授权方企业用户规模
                "corp_agent_max": 30,
                "corp_full_name":"full_name", # 授权方企业的主体名称(仅认证过的企业有)
                "verified_end_time":1431775834, # 认证到期时间
                "subject_type": 1, # 企业类型，1. 企业; 2. 政府以及事业单位; 3. 其他组织, 4.团队号
                "corp_wxqrcode": "zzzzz", # 授权企业在微工作台（原企业号）的二维码，可用于关注微工作台
                "corp_scale": "1-50人", # 企业规模。当企业未设置该属性时，值为空
                "corp_industry": "IT服务", # 企业所属行业。当企业未设置该属性时，值为空
                "corp_sub_industry": "计算机软件/硬件/信息服务", # 企业所属子行业。当企业未设置该属性时，值为空
                "location":"广东省广州市" # 企业所在地信息, 为空时表示未知
            },
            "auth_info": # 授权信息。如果是通讯录应用，且没开启实体应用，是没有该项的。通讯录应用拥有企业通讯录的全部信息读写权限
            {
                "agent" : # 授权的应用信息，注意是一个数组，但仅旧的多应用套件授权时会返回多个agent，对新的单应用授权，永远只返回一个agent
                [
                    {
                        "agentid":1, # 授权方应用id
                        "name":"NAME", # 授权方应用名字
                        "round_logo_url":"xxxxxx", # 授权方应用圆形头像
                        "square_logo_url":"yyyyyy", # 授权方应用方形头像
                        "appid":1, # 旧的多应用套件中的对应应用id，新开发者请忽略
                        "privilege": # 应用对应的权限
                        {
                            "level":1, 1:通讯录基本信息只读 
                                       3:通讯录全部信息读写 4:单个基本信息只读
                            "allow_party":[1,2,3], # 应用可见范围（部门）
                            "allow_user":["zhansan","lisi"], # 应用可见范围（成员）
                            "allow_tag":[1,2,3], # 应用可见范围（标签）
                            "extra_party":[4,5,6], # 额外通讯录（部门）
                            "extra_user":["wangwu"], # 额外通讯录（成员）
                            "extra_tag":[4,5,6] # 额外通讯录（标签）
                        }
                    },
                    {
                        "agentid":2,
                        "name":"NAME2",
                        "round_logo_url":"xxxxxx",
                        "square_logo_url":"yyyyyy",
                        "appid":5
                    }
                ]
            }
        }
        """
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_auth_info?suite_access_token={}'.format(
            self.access_token
        )
        return requests.post(url, json={
            'auth_corpid': corp_id,
            'permanent_code': permanent_code,
        }).json()

    def install_app_required(self, test=False):
        def wrapper(func):
            def get_corp_info(request, *args, **kwargs):
                helper = self.settings.HELPER(request)
                auth_code = helper.get_params().get('auth_code', '')
                if auth_code:
                    request.corp_info = self.get_corp_access_token_and_info(auth_code)
                    return func(request, *args, **kwargs)
                pre_auth_code = self.set_session_info(self.pre_auth_code, test)
                path = helper.get_current_path()
                return helper.redirect(self.get_install_url(path, pre_auth_code))
            return get_corp_info
        return wrapper


class WorkProviderWechatApi(BaseWechatAPI):
    """服务商api"""
    def __init__(self, settings, wechat_api):
        self.wechat_api = wechat_api
        self.settings = settings
        self._global_access_token = {'name': ('provider_access_token', 'provider_expires_time')}

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
        data = requests.post(url, json={
            'corpid': self.settings.CROP_ID,
            'provider_secret': self.settings.PROVIDER_SECRET
        }).json()
        return data['provider_access_token'], data['expires_in']

    def get_user_info(self, code):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/service/get_login_info?access_token={}'.format(self.access_token)
        data = requests.post(url, json={
            'auth_code': code,
        }).json()
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
