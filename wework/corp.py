import json
import requests
import time
from .base import BaseWechatAPI
from .ierror import GetAccessTokenError, APIValueError
from .msg import MSG


__all__ = ['WorkWechatCorpAPI']


def rq_get(url):
    data = requests.get(url).json()
    if data['errcode'] != 0:
        raise APIValueError(data)
    return data


class WorkWechatCorpAPI(BaseWechatAPI):
    """企业自建应用的api"""
    def __init__(self, corp_id, secret, agent_id):
        """
        :param corp_id: 企业id 
        :param secret: 企业自建应用的secret
        """
        self.corp_id = corp_id
        self.secret = secret
        self.agent_id = agent_id
        self._global_access_token = {}

    @property
    def msg(self):
        return MSG(self.access_token, self.agent_id)

    def _get_access_token(self):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}'.format(self.corp_id, self.secret)
        data = requests.get(url).json()
        if 'access_token' not in data:
            raise GetAccessTokenError(data)
        try:
            self._global_access_token['access_token'] = data['access_token']
            self._global_access_token['expires_time'] = data['expires_in'] + int(time.time())
        except KeyError:
            raise GetAccessTokenError(data)

    def get_department_list(self, id=None):
        """
        https://work.weixin.qq.com/api/doc#90000/90135/90208
        获取部门列表
        :param id: 部门id。获取指定部门及其下的子部门。 如果不填，默认获取全量组织架构
        :return:        
        [{
           "id": 2, # 创建的部门id
           "name": "广州研发中心", # 部门名称
           "parentid": 1, # 父亲部门id。根部门为1
           "order": 10， # 在父部门中的次序值。order值大的排序靠前。值范围是[0, 2^32)
       }],
        """
        url = 'https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token={}'.format(self.access_token)
        if id is not None:
            url += '&id={}'.format(id)
        return rq_get(url)['department']

    def get_department_user_list(self, department_id, fetch_child=False):
        """
        https://work.weixin.qq.com/api/doc#90000/90135/90200
        获取部门成员
        :param department_id: 获取的部门id
        :param fetch_child: 1/0：是否递归获取子部门下面的成员
        :return: 
        [
           {
                  "userid": "zhangsan",
                  "name": "李四",
                  "department": [1, 2], # 成员所属部门列表。列表项为部门ID，32位整型
           }
        ]
        """
        fetch_child = 1 if fetch_child else 0
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?' \
              'access_token={}&department_id={}&fetch_child={}'.format(self.access_token, department_id, fetch_child)
        return rq_get(url)['userlist']

    def get_department_user_detail_list(self, department_id, fetch_child=False):
        """
        https://work.weixin.qq.com/api/doc#90000/90135/90201
        获取所有部门成员的详情信息
        :param department_id: 获取的部门id
        :param fetch_child: 1/0：是否递归获取子部门下面的成员
        :return: 
        [{
            "userid": "zhangsan", # 成员UserID。对应管理端的帐号
            "name": "李四", # 成员名称
            "department": [1, 2], # 成员所属部门id列表，仅返回该应用有查看权限的部门id
            "order": [1, 2], # 部门内的排序值，32位整数，默认为0。数量必须和department一致，数值越大排序越前面。
            "position": "后台工程师", # 职务信息；第三方仅通讯录应用可获取
            "mobile": "15913215421", # 手机号码，第三方仅通讯录应用可获取
            "gender": "1", # 性别。0表示未定义，1表示男性，2表示女性
            "email": "zhangsan@gzdev.com", # 邮箱，第三方仅通讯录应用可获取
            "is_leader_in_dept": [1, 0], # 表示在所在的部门内是否为上级；第三方仅通讯录应用可获取
            "avatar": "url", # 头像url。注：如果要获取小图将url最后的”/0”改成”/100”即可。第三方仅通讯录应用可获取
            "telephone": "020-123456", # 座机。第三方仅通讯录应用可获取
            "enable": 1, # 成员启用状态。1表示启用的成员，0表示被禁用。服务商调用接口不会返回此字段
            "alias": "jackzhang", # 别名；第三方仅通讯录应用可获取
            "status": 1, # 激活状态: 1=已激活，2=已禁用，4=未激活 
            已激活代表已激活企业微信或已关注微工作台（原企业号）。未激活代表既未激活企业微信又未关注微工作台（原企业号）。
            "extattr": { # 扩展属性，第三方仅通讯录应用可获取
                "attrs": [
                    {
                        "type": 0,
                        "name": "文本名称",
                        "text": {
                            "value": "文本"
                        }
                    },
                    {
                        "type": 1,
                        "name": "网页名称",
                        "web": {
                            "url": "http://www.test.com",
                            "title": "标题"
                        }
                    }
                ]
            },
            "qr_code": "https://open.work.weixin.qq.com/wwopen/userQRCode?vcode=xxx", # 员工个人二维码，扫描可添加为外部联系人；第三方仅通讯录应用可获取
            "external_position": "产品经理", # 对外职务。 第三方仅通讯录应用可获取
            "external_profile": { # 成员对外属性，字段详情见对外属性；第三方仅通讯录应用可获取
                "external_corp_name": "企业简称",
                "external_attr": [{
                        "type": 0,
                        "name": "文本名称",
                        "text": {
                            "value": "文本"
                        }
                    },
                    {
                        "type": 1,
                        "name": "网页名称",
                        "web": {
                            "url": "http://www.test.com",
                            "title": "标题"
                        }
                    },
                    {
                        "type": 2,
                        "name": "测试app",
                        "miniprogram": {
                            "appid": "wx8bd80126147df384",
                            "pagepath": "/index",
                            "title": "miniprogram"
                        }
                    }
                ]
            }
        }]
        """
        fetch_child = 1 if fetch_child else 0
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/list?' \
              'access_token={}&department_id={}&fetch_child={}'.format(self.access_token, department_id, fetch_child)
        return rq_get(url)['userlist']

    def get_user_detail(self, user_id):
        """
        https://work.weixin.qq.com/api/doc#90000/90135/90196
        获取成员详细信息
        :param user_id: 成员UserID。对应管理端的帐号，企业内必须唯一。不区分大小写，长度为1~64个字节
        :return: dict
        内容与 get_department_user_detail_list 中的字典返回值是一样的。
        """
        url = 'https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={}&userid={}'.format(
            self.access_token,
            user_id
        )
        return rq_get(url)

    def get_tag_list(self):
        """
        https://work.weixin.qq.com/api/doc#90000/90135/90216
        获取标签列表
        :return: 
        [
            {
                'tagid': int,
                'tagname': str,
            }
        ]
        """
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/list?access_token={}'.format(self.access_token)
        return rq_get(url)['taglist']

    def get_tag_user_list(self, tag_id):
        """
        https://work.weixin.qq.com/api/doc#90000/90135/90213
        获取标签成员
        :param tag_id: 标签ID
        :return: 
        [
            {
                "userid": "zhangsan",
                "name": "李四"
            }
        ],
        """
        url = 'https://qyapi.weixin.qq.com/cgi-bin/tag/get?access_token={}&tagid={}'.format(self.access_token, tag_id)
        return rq_get(url)['userlist']
