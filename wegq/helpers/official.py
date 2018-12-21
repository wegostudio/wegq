from . import BaseHelper


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