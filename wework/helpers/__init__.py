
class HelperError(Exception):
    pass


class BaseHelper(object):

    def get_current_path(self):
        raise HelperError('you have to customized YourHelper.get_current_path')

    def get_params(self):
        raise HelperError('you have to customized YourHelper.get_params')

    def get_body(self):
        raise HelperError('you have to customized YourHelper.get_body')

    def redirect(self, url):
        raise HelperError('you have to customized YourHelper.redirect')