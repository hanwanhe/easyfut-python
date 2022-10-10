# EasyFut

#### 介绍

简单期货HTTP交易接口，基于TqSdk。

#### 安装&启动教程

1.pip install easyfut

2.创建配置文件 easyfut -n easyfut.conf

3.修改 easyfut.conf 配置文件内容

4.命令行启动 easyfut -c easyfut.conf

#### 使用说明（curl演示）

#获取账户信息

curl http://127.0.0.1:8888/account

#获取当前持仓

curl http://127.0.0.1:8888/position

#获取实时行情

curl http://127.0.0.1:8888/quote/SHFE.rb2210

#获取K线行情

curl http://127.0.0.1:8888/klines/SHFE.rb2210_60_20

#获取Tick序列

curl http://127.0.0.1:8888/ticks/SHFE.rb2210_20   

#委托下单

curl -X POST -H "Content-type: application/json" -d '{"symbol":"SHFE.rb2210", "direction":"BUY","offset":"OPEN","volume":1,"limit_price":"UPPER_LIMIT"}' http://127.0.0.1:8888/order

#取消委托单

curl -X POST -H "Content-type: application/json" -d '{"order_id":"f1786bea1ad045199925deea3cd6f1c7"}' http://127.0.0.1:8888/order/cancel

#获取委托单信息

curl http://127.0.0.1:8888/order/fbcce9326a3a4f8c80295b0e6e07434a

#获取当日可撤委托

curl http://127.0.0.1:8888/order/alive


#更多详见官方文档 [https://easyfut.iweiai.com/doc](https://easyfut.iweiai.com/doc) 

