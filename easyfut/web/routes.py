from easyfut.web.handlers.account import AccountHandler
from easyfut.web.handlers.order import OrderHandler
from easyfut.web.handlers.quote import QuotesHandler
from easyfut.web.handlers.position import PositionHandler
from easyfut.web.handlers.klines import KlinesHandler
from easyfut.web.handlers.ticks import TicksHandler

#创建路由
def createRoutes(share_dict, message_queue):
    routes = []
    url2handler = {
        r"/account"                         : AccountHandler,
        r"/quote([\/a-zA-Z0-9\.\,]*)"       : QuotesHandler,
        r"/klines([\/a-zA-Z0-9\.\,\_]*)"    : KlinesHandler,
        r"/ticks([\/a-zA-Z0-9\.\,\_]*)"     : TicksHandler,
        r"/order([\/a-zA-Z0-9\,]*)"         : OrderHandler,
        r"/position"                        : PositionHandler,

    }
    for url, handler, in url2handler.items():
        routes.append((url, handler, {'share_dict': share_dict, 'message_queue': message_queue}))
    return routes

