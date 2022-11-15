from easyfut.web.handlers.base import BaseHandler
from easyfut.web.response import rcodes
import re, time

# 获取Tick相关
class TicksHandler(BaseHandler):
    def get(self, ticks_symbol):
        ticks_symbols = self.parse_symbol(ticks_symbol)
        ticks_symbol_len = len(ticks_symbols)
        if(ticks_symbol_len == 0):
            self.suc(self.share_dict['ticks'])
        else:
            for ticks_symbol in ticks_symbols:
                if (ticks_symbol.count('_') != 1):
                    return self.error(rcodes['request_param_error']['code'], rcodes['request_param_error']['msg'])
                self.message_queue['ticks'].put(ticks_symbol)
            current_timestamp = int(time.time()*1000)
            # 超时时间（毫秒）
            timeout_ms = 3000+1000*ticks_symbol_len            
            while True:
                # 默认处理完成
                flag = True
                for ticks_symbol in ticks_symbols:
                    if(ticks_symbol not in self.share_dict['ticks']):
                        # 还有未完成，需要继续等待
                        flag = False
                        break
                if(flag == True):
                    break
                if(int(time.time()*1000) - current_timestamp >= timeout_ms):
                    return self.error(rcodes['operate_timeout']['code'], rcodes['operate_timeout']['msg'])
                time.sleep(0.01)
            ret_data = {}
            for ticks_symbol in ticks_symbols:
                ret_data[ticks_symbol] = self.share_dict['ticks'][ticks_symbol]
            return self.suc(ret_data)