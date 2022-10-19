from easyfut.web.handlers.base import BaseHandler
from easyfut.web.response import rcodes
import time
import re


# 获取行情相关
class QuotesHandler(BaseHandler):
    def get(self, quote_symbol):
        quote_symbols = self.parse_symbol(quote_symbol)
        quote_symbols_len = len(quote_symbols)
        if(quote_symbols_len == 0):
            self.suc(self.share_dict['quote'])
        else:
            for quote_symbol in quote_symbols:
                self.message_queue['quote'].put(quote_symbol)
            current_timestamp = int(time.time()*1000)
            # 超时时间（毫秒）
            timeout_ms = 3000+1000*quote_symbols_len            
            while True:
                # 默认处理完成
                flag = True
                for quote_symbol in quote_symbols:
                    if(quote_symbol not in self.share_dict['quote']):
                        # 还有未完成，需要继续等待
                        flag = False
                        break
                if(flag == True):
                    break
                if(int(time.time()*1000) - current_timestamp >= timeout_ms):
                    return self.error(rcodes['operate_timeout']['code'], rcodes['operate_timeout']['msg'])
                time.sleep(0.01)
            ret_data = {}
            for quote_symbol in quote_symbols:
                ret_data[quote_symbol] = self.share_dict['quote'][quote_symbol]
            return self.suc(ret_data)

