import json
import requests
from .ierror import SendMsgError, GetAccessTokenError, UploadTypeError, UploadError


__all__ = ['MSG']


class MSG(object):
    def __init__(self, access_token, agent_id):
        self.access_token = access_token
        self._touser = None
        self._toparty = None
        self._totag = None
        self.agent_id = agent_id
        self.safe = 0

    @classmethod
    def new(cls, corp_id, secret, agent_id):
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}'.format(corp_id, secret)
        data = requests.get(url).json()
        if 'access_token' not in data:
            raise GetAccessTokenError(data)
        obj = cls(data['access_token'], agent_id)
        return obj

    @property
    def touser(self):
        """成员ID列表（消息接收者，多个接收者用‘|’分隔，最多支持1000个）。特殊情况：指定为@all，则向该企业应用的全部成员发送"""
        return self._touser

    @touser.setter
    def touser(self, values):
        self._touser = '|'.join(values) if not isinstance(values, str) else values

    @property
    def toparty(self):
        """部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数"""
        return self._toparty

    @toparty.setter
    def toparty(self, values):
        self._toparty = '|'.join(values) if not isinstance(values, str) else values

    @property
    def totag(self):
        """标签ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数"""
        return self._totag

    @totag.setter
    def totag(self, values):
        self._totag = '|'.join(values) if not isinstance(values, str) else values

    def check(self, type, msg):
        """
        https://work.weixin.qq.com/api/doc#90001/90143/90372
           "touser" : "UserID1|UserID2|UserID3", // 成员ID列表（消息接收者，多个接收者用‘|’分隔，最多支持1000个）。
           特殊情况：指定为@all，则向该企业应用的全部成员发送
           "toparty" : "PartyID1|PartyID2", // 部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
           "totag" : "TagID1 | TagID2", // 标签ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
           "msgtype" : "text", // 消息类型
           "agentid" : 1, // 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 获取企业授权信息 获取该参数值
           "safe": 0, // 表示是否是保密消息，0表示否，1表示是，默认0
        """
        if not (self.toparty or self.totag or self.touser):
            raise SendMsgError('toparty、touser、totag不能同时为空')

        def check_news(msg):
            if 'articles' not in msg:
                raise SendMsgError('msg 中缺少参数 articles')
            """
            参数前有井号说明不为必需参数。
            title       标题，不超过128个字节，超过会自动截断
            url         点击后跳转的链接。
            # description 描述，不超过512个字节，超过会自动截断
            # picurl      图文消息的图片链接，支持JPG、PNG格式，较好的效果为大图 1068*455，小图150*150
            """
            params = 'title', 'url'
            for param in params:
                for article in msg['articles']:
                    if param not in article:
                        raise SendMsgError(f'msg 中缺少参数 {param}')

        def check_mpnews(msg):
            """
            mpnews类型的图文消息，跟普通的图文消息一致，唯一的差异是图文内容存储在企业微信。
            多次发送mpnews，会被认为是不同的图文，阅读、点赞的统计会被分开计算。
            """
            if 'articles' not in msg:
                raise SendMsgError('msg 中缺少参数 articles')
            """
            参数前有井号说明不为必需参数。
            title                   标题，不超过128个字节，超过会自动截断
            thumb_media_id          图文消息缩略图的media_id，可以通过素材管理接口获得。此处thumb_media_id即上传接口返回的media_id
            content                 图文消息的内容，支持html标签，不超过666 K个字节
            # author                图文消息的作者，不超过64个字节
            # content_source_url    图文消息点击“阅读原文”之后的页面链接
            # digest                图文消息的描述，不超过512个字节，超过会自动截断
            """
            params = 'title', 'thumb_media_id', 'content'
            for param in params:
                for article in msg['articles']:
                    if param not in article:
                        raise SendMsgError(f'msg 中缺少参数 {param}')

        msg_tables = {
            'text': (
                # 消息内容，最长不超过2048个字节，超过将截断
                'content',
            ),
            'image': (
                # 图片媒体文件id，可以调用上传临时素材接口获取
                'media_id',
            ),
            'voice': (
                # 语音文件id，可以调用上传临时素材接口获取
                'media_id',
            ),
            'video': (
                # 视频媒体文件id，可以调用上传临时素材接口获取
                'media_id',
                # 视频消息的标题，不超过128个字节，超过会自动截断
                # 'title', -----> 该参数不为必需
                # 视频消息的描述，不超过512个字节，超过会自动截断
                # 'description', -----> 该参数不为必需
            ),
            'file': (
                # 文件id，可以调用上传临时素材接口获取
                'media_id',
            ),
            'textcard': (
                # 标题，不超过128个字节，超过会自动截断
                'title',
                # 描述，不超过512个字节，超过会自动截断
                'description',
                # 点击后跳转的链接。
                'url',
                # 按钮文字。 默认为“详情”， 不超过4个文字，超过自动截断。
                # 'btntxt', -----> 该参数不为必需
            ),
            'markdown': (
                # markdown内容，最长不超过2048个字节，必须是utf8编码
                'content',
            ),
            'miniprogram_notice': (
                # 小程序appid，必须是与当前小程序应用关联的小程序
                'appid',
                # 点击消息卡片后的小程序页面，仅限本小程序内的页面。该字段不填则消息点击后不跳转。
                # 'page', -----> 该参数不为必需
                # 消息标题，长度限制4-12个汉字
                'title',
                # 消息描述，长度限制4-12个汉字
                # 'description', -----> 该参数不为必需
                # 是否放大第一个content_item， 参数为 True 或者 False
                # 'emphasis_first_item', -----> 该参数不为必需
                # 消息内容键值对，最多允许10个item
                # 'content_item', {'key': key, 'value': value} -----> 该参数不为必需
            ),
            'news': (
                check_news,
            ),
            'mpnews': (
                check_mpnews,
            )
        }

        for param in msg_tables[type]:
            if hasattr(param, '__call__'):
                param(msg)
            else:
                if param not in msg:
                    raise SendMsgError(f'type 为 {type} 的msg 中缺少参数 {param}')

    def send(self, type, msg):
        """
           "touser" : "UserID1|UserID2|UserID3", // 成员ID列表（消息接收者，多个接收者用‘|’分隔，最多支持1000个）。
           特殊情况：指定为@all，则向该企业应用的全部成员发送
           "toparty" : "PartyID1|PartyID2", // 部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
           "totag" : "TagID1 | TagID2", // 标签ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
           "msgtype" : "text", // 消息类型
           "agentid" : 1, // 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 获取企业授权信息 获取该参数值
           "safe": 0, // 表示是否是保密消息，0表示否，1表示是，默认0
        :return: 
        """
        self.check(type, msg)
        url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}'
        data = {
            'touser': self.touser,
            'toparty': self.toparty,
            'totag': self.totag,
            'msgtype': type,
            type: msg,
            'agentid': self.agent_id,
            'safe': self.safe
        }
        data = requests.post(url, json.dumps(data)).json()
        if data['errcode'] != 0:
            raise SendMsgError(data)
        return data['errmsg']

    def upload_temp_media(self, type, file, filename):
        """
        https://work.weixin.qq.com/api/doc#90000/90135/90253
        上传临时素材
        素材上传得到media_id，该media_id仅三天内有效
        media_id在同一企业内应用之间可以共享
        :param type: 媒体文件类型，分别有图片（image）、语音（voice）、视频（video），普通文件（file） 
        :return: 
        {
           "errcode": 0,
           "errmsg": ""，
           "type": "image",
           "media_id": "1G6nrLmr5EC3MMb_-zK1dDdzmd0p7cNliYu9V5w7o8K0", # 媒体文件上传后获取的唯一标识，3天内有效
           "created_at": "1380000000"
        }
        """
        if type not in ['image', 'voice', 'video', 'file']:
            raise UploadTypeError('type的值应为以下几种之一：image、voice、video、file')
        files = {
            "media": (filename, file, )
        }
        url = 'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={}&type={}'.format(
            self.access_token,
            type,
        )
        data = requests.post(url, files=files).json()
        if data['errcode'] != 0:
            raise UploadError(data)
        return data
