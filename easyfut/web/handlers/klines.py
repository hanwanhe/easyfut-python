from easyfut.web.handlers.base import BaseHandler
from easyfut.web.response import rcodes
import re, time

# 获取k线相关
class KlinesHandler(BaseHandler):
    def get(self, klines_symbol):
        klines_symbols = self.parse_symbol(klines_symbol)
        klines_symbols_len = len(klines_symbols)
        if(klines_symbols_len == 0):
            self.suc(self.share_dict['klines'])
        else:
            for klines_symbol in klines_symbols:
                if (klines_symbol.count('_') != 2):
                    return self.error(rcodes['request_param_error']['code'], rcodes['request_param_error']['msg'])
                self.message_queue['klines'].put(klines_symbol)
            current_timestamp = int(time.time()*1000)
            # 超时时间（毫秒）
            timeout_ms = 3000+1000*klines_symbols_len            
            while True:
                # 默认处理完成
                flag = True
                for klines_symbol in klines_symbols:
                    if(klines_symbol not in self.share_dict['klines']):
                        # 还有未完成，需要继续等待
                        flag = False
                        break
                if(flag == True):
                    break
                if(int(time.time()*1000) - current_timestamp >= timeout_ms):
                    return self.error(rcodes['operate_timeout']['code'], rcodes['operate_timeout']['msg'])
                time.sleep(0.01)
            ret_data = {}
            for klines_symbol in klines_symbols:
                ret_data[klines_symbol] = self.share_dict['klines'][klines_symbol]
            return self.suc(ret_data)