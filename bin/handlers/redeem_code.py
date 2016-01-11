# -*- coding:utf-8 -*-
import redis
from util.misc import *
from config import RedisServer, BUSINESS_PREFIX
from util.redis_helper import RedisHash, RedisSet
from thrift_gen.redeem_code.ttypes import Code


db_redis = redis.Redis(host=RedisServer.host, port=RedisServer.port, db=RedisServer.store_db)


def create_and_validate(randomStr, bits, sets):
    """
    递归 生成 无重复的随机码
    :param randomStr:
    :param bits:
    :param sets:
    :return:
    """
    temp_code = randomStr(bits)
    t = sets.sadd(temp_code)
    if not t:
        return create_and_validate(randomStr, bits, sets)
    return temp_code


class RedeemCodeServer(object):

    def __init__(self, bid):
        self.bid = bid
        # redis hash key 用于同一业务 redis hash 的 key
        # redis set key 用于同一业务 redis set 的 key
        self.cset = RedisSet(BUSINESS_PREFIX % ('set', bid), db_redis)
        self.chash = RedisHash(BUSINESS_PREFIX % ('hash', bid), db_redis)

    def create_codes(self, quantity, bits, ctype, mark):
        """
        :param quantity: 生成兑换码数量
        :param bits:
        :param ctype: 1: 只有数字， 2:不区分大小写字母 3: 区分大小写字母  4: 字母数字混合(不区分大小写) 5: 字母数字混合(区分大小写)
        :param mark:
        :return:
        """
        if ctype not in range(1, 6):
            return []
        randomStr = globals().get('randomStr%s' % ctype, None)
        if not randomStr:
            return []
        code_list = []
        for x in xrange(quantity):
            ccode = create_and_validate(randomStr, bits, self.cset)
            if mark:
                self.chash.hset(ccode, mark)
                code = Code(code=ccode, mark=mark)
            else:
                code = Code(code=ccode, mark='')
            code_list.append(code)
        return code_list

    def load_codes(self, codes):
        """
        加载兑换码
        :param codes:
        :param mark:
        :return:
        """
        success_count = 0
        for code in codes:
            s = self.cset.sadd(code.code)
            if s:
                success_count += 1
                if code.mark:
                    self.chash.hset(code.code, code.mark)
        return success_count

    def get_codes(self, quantity, gtype):
        """
        获取兑换码
        :param gtype: 1 仅获取  2 获取并销毁
        :return:
        """
        assert isinstance(quantity, int)
        code_list = []
        if gtype == 2:
            for x in xrange(quantity):
                c = self.cset.spop()
                if c:
                    mark = self.chash.hget(c)
                    self.chash.hdel(c)
                    code = Code(code=c, mark=mark)
                    code_list.append(code)
        else:
            codes = self.cset.srandmember(quantity)
            for c in codes:
                mark = self.chash.hget(c)
                code = Code(code=c, mark=mark)
                code_list.append(code)
        if quantity == 1:
            return code_list[0] if code_list else []
        return code_list

    def code_redeem(self, codes):
        """
        兑换码兑换  销毁
        :param code:
        :return:
        """
        if isinstance(codes, basestring):
            codes = [codes]
        snum = self.cset.srem(*codes)
        self.chash.hdel(*codes)
        return snum

