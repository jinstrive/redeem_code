#coding:utf8

import random


# 1: 只有数字， 2:不区分大小写字母 3: 区分大小写字母  4: 字母数字混合(不区分大小写) 5: 字母数字混合(区分大小写)

def randomStr1(n=16):
    """
    生成字符串  只有数字
    :param n:
    :return:
    """
    SAMPLE = '0123456789'
    return ''.join([random.choice(SAMPLE) for _i in xrange(n)])


def randomStr2(n=16):
    """
    生成字符串  2:不区分大小写字母
    :param n:
    :return:
    """
    SAMPLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join([random.choice(SAMPLE) for _i in xrange(n)])


def randomStr3(n=16):
    """
    3: 区分大小写字母
    :param n:
    :return:
    """
    SAMPLE = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join([random.choice(SAMPLE) for _i in xrange(n)])


def randomStr4(n=16):
    """
    4: 字母数字混合(不区分大小写)
    :param n:
    :return:
    """
    SAMPLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join([random.choice(SAMPLE) for _i in xrange(n)])


def randomStr5(n=16):
    """
    5: 字母数字混合(区分大小写)
    :param n:
    :return:
    """
    SAMPLE = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join([random.choice(SAMPLE) for _i in xrange(n)])


def main():
    print randomStr1(32)
    print randomStr2(32)
    print randomStr3(32)
    print randomStr4(32)
    print randomStr5(32)

if __name__=='__main__':
    main()
