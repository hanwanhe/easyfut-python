from multiprocessing import Manager, Queue
import argparse, configparser
from easyfut.server import TqsdkServer, Webserver
import signal
import sys
import os


def run():
    # 传参解析
    parser = argparse.ArgumentParser()
    group  = parser.add_mutually_exclusive_group(required=True)
    # 启动使用的配置文件
    group.add_argument('-c', metavar="configuration file", help="Specify the configuration file required to start EasyFut")
    # 生成配置文件的地址
    group.add_argument('-n', metavar="configuration file",help="Generate a new configuration file")
    # 解析传参
    args = parser.parse_args()
    # 创建模板配置文件
    if(args.n is not None):
        if (os.path.exists(args.n) == True):
            print("配置文件 " + args.n + " 已存在！")
            sys.exit(-1)
        source = open(os.path.join(os.path.dirname(__file__), 'conf', 'easyfut-template.conf'), "r", encoding="utf-8")
        dest = open(args.n, "w", encoding="utf-8")
        line = source.readline()
        while line:
            dest.write(line)
            line = source.readline()
        source.close()
        dest.close()
        print("配置文件 " + args.n + " 创建成功！")
        return

    #判断配置文件存在
    if(os.path.exists(args.c) == False):
        print("配置文件 "+args.c+" 不存在！")
        sys.exit(-1)
    # 解析配置文件
    app_config = configparser.ConfigParser()
    app_config.read(args.c, encoding="utf-8")
    # 进程间共享变量
    manager = Manager()
    share_dict = manager.dict()
    share_dict['tqsdkserver_alive'] = True
    share_dict['webserver_ready'] = False
    # 进程间消息队列
    message_queue = {
        'order'     : Queue(),
        'quote'     : Queue(),
        'klines'    : Queue(),
        'ticks'     : Queue()
    }
    # tqsdk 服务进程启动
    tqsdkserver = TqsdkServer(app_config, share_dict, message_queue)
    tqsdkserver.start()
    # http 服务进程启动
    webserver = Webserver(app_config, share_dict, message_queue)
    webserver.start()
    # 监听kill信号
    def signal_handler(signal, frame):
        tqsdkserver.terminate()
        webserver.terminate()
        manager.shutdown()
        sys.exit(0)
    signal.signal(signal.SIGTERM, signal_handler)
    # 等待子进程完成
    tqsdkserver.join()
    # 标记进程死掉
    share_dict['tqsdkserver_alive'] = False
    webserver.join()


