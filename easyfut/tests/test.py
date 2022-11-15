import requests
import hashlib
import time
import sys


#服务
host_url = 'http://127.0.0.1:8888'

#测试获取账户信息
def test_account():
    account = requests.get(host_url+'/account').json()
    assert(account['code'] == 10000 and len(account['data']) > 0 and isinstance(account['data']['balance'], float))
    print("账户权益："+str(account['data']['balance']))
#测试获取当前持仓
def test_position():
    position = requests.get(host_url+'/position').json()   
    assert(position['code'] == 10000)
    pos_num = 0
    for quote_symbol, position_info in position['data'].items():
        if(position_info['pos_short'] > 0 or position_info['pos_long'] > 0):
            pos_num+=1
    print('持仓品种数：'+str(pos_num))


#获取主力合约对应的标的合约
def test_kqm_quote():
    #获取螺纹钢和铁矿石当前主力合约
    quote = requests.get(host_url+'/quote/KQ.m@SHFE.rb,KQ.m@DCE.i').json()
    assert(quote['code'] == 10000 and 'KQ.m@SHFE.rb' in quote['data'] and 'KQ.m@DCE.i' in quote['data'])
    rb_underlying_symbol = quote['data']['KQ.m@SHFE.rb']['underlying_symbol']
    i_underlying_symbol = quote['data']['KQ.m@DCE.i']['underlying_symbol']
    assert(rb_underlying_symbol != '')
    assert(i_underlying_symbol != '')
    print("螺纹钢主力合约："+rb_underlying_symbol)
    print("铁矿石主力合约："+i_underlying_symbol)
    return rb_underlying_symbol, i_underlying_symbol

#测试实时行情
def test_quote():
    rb_underlying_symbol, i_underlying_symbol = test_kqm_quote()
    #获取实时行情
    quote = requests.get(host_url+'/quote/'+rb_underlying_symbol+','+i_underlying_symbol).json()
    assert(quote['code'] == 10000 and rb_underlying_symbol in quote['data'] and i_underlying_symbol in quote['data'])
    print(rb_underlying_symbol+" 最新价："+str(quote['data'][rb_underlying_symbol]['last_price']))
    print(i_underlying_symbol+" 最新价："+str(quote['data'][i_underlying_symbol]['last_price']))

#测试k线行情
def test_klines():
    rb_underlying_symbol, i_underlying_symbol = test_kqm_quote()
    klines = requests.get(host_url+'/klines/'+rb_underlying_symbol+'_60_5,'+i_underlying_symbol+'_60_5').json()
    assert(klines['code'] == 10000 and rb_underlying_symbol+'_60_5' in klines['data'] and i_underlying_symbol+'_60_5' in klines['data'])
    print(rb_underlying_symbol+'_60_5 k线最新收盘价：'+str(klines['data'][rb_underlying_symbol+'_60_5'][-1]['close']))
    print(i_underlying_symbol+'_60_5 k线最新收盘价：'+str(klines['data'][i_underlying_symbol+'_60_5'][-1]['close']))

#测试ticks
def test_ticks():
    rb_underlying_symbol, i_underlying_symbol = test_kqm_quote()
    ticks = requests.get(host_url+'/ticks/'+rb_underlying_symbol+'_5,'+i_underlying_symbol+'_5').json()
    assert(ticks['code'] == 10000 and rb_underlying_symbol+'_5' in ticks['data'] and i_underlying_symbol+'_5' in ticks['data'])
    print(rb_underlying_symbol+'_5 ticks最新价：'+str(ticks['data'][rb_underlying_symbol+'_5'][-1]['last_price']))
    print(i_underlying_symbol+'_5 ticks最新价：'+str(ticks['data'][i_underlying_symbol+'_5'][-1]['last_price']))

#测试下单,撤单等
def test_order():
    rb_underlying_symbol, i_underlying_symbol = test_kqm_quote()
    my_order_id = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()
    # 涨停买入
    order = requests.post(host_url+'/order', json={
        'order_id': my_order_id,
        'symbol' : rb_underlying_symbol, 
        'direction' : 'BUY',
        'offset': 'OPEN',
        'volume': 1,
        'limit_price': 'UPPER_LIMIT'
    }).json()
    assert(order['code'] == 10000 and order['data']['order_id'] == my_order_id)
    while True:
        order_info = requests.get(host_url+'/order/'+my_order_id).json()
        if order_info['data'][my_order_id]['status'] == 'FINISHED':
            print("涨停买入成交价格："+str(order_info['data'][my_order_id]['trade_price']))
            break
        time.sleep(1)
    #跌停买入
    my_order_id = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()
    order = requests.post(host_url+'/order', json={
        'order_id': my_order_id,
        'symbol' : rb_underlying_symbol, 
        'direction' : 'BUY',
        'offset': 'OPEN',
        'volume': 2,
        'limit_price': 'LOWER_LIMIT'
    }).json()
    assert(order['code'] == 10000 and order['data']['order_id'] == my_order_id)
    print("跌停买入成功，委托ID："+str(order['data']['order_id']))
    #获取单个委托单
    order = requests.get(host_url+'/order/'+my_order_id).json()
    assert(order['code'] == 10000 and my_order_id in order['data'] and order['data'][my_order_id]['status'] == 'ALIVE')
    print("当前委托价格:"+str(order['data'][my_order_id]['limit_price']))
    #获取当前可撤委托单
    order = requests.get(host_url+'/order/alive').json()
    assert(order['code'] == 10000 and my_order_id in order['data'] and order['data'][my_order_id]['status'] == 'ALIVE')
    print("当前可撤数量:"+str(len(order['data'])))
    #取消跌停买入的单子
    order = requests.post(host_url+'/order/cancel', json={
        'order_id': my_order_id,
    }).json()
    assert(order['code'] == 10000 and order['data']['order_id'] == my_order_id)
    print("取消成功，委托ID："+str(order['data']['order_id']))

    #市价卖出
    my_order_id = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()
    order = requests.post(host_url+'/order', json={
        'order_id': my_order_id,
        'symbol' : rb_underlying_symbol, 
        'direction' : 'SELL',
        'offset': 'OPEN',
        'volume': 3,
        'limit_price':'LOWER_LIMIT'
    }).json()
    assert(order['code'] == 10000 and order['data']['order_id'] == my_order_id)

#测试清除所有今仓
def test_clear_position():
    position = requests.get(host_url+'/position').json()   
    assert(position['code'] == 10000)
    pos_num = 0
    print('持仓品种数：'+str(pos_num))
    for quote_symbol, position_info in position['data'].items():
        if(position_info['pos_short'] > 0 or position_info['pos_long'] > 0):
            pos_num+=1
    for quote_symbol, position_info in position['data'].items():
        if(position_info['pos_short_today'] > 0):
            offset = 'CLOSE'
            if('SHFE' in quote_symbol):
                offset = 'CLOSETODAY'
            order = requests.post(host_url+'/order', json={
                'symbol' : quote_symbol, 
                'direction' : 'BUY',
                'offset': offset,
                'volume': position_info['pos_short_today'],
                'limit_price':'UPPER_LIMIT'
            }).json()

        if(position_info['pos_long_today'] > 0):
            offset = 'CLOSE'
            if('SHFE' in quote_symbol):
                offset = 'CLOSETODAY'
            order = requests.post(host_url+'/order', json={
                'symbol' : quote_symbol, 
                'direction' : 'SELL',
                'offset': offset,
                'volume': position_info['pos_long_today'],
                'limit_price':'LOWER_LIMIT'
            }).json()
    time.sleep(3)
    position = requests.get(host_url+'/position').json()   
    assert(position['code'] == 10000)
    pos_num = 0
    for quote_symbol, position_info in position['data'].items():
        if(position_info['pos_short'] > 0 or position_info['pos_long'] > 0):
            pos_num+=1
    print('持仓品种数：'+str(pos_num))

def main():
    if(len(sys.argv) > 1):
        func = sys.argv[1]
        eval(func)()
    else:
        test_account()
        test_position()
        test_kqm_quote()
        test_quote()
        test_klines()
        test_ticks()
        test_order()
        time.sleep(3)
        test_clear_position()


if __name__ == '__main__':
    main()