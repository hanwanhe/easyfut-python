from easyfut.web.handlers.base import BaseHandler

# 获取仓位相关
class PositionHandler(BaseHandler):
    def get(self):
        self.suc(self.share_dict['position'])