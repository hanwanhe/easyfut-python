from easyfut.web.handlers.base import BaseHandler
from easyfut.web.response import rcodes
import tornado
import time
import re
import random 
import hashlib

# 获取订单相关
class OrderHandler(BaseHandler):

    #查询订单
    def get(self, order_symbol):
        order_symbols = self.parse_symbol(order_symbol)
        order_symbols_len = len(order_symbols)
        if(order_symbols_len == 0):
            #获取全部的订单
            return self.suc(self.share_dict['orders'])
        elif(order_symbols_len == 1 and order_symbols[0] == 'alive'):
            #获取当前委托
            order_alive = {}
            for order_id in self.share_dict['orders']:
                if(self.share_dict['orders'][order_id]['status'] == 'ALIVE'):
                    order_alive[order_id] = self.share_dict['orders'][order_id]
            return self.suc(order_alive) 
        else:
            #获取订单详情
            order_detail = {}
            for order_id in order_symbols:
                if(order_id in self.share_dict['orders']):
                    order_detail[order_id] = self.share_dict['orders'][order_id]
            return self.suc(order_detail) 
        
    #下单或取消委托单
    def post(self, operate):
        operate = operate.strip('/')
        if(operate == 'cancel'):
            #取消委托单
            req_param = tornado.escape.json_decode(self.request.body) 
            if('order_id' not in req_param or req_param['order_id'] not in self.share_dict['orders']):
                return self.error(rcodes['order_not_exists']['code'], rcodes['order_not_exists']['msg'])
            if(self.share_dict['orders'][req_param['order_id']]['status'] != 'ALIVE'):
                return self.error(rcodes['order_finished']['code'], rcodes['order_finished']['msg'])
            #加入消息队列，要取消的委托单
            self.message_queue['order'].put({'operate':'cancel', 'params':{'order_id':req_param['order_id']}})
            # 超时时间（毫秒）
            timeout_ms = 3000     
            current_timestamp = int(time.time()*1000)   
            while self.share_dict['orders'][req_param['order_id']]['status'] == 'ALIVE':
                if(int(time.time()*1000) - current_timestamp >= timeout_ms):
                    return self.error(rcodes['operate_timeout']['code'], rcodes['operate_timeout']['msg'])
                time.sleep(0.01)    
            return self.suc(self.share_dict['orders'][req_param['order_id']])  
        else:
            #创建委托单
            req_param = tornado.escape.json_decode(self.request.body)
            #校验委托单ID
            if('order_id' in req_param and req_param['order_id'] != ''):
                if(re.match(r'^[a-zA-Z0-9]{32}$', req_param['order_id']) is None):
                    return self.error(rcodes['request_param_error']['code'], 'order_id '+rcodes['request_param_error']['msg'])
                if(req_param['order_id'] in self.share_dict['orders']):
                    return self.error(rcodes['order_unique_error']['code'], rcodes['order_unique_error']['msg'])
                order_id = req_param['order_id']
            else:
                random_str = str(time.time())+str(random.randint(1, 100))
                order_id = hashlib.md5(random_str.encode(encoding='UTF-8')).hexdigest()
            #symbol 合约ID
            if('symbol' not in req_param or re.match(r'^[a-zA-Z0-9]+\.[a-zA-Z0-9]+$', req_param['symbol']) is None):
                return self.error(rcodes['request_param_error']['code'], 'symbol '+rcodes['request_param_error']['msg'])
            #direction
            if('direction' not in req_param or req_param['direction'] not in ("BUY", "SELL")):
                return self.error(rcodes['request_param_error']['code'], 'direction '+rcodes['request_param_error']['msg'])
            #offset
            if('offset' not in req_param or req_param['offset'] not in ("CLOSE", "OPEN", "CLOSETODAY")):
                return self.error(rcodes['request_param_error']['code'], 'offset '+rcodes['request_param_error']['msg'])
            #limit_price
            if('limit_price' not in req_param):
                return self.error(rcodes['request_param_error']['code'], 'limit_price '+rcodes['request_param_error']['msg'])
            if(req_param['limit_price'] in ('UPPER_LIMIT', 'LOWER_LIMIT', 'MARKET', 'BEST', 'FIVELEVEL')):
                limit_price = req_param['limit_price']
            else:
                try:
                    limit_price = float(req_param['limit_price'])
                except Exception as e:
                    return self.error(rcodes['request_param_error']['code'], 'limit_price '+rcodes['request_param_error']['msg'])
            #volume
            if('volume' not in req_param):
                return self.error(rcodes['request_param_error']['code'], 'volume '+rcodes['request_param_error']['msg'])
            try:
                volume = int(req_param['volume'])
            except Exception as e:
                return self.error(rcodes['request_param_error']['code'], 'limit_price '+rcodes['request_param_error']['msg'])
            if(volume < 1):
                return self.error(rcodes['request_param_error']['code'], 'limit_price '+rcodes['request_param_error']['msg'])
            #advanced
            if('advanced' in req_param and  req_param['advanced']!='' and req_param['advanced'] not in ("FAK", "FOK")):
                return self.error(rcodes['request_param_error']['code'], 'advanced '+rcodes['request_param_error']['msg'])
            #写入队列
            self.message_queue['order'].put(
                {
                    'operate':'insert', 
                    'params':{
                            'order_id'      : order_id,
                            'symbol'        : req_param['symbol'],
                            'direction'     : req_param['direction'],
                            'offset'        : req_param['offset'],
                            'volume'        : volume,
                            'limit_price'   : limit_price,
                            'advanced'      : req_param['advanced'] if ('advanced' in req_param and req_param['advanced']!='') else None
                    }
                }
            )
            # 超时时间（毫秒）
            timeout_ms = 3000   
            current_timestamp = int(time.time()*1000)  
            while order_id not in self.share_dict['orders']:
                if(int(time.time()*1000) - current_timestamp >= timeout_ms):
                    return self.error(rcodes['operate_timeout']['code'], rcodes['operate_timeout']['msg'])
                time.sleep(0.01)
            self.suc(self.share_dict['orders'][order_id])