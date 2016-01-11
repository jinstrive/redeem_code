# coding: utf-8
# import os
# import sys
from functools import partial
import redis
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class RedisObject(object):

    def __init__(self, key, redis_instance):
        self.redis_instance = redis_instance
        self._key = str(key)

    def __getattr__(self, method):
        return partial(getattr(self.redis_instance, method), self._key)


class RedisString(RedisObject):

    def get_number(self):
        num = self.redis_instance.get(self._key)
        if not num:
            num = 0
        return num


class RedisHash(RedisObject):

    def incr_num(self, field, amount=1):
        return self.redis_instance.hincrby(self._key, field, amount)

    def decr_num(self, field, amount=1):
        return self.redis_instance.hincrby(self._key, field, 0 - amount)

    def get_num(self, field):
        num = self.redis_instance.hget(self._key, field)
        if not num:
            num = 0
        return int(num)


class RedisSet(RedisObject):

    def is_exist(self, data):
        return self.redis_instance.sismember(self._key, data)


class RedisSortedSet(RedisObject):

    def incrby(self, field, amount=1):
        return self.redis_instance.zincrby(self._key, field, amount)

    def decrby(self, field, amount=-1):
        return self.redis_instance.zincrby(self._key, field, amount)


if __name__ == '__main__':
    r = redis.StrictRedis()
    r.zrange
    robj = RedisObject('test', r)
    print robj.set('11111')
    hobj = RedisObject('hashtest', r)
    print hobj.hset('order', '12345')
    zobj = RedisObject('zsettest', r)
    zobj.zadd(1, 'a', 2, 'b', 0.5, 'c')
    print zobj.zrange(0, -1)

