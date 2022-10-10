
rcodes = {
    'suc'                       : {'code': 10000, 'msg': '操作成功！'},
    'tq_error'                  : {'code': 10001, 'msg': '服务异常，需要重启EasyFut！' },
    'tq_wait'                   : {'code': 10002, 'msg': '底层TqSdk服务正在启动，请耐心等待几秒钟！' },
    'request_param_error'       : {'code': 10003, 'msg': '传参错误，请检查您的传参！' },
    'operate_timeout'           : {'code': 10004, 'msg': '操作超时，请确保传参正确后重试！' },
    'order_not_exists'          : {'code': 10005, 'msg': '该委托单不存在，请检查传入参数是否正确！' },
    'order_finished'            : {'code': 10006, 'msg': '该委托单已完成，无法取消！' },
    'order_unique_error'        : {'code': 10007, 'msg': '委托单ID重复提交！' }
}