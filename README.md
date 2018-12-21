# wegq
微信企业开发通用库


## Install

```
$ python(3) setup.py install
```


## Usage

```python

# django

import wegq


w = wegq.init(
    CROP_ID='CROP_ID',
    PROVIDER_SECRET='PROVIDER_SECRET',
    REGISTER_URL='REGISTER_URL',
    HELPER='wegq.DjangoHelper'
)

@w.login_required
def index(request):
	wx_user = request.work_wx_user
    string = f'{user.name}, {user.userid}, {user.email}'
    return HttpResponse(string)
```


## License

[Apache](http://www.apache.org/licenses/)