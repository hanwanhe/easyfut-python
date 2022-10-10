from easyfut.web.handlers.base import BaseHandler


# 获取账户相关
class AccountHandler(BaseHandler):
    def get(self):
        self.suc(self.share_dict['account'])