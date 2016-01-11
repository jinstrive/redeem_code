# -*- coding:utf-8 -*-
from client import ThriftClient
from bin.thrift_gen.redeem_code import RedeemCode

REDEEM_SERVER = [{'addr': ('127.0.0.1', 9500), 'timeout': 2000}]


def test_create_codes(bid='test_codes', quantity=10, bits=10, ctype=2, mark=''):
    bid = 'test_codes'
    client = ThriftClient(REDEEM_SERVER, RedeemCode)
    ret = client.call('create_codes', bid, quantity, bits, ctype, mark)
    print ret


def test_get_code(gtype=1):
    bid = 'test_codes'
    client = ThriftClient(REDEEM_SERVER, RedeemCode)
    ret = client.call('get_code', bid, gtype)
    print ret


def test_get_codes(quantity=10, gtype=1):
    bid = 'test_codes'
    client = ThriftClient(REDEEM_SERVER, RedeemCode)
    ret = client.call('get_codes', bid, quantity, gtype)
    print len(ret), ret


def test_redeem_code(bid='test_codes', code=''):
    bid = 'test_codes'
    client = ThriftClient(REDEEM_SERVER, RedeemCode)
    ret = client.call('code_redeem', bid, code)
    print ret



if __name__ == '__main__':
    # test_create_codes(quantity=10)
    # test_get_code()
    test_get_codes(100, 2)
    # test_redeem_code(code='ZPPOHKQAOO')