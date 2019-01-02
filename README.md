# wework
微信企业开发通用库


## Install

```
$ python(3) setup.py install
```


## Usage

```python

# django

import wework


w = wework.init(
    SUITE_ID=SUITE_ID,
    SUITE_SECRET=SUITE_SECRET,
    REGISTER_URL=REGISTER_URL,
    HELPER=wegq.DjangoHelper
)

@w.web_login_required(scope='snsapi_privateinfo')
def index(request):
	wx_user = request.work_wx_user
    string = wx_user.__dict__'
    return HttpResponse(string)
```



## License

[Apache](http://www.apache.org/licenses/)