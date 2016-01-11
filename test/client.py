# coding: utf-8
import time, random
import traceback
import random, operator
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

class Selector:
    def __init__(self, serverlist, policy='round_robin'):
        self.servers = []
        self.pos = 0
        self.policy = policy
        for item in serverlist:
            newitem = {}
            newitem['server'] = item
            newitem['valid']  = True
            newitem['timestamp'] = 0
            self.servers.append(newitem)

        self._op_map = {
            '=':  'eq',
            '!=': 'ne',
            '>':  'gt',
            '>=': 'ge',
            '<':  'lt',
            '<=': 'le',
            'in': 'contains',
        }

    def filter_by_rule(self, input):
        if not input:
            return self.servers
        serv = []
        addition_server = []
        for item in self.servers:
            rule = item['server'].get('rule', '')
            if not rule:
                addition_server.append(item)
                continue
            for r in rule:
                name, op, value = r
                v = input.get(name, '')
                if not v:
                    break
                if not getattr(operator, self._op_map[op])(v, value):
                    break
            else:
                serv.append(item)
        if not serv:
            return addition_server
        return serv

    def next(self, input=None):
        return getattr(self, self.policy)(input)

    def round_robin(self, input=None):
        server_valid = []
        servers = self.filter_by_rule(input)
        i = 0;
        for item in servers:
            if item['valid']:
                server_valid.append(item)
                i += 1
        if i == 0:
            return None
        select = server_valid[self.pos % i]
        self.pos = (self.pos + 1) % len(server_valid)
        #log.debug("select:%s, i:%d", select, i)
        return select


    def random(self, input=None):
        server_valid = []
        servers = self.filter_by_rule(input)
        i = 0
        for item in servers:
            if item['valid'] == True:
                server_valid.append(item)
                i += 1
        if i == 0:
            return None
        index = random.randint(0, i-1)
        return server_valid[index]

    def not_valid(self, input=None):
        notvalid = []
        servers = self.filter_by_rule(input)
        for item in servers:
            if not item['valid']:
                notvalid.append(item)
        return notvalid


class ThriftClientError(Exception):
    pass

class ThriftClient:
    def __init__(self, server, thriftmod, timeout=0, framed=False, raise_except=False):
        '''server - 为Selector对象，或者地址{'addr':('127.0.0.1',5000),'timeout':1000}'''
        self.starttime = time.time()
        self.server_selector  = None
        self.server = None
        self.client = None
        self.thriftmod    = thriftmod
        self.frame_transport = framed
        self.raise_except = raise_except  # 是否在调用时抛出异常

        self.timeout = timeout

        if isinstance(server, dict): # 只有一个server
            self.server = [server,]
            self.server_selector = Selector(self.server, 'random')
        elif isinstance(server, list): # server列表，需要创建selector，策略为随机
            self.server = server
            self.server_selector = Selector(self.server, 'random')
        else: # 直接是selector
            self.server_selector = server
        while True:
            if self.open() == 0:
                break

    def open(self):
        starttime = time.time()
        err = ''
        self.transport = None
        #try:
        self.server = self.server_selector.next()
        if not self.server:
            restore(self.server_selector, self.thriftmod)

            self.server = self.server_selector.next()
            if not self.server:
                raise ThriftClientError
        addr = self.server['server']['addr']

        try:
            self.transport = TSocket.TSocket(addr[0], addr[1])
            if self.timeout > 0:
                self.transport.setTimeout(self.timeout)
            else:
                self.transport.setTimeout(self.server['server']['timeout'])
            if self.frame_transport:
                self.transport = TTransport.TFramedTransport(self.transport)
            else:
                self.transport = TTransport.TBufferedTransport(self.transport)
            protocol = TBinaryProtocol.TBinaryProtocol(self.transport)

            self.client = self.thriftmod.Client(protocol)
            self.transport.open()
        except Exception, e:
            err = str(e)
            self.server['valid'] = False

            if self.transport:
                self.transport.close()
                self.transport = None
        finally:
            endtime = time.time()
            addr = self.server['server']['addr']
            tname = self.thriftmod.__name__
            pos = tname.rfind('.')
            if pos > 0:
                tname = tname[pos+1:]
            s = 'server=%s|func=open|addr=%s:%d/%d|time=%d' % \
                    (tname,
                    addr[0], addr[1],
                    self.server['server']['timeout'],
                    int((endtime-starttime)*1000000),
                    )
            if err:
                s += '|err=%s' % repr(err)
        if not err:
            return 0
        return -1

    def __del__(self):
        self.close()

    def close(self):
        if self.transport:
            self.transport.close()
            self.transport = None
            self.client = None

    def call(self, funcname, *args, **kwargs):
        def _call_log(ret, err=''):
            endtime = time.time()
            addr = self.server['server']['addr']
            tname = self.thriftmod.__name__
            pos = tname.rfind('.')
            if pos > 0:
                tname = tname[pos+1:]

            retstr = str(ret)
            if tname == 'Encryptor' and ret:
                retstr = str(ret.code)
            s = 'server=%s|func=%s|addr=%s:%d/%d|time=%d|args=%s|kwargs=%s' % \
                    (tname, funcname,
                    addr[0], addr[1],
                    self.server['server']['timeout'],
                    int((endtime-starttime)*1000000),
                    args, kwargs)
            if err:
                s += '|ret=%s|err=%s' % (retstr, repr(err))

        starttime = time.time()
        ret = None
        try:
            func = getattr(self.client, funcname)
            ret = func(*args, **kwargs)
        except Exception, e:
            _call_log(ret, e)
            if self.raise_except:
                raise
        else:
            _call_log(ret)
        return ret

    def __getattr__(self, name):
        def _(*args, **kwargs):
            return self.call(name, *args, **kwargs)
        return _

def restore(selector, thriftmod, framed=False):
    invalid = selector.not_valid()
    for server in invalid:
        transport = None
        try:
            addr = server['server']['addr']
            transport = TSocket.TSocket(addr[0], addr[1])
            transport.setTimeout(server['server']['timeout'])
            if framed:
                transport = TTransport.TFramedTransport(transport)
            else:
                transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = thriftmod.Client(protocol)
            transport.open()
            client.ping()
        except:
            continue
        finally:
            if transport:
                transport.close()

        log.debug('restore ok %s', server['server']['addr'])
        server['valid'] = True

