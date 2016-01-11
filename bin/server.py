# -*- coding:utf-8 -*-
import os, sys
import time
import signal
import traceback
from functools import wraps

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

HOME = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(HOME), 'conf'))

# 不同配置文件加载

if __name__ == '__main__':
    config_name = None
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    libpath = [
        os.path.join(os.path.dirname(HOME), 'conf'),
        os.path.dirname(os.path.dirname(HOME)),
    ]
    for path in libpath:
        if os.path.isdir(path):
            sys.path.append(path)
    if config_name:
        config_file = 'config_' + config_name
        sys.modules['config'] = __import__(config_file)

import config
from init_log import log
from handlers.redeem_code import RedeemCodeServer
from thrift_gen.redeem_code import RedeemCode
from thrift_gen.redeem_code.ttypes import ServerError


def log_api_call(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        start_time = time.time()
        log_fields = []
        log_fields.append('method=%s' % func.func_name)
        log_fields.append('query=%s' % [str(arg) for arg in args])
        try:
            result = func(self, *args, **kwargs)
            log_fields.append('time=%.3f' % ((time.time() - start_time) * 1000))
            log_fields.append('ret=%s' % result)
            log.note('|'.join(log_fields))
            return result
        except ServerError as e:
            log_fields.append('time=%.3f' % ((time.time() - start_time) * 1000))
            log_fields.append('ret=error')
            log_fields.append('error=%s' % e.message)
            log.note('|'.join(log_fields))
            raise ServerError(e.rcode, e.message)
        except Exception as e:
            log_fields.append('time=%.3f' % ((time.time() - start_time) * 1000))
            log_fields.append('ret=error')
            log_fields.append('error=%s' % e.message)
            note_log = '|'.join(log_fields)
            log.note(note_log)
            log.exception('%s%s' % (note_log, e))
            raise ServerError('unknown', 'server error')
    return wrapped


class APIRecorder(type):

    def __new__(cls, cls_nm, cls_parents, cls_attrs):
        for attr_nm in cls_attrs:
            if not attr_nm.startswith("__") and callable(cls_attrs[attr_nm]):
                cls_attrs[attr_nm] = log_api_call(cls_attrs[attr_nm])
        return super(APIRecorder, cls).__new__(cls, cls_nm, cls_parents, cls_attrs)


class RedeemCodeHandler(object):

    __metaclass__ = APIRecorder

    def ping(self):
        return 'OK'

    def create_codes(self, bid, quantity, bits, ctype, mark):
        """
        生成兑换码
        :param bid:
        :param quantity:
        :param bits:
        :param ctype:
        :param mark:
        :return:
        """
        s = RedeemCodeServer(bid)
        return s.create_codes(quantity, bits, ctype, mark)

    def load_codes(self, bid, codes):
        """
        加载兑换码
        :param bid:
        :param codes:
        :param mark:
        :return:
        """
        s = RedeemCodeServer(bid)
        return s.load_codes(codes)

    def get_code(self, bid, gtype):
        """
        获取兑换码
        :param bid:
        :return:
        """
        s = RedeemCodeServer(bid)
        return s.get_codes(1, gtype)

    def get_codes(self, bid, quantity, gtype):
        """
        获取指定数量兑换码
        :param bid:
        :param quantity:
        :return:
        """
        s = RedeemCodeServer(bid)
        return s.get_codes(quantity, gtype)

    def code_redeem(self, bid, code):
        """
        兑换码使用、销毁
        :param bid:
        :param code:
        :return:
        """
        s = RedeemCodeServer(bid)
        rnum = s.code_redeem(code)
        return True if rnum else False


def start_log():
    '''服务启动日志'''
    log.info('Starting the server...')
    log.info('host:%s', config.HOST)
    log.info('port:%d', config.PORT)
    log.info('thread_num:%d', config.threads)

def server():
    handler = RedeemCodeHandler()
    processor = RedeemCode.Processor(handler)
    transport = TSocket.TServerSocket(host=config.HOST, port=config.PORT)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    thrift_server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
    thrift_server.setNumThreads(config.threads)

    start_log()

    try:
        thrift_server.serve()
    except KeyboardInterrupt:
        log.info('server done.')
        os.kill(os.getpid(), signal.SIGTERM)
        sys.exit(0)

    log.info('server done.')



if __name__ == '__main__':
    server()

