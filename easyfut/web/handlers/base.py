import tornado.web
import time
from easyfut.web.response import rcodes

# 基础handler
class BaseHandler(tornado.web.RequestHandler):

    #错误信息
    last_error_msg = ''

    #初始化
    def initialize(self, share_dict, message_queue):
        #共享变量
        self.share_dict = share_dict
        #消息队列
        self.message_queue = message_queue

    #解析传过来的symbol
    def parse_symbol(self, symbol):
        return list(filter(None, map(str.strip, symbol.strip('/').split(','))))


    #initialize后调用
    def prepare(self):
        if(self.share_dict['tqsdkserver_alive'] == False):
            return self.error(rcodes['tq_error']['code'], rcodes['tq_error']['msg'])
        #判断底层TqsdkServer是否已经启动完成
        if(int(self.share_dict['last_update']) == 0):
            return self.error(rcodes['tq_wait']['code'], rcodes['tq_wait']['msg'])
        #判断TqsdkServer是否正常(30秒内有过更新) 或者 进程已经挂掉
        if(int(time.time()) - self.share_dict['last_update'] > 30):
            return self.error(rcodes['tq_error']['code'], rcodes['tq_error']['msg'])
    #日志格式
    def _request_summary(self):
        params = ''
        err_msg = ''
        if(self.request.method == 'POST'):
            params = self.request.body
        if(self.last_error_msg != ''):
            err_msg = self.last_error_msg
        return "%s %s %s %s" % (self.request.method, self.request.uri,
                                params, err_msg)

    #返回正确响应
    def suc(self, data):
        self.finish({
            'code' : rcodes['suc']['code'],
            'data': data,
            'msg': rcodes['suc']['msg'],
        })

    # 返回错误响应
    def error(self, code, errmsg, data = {}):
        self.set_status(400)
        self.last_error_msg = '错误信息：'+str(code) + " "+errmsg
        self.finish({
            'code' : code,
            'data': data,
            'msg': errmsg
        })
