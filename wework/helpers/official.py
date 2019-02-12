from . import BaseHelper
import json


class DjangoHelper(BaseHelper):
    def __init__(self, request):
        self.request = request

    def get_current_path(self):
        return self.request.get_full_path()

    def get_params(self):
        return self.request.GET.dict()

    def get_body(self):
        return self.request.body

    def redirect(self, url):
        from django.shortcuts import redirect
        return redirect(url)

    @staticmethod
    def cache_get(key):
        try:
            with open('wework_cache.txt', 'r') as f:
                data = f.read()
                data = {} if len(data) == 0 else json.loads(data)
                try:
                    return data[key]
                except KeyError:
                    return None
        except FileNotFoundError:
            return None

    @staticmethod
    def cache_set(key, value, **kwargs):
        filename = 'wework_cache.txt'
        try:
            with open(filename, 'r') as f:
                data = f.read()
                data = {} if len(data) == 0 else json.loads(data)
        except FileNotFoundError:
            data = {}

        with open(filename, 'w+') as f:
            data[key] = value
            f.write(json.dumps(data))
