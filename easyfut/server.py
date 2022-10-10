import logging
from multiprocessing import Process
import tornado.ioloop
import tornado.web
import tornado.options
from easyfut.web.routes import createRoutes
import time,math


# 服务基类
class BaseServer(Process):
    #程序配置
    app_config = None
    # 共享变量
    share_dict = None
    # 消息队列
    message_queue = None

    def __init__(self, app_config, share_dict, message_queue):
        Process.__init__(self)
        # 程序配置
        self.app_config = app_config
        # 共享变量
        self.share_dict = share_dict
        # 消息队列
        self.message_queue = message_queue
        # 共享变量初始化
        self.share_dict['account'] = {}
        self.share_dict['position'] = {}
        self.share_dict['orders'] = {}
        self.share_dict['quote'] = {}
        self.share_dict['klines'] = {}
        self.share_dict['ticks'] = {}
        self.share_dict['last_update'] = 0

# 启动tqsdk
class TqsdkServer(BaseServer):

    # tqsdk api 句柄
    api = None

    # 当前所处环境
    env = None

    def run(self):
        # 日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s -     %(levelname)s - 通知: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        # 导入tqsdk相关
        from tqsdk import TqApi, TqAuth, TqKq, TqSim, TqAccount
        # 连接tqsdk
        tq_username = self.app_config.get('tqsdk', 'username')
        tq_password = self.app_config.get('tqsdk', 'password')
        auth = TqAuth(tq_username, tq_password)
        # 连接tqsdk
        self.env = self.app_config.get('tqsdk', 'env')
        if(self.env == 'prod'):
            # 实盘
            broker_id = self.app_config.get('tqsdk', 'broker_id')
            account_id = self.app_config.get('tqsdk', 'account_id')
            account_password = self.app_config.get('tqsdk', 'account_password')
            td_url = None
            if (self.app_config.has_option('tqsdk', 'td_url') and self.app_config.get('tqsdk', 'td_url') != ''):
                td_url = self.app_config.get('tqsdk', 'td_url')
            self.api = TqApi(TqAccount(broker_id, account_id, account_password, td_url = td_url), auth=auth)
        else:
            # 模拟
            self.api = TqApi(TqKq(), auth=auth)
        # 获取账户
        account = self.api.get_account()
        # 获取订单
        orders = self.api.get_order()
        # quote信息
        all_quotes = {}
        # 隐含的quotes
        all_hidden_quotes = {}
        # klines信息
        all_klines = {}
        # ticks信息
        all_ticks = {}
        # 获取仓位信息
        position = self.api.get_position()
        # 首次tqsdk信息同步到共享变量
        self.sync2sharedict(account, orders, all_quotes, position, all_klines, all_ticks, True)
        # 是否启动
        is_start = False
        # 主逻辑
        while True:
            # 等待数据更新截止事件
            self.api.wait_update(int(time.time())+3)
            # 首次启动提示
            if(is_start == False):
                is_start = True
                self.share_dict['tqsdkserver_ready'] = True
                # 服务启动成功
                logging.info("TqsdkServer 启动成功")
                host = self.app_config.get('webserver', 'host')
                port = self.app_config.get('webserver', 'port')
                while(self.share_dict['webserver_ready'] == True):
                    logging.info("WebServer 启动成功，正在监听：" + str(host) + ':' + str(port))
                    break
                # 输出免责
                logging.warning("因交易过程中存在各种不可抗拒因素（断网，程序Bug...），用户在使用EasyFut过程中产生的任何亏损（损失），用户需自行承担，EasyFut不承担任何责任。")
                # 输出当前交易环境
                if(self.env == 'prod'):
                    logging.warning("您当前正处于实盘交易中，请注意...")
                else:
                    logging.info("您当前正处于模拟交易中")
            # 新的委托单处理
            while (self.message_queue['order'].empty() == False):
                queue_order = self.message_queue['order'].get()
                if(queue_order['operate'] == 'cancel'):
                    self.api.cancel_order(queue_order['params']['order_id'])
                elif(queue_order['operate'] == 'insert'):
                    #处理涨停和跌停价格
                    if(queue_order['params']['limit_price'] in ('UPPER_LIMIT', 'LOWER_LIMIT')):
                        if(queue_order['params']['symbol'] not in all_hidden_quotes):
                            if(queue_order['params']['symbol'] in all_quotes):
                                all_hidden_quotes[queue_order['params']['symbol']] = all_quotes[queue_order['params']['symbol']]
                            else:
                                all_hidden_quotes[queue_order['params']['symbol']] = self.api.get_quote(queue_order['params']['symbol'])
                        if(queue_order['params']['limit_price'] == 'UPPER_LIMIT'):
                            queue_order['params']['limit_price'] = all_hidden_quotes[queue_order['params']['symbol']]['upper_limit']
                        else:
                            queue_order['params']['limit_price'] = all_hidden_quotes[queue_order['params']['symbol']]['lower_limit']
                    elif(queue_order['params']['limit_price'] == 'MARKET'):
                        queue_order['params']['limit_price'] = None
                    self.api.insert_order(**queue_order['params'])
                    # 立即发送下单
                    self.api.wait_update(int(time.time())+3)
            # 是否有新的quote需要订阅
            while (self.message_queue['quote'].empty() == False):
                quote_symbol = self.message_queue['quote'].get()
                if(quote_symbol in all_quotes):
                    continue
                # 之前隐形获取过，涨跌停开仓的时候
                if(quote_symbol in all_hidden_quotes):
                    all_quotes[quote_symbol] = all_hidden_quotes[quote_symbol]
                else:
                    all_quotes[quote_symbol] = self.api.get_quote(quote_symbol)

            # 是否有新的klines需要订阅
            while (self.message_queue['klines'].empty() == False):
                klines_symbol = self.message_queue['klines'].get()
                if(klines_symbol in all_klines):
                    continue

                klines_symbol_arr = klines_symbol.split('_')
                all_klines[klines_symbol] = self.api.get_kline_serial(klines_symbol_arr[0], klines_symbol_arr[1], klines_symbol_arr[2])

            # 是否有新的ticks需要订阅
            while (self.message_queue['ticks'].empty() == False):
                ticks_symbol = self.message_queue['ticks'].get()
                if(ticks_symbol in all_ticks):
                    continue
                ticks_symbol_arr = ticks_symbol.split('_')
                all_ticks[ticks_symbol] = self.api.get_tick_serial(ticks_symbol_arr[0], ticks_symbol_arr[1])
            # tqsdk信息同步到共享变量
            self.sync2sharedict(account, orders, all_quotes, position, all_klines, all_ticks, False)
        self.api.close()


    # 抽取tqsdk变量中的键值对
    def extract_kv(self, tqsdk_variable):
        from tqsdk import objs
        kv = {}
        it = iter(tqsdk_variable)
        while True:
            try:
                k = next(it)
                if (
                        isinstance(tqsdk_variable[k], str) or
                        isinstance(tqsdk_variable[k], float) or
                        isinstance(tqsdk_variable[k], int) or
                        isinstance(tqsdk_variable[k], list) or
                        isinstance(tqsdk_variable[k], bool) or 
                        isinstance(tqsdk_variable[k], objs.TradingTime)
                ):
                    if(isinstance(tqsdk_variable[k], float)):
                        if(math.isnan(tqsdk_variable[k]) == True):
                            kv[k] = 0.0
                        else:
                            kv[k] = round(tqsdk_variable[k]*100)/100
                    elif(isinstance(tqsdk_variable[k], objs.TradingTime)):
                        kv[k] = {}
                        kv[k]['day'] = tqsdk_variable[k].day
                        kv[k]['night'] = tqsdk_variable[k].night
                    else:
                        kv[k] = tqsdk_variable[k]
            except StopIteration:
                break
        return kv


    # 更新tqsdk当前信息到共享变量
    def sync2sharedict(self, account, orders, all_quotes, position, all_klines, all_ticks, force = False):
        # 同步账户
        if(self.api.is_changing(account) or force == True):
            self.share_dict['account'] = self.extract_kv(account)
        # 同步订单
        if (self.api.is_changing(orders) or force == True):
            my_orderes = {}
            for order_id in orders:
                my_orderes[order_id] = self.extract_kv(orders[order_id])
            self.share_dict['orders'] = my_orderes
        # 同步quote
        is_changing = False
        my_quotes = {}
        for quote_symbol in all_quotes:
            my_quotes[quote_symbol] = self.extract_kv(all_quotes[quote_symbol])
            if(self.api.is_changing(all_quotes[quote_symbol])):
                is_changing = True
        if(is_changing or force == True):
            self.share_dict['quote'] = my_quotes
        # 同步position
        if (self.api.is_changing(position) or force == True):
            my_position = {}
            for quote_symbol in position:
                my_position[quote_symbol] = self.extract_kv(position[quote_symbol])
            self.share_dict['position'] = my_position
        # 同步klines
        is_changing = False
        my_klines = {}
        for quote_symbol in all_klines:
            my_klines[quote_symbol] = all_klines[quote_symbol].to_dict('records')
            if(self.api.is_changing(all_klines[quote_symbol])):
                is_changing = True
        if(is_changing or force == True):
            self.share_dict['klines'] = my_klines
        # 同步ticks
        is_changing = False
        my_ticks = {}
        for quote_symbol in all_ticks:
            my_ticks[quote_symbol] = all_ticks[quote_symbol].to_dict('records')
            if(self.api.is_changing(all_ticks[quote_symbol])):
                is_changing = True
        if(is_changing or force == True):
            self.share_dict['ticks'] = my_ticks
        # 标记最近一次更新的时间戳
        if(force == False):
            self.share_dict['last_update'] = int(time.time())
        return True



# 启动http服务
class Webserver(BaseServer):

    def run(self):
        app = tornado.web.Application(createRoutes(self.share_dict, self.message_queue))
        host = self.app_config.get('webserver', 'host')
        port = self.app_config.get('webserver', 'port')
        app.listen(port, host)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s -     %(levelname)s - 通知: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.share_dict['webserver_ready'] = True
        tornado.ioloop.IOLoop.current().start()



