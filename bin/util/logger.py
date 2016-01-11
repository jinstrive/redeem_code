import logging
import logging.config
import multiprocessing
import threading
import sys
import traceback
import time
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

logging.NOTE = 25
logging.addLevelName(logging.NOTE, "NOTE")
logging.MPAY = 15
logging.addLevelName(logging.MPAY, "MPAY")
logging.RISK = 35
logging.addLevelName(logging.RISK, "RISK")

def note(self, message, *args, **kws):
    self._log(logging.NOTE, message, args, **kws)
def mpay(self, message, *args, **kws):
    self._log(logging.MPAY, message, args, **kws)
def risk(self, message, *args, **kws):
    self._log(logging.RISK, message, args, **kws)


logging.Logger.note = note
logging.Logger.mpay = mpay
logging.Logger.risk = risk
LEVEL_COLOR = {
    logging.DEBUG: '\33[2;39m',
    logging.INFO: '\33[0;37m',
    logging.MPAY: '\33[0;37m',
    logging.RISK: '\33[0;37m',
    logging.NOTE: '\033[0;36m',
    logging.WARN: '\33[4;35m',
    logging.ERROR: '\33[0;31m',
    logging.FATAL: '\33[7;31m'
}


class MyTimedRotatingFileHandler(TimedRotatingFileHandler):

    def doRollover(self):
        if self.stream:
            self.stream.close()

        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        if not os.path.exists(dfn):
            os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        self.mode = 'a'
        self.stream = self._open()
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)

        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:
                    newRolloverAt = newRolloverAt - 3600
                else:
                    newRolloverAt = newRolloverAt + 3600

        self.rolloverAt = newRolloverAt


class ScreenHandler (logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            fs = LEVEL_COLOR[record.levelno] + "%s\n" + '\33[0m'
            try:
                if isinstance(msg, unicode) and getattr(stream, 'encoding', None):
                    ufs = fs.decode(stream.encoding)
                    try:
                        stream.write(ufs % msg)
                    except UnicodeEncodeError:
                        stream.write((ufs % msg).encode(stream.encoding))
                else:
                    stream.write(fs % msg)
            except UnicodeError:
                stream.write(fs % msg.encode("UTF-8"))

            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class MultiProcessingLog(logging.Handler):
    def __init__(self, filename, mode='timed', max_bytes=0, backup_count=0):
        logging.Handler.__init__(self)
        self.queue = multiprocessing.Queue(-1)

        if mode == 'timed':
            self._handler = TimedRotatingFileHandler(filename, 'midnight', 1, backup_count)
        else:
            self._handler = RotatingFileHandler(filename, 'a', max_bytes, backup_count)

        t = threading.Thread(target=self.receive)
        t.daemon = True
        t.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def receive(self):
        while self.queue.empty() == False:
            try:
                record = self.queue.get()
                self._handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def send(self, s):
        self.queue.put_nowait(s)

    def _format_record(self, record):
        # ensure that exc_info and args
        # have been stringified.  Removes any chance of
        # unpickleable things inside and possibly reduces
        # message size sent over the pipe
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            dummy = self.format(record)
            record.exc_info = None

        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self._handler.close()
        logging.Handler.close(self)


class SingleLevelFilter(logging.Filter):
    def __init__(self, passlevel, reject=False):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return record.levelno != self.passlevel
        else:
            return record.levelno == self.passlevel


def initlog(config, console=False, backup_count=0, separate=True):
    conf = {
        'version': 1,
        'formatters': {
            'myformat': {
                'format': '%(asctime)s %(process)d,%(threadName)s %(filename)s:%(lineno)d [%(levelname)s] %(message)s'
            }
        },
        'filters': {
            'debug': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.DEBUG
            },
            'info': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.INFO
            },
            'note': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.NOTE
            },
            'mpay': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.MPAY
            },
            'risk': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.RISK
            },
            'warn': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.WARN
            },
            'error': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.ERROR
            },
            'critical': {
                '()': 'util.logger.SingleLevelFilter',
                'passlevel': logging.CRITICAL
            }
        },
        'handlers': {
            'console': {
                'class': 'util.logger.ScreenHandler',
                'formatter': 'myformat',
                'level': 'DEBUG',
                'stream': 'ext://sys.stdout'
            }
        },
        'root': {
            'level': 'DEBUG'
        }
    }

    handlers = ['console'] if console else []
    for level, name in config.iteritems():
        handler = '%s_FILE' % level
        handlers.append(handler)
        conf['handlers'][handler] = {
            'class': 'util.logger.MyTimedRotatingFileHandler',
            'filename': name,
            'when': 'midnight',
            'interval': 1,
            'formatter': 'myformat',
            'level': level.upper(),
            'backupCount': backup_count,
            'filters': [level.lower()] if separate else None
        }

    conf['root'].update({'handlers': handlers})
    logging.config.dictConfig(conf)
    return logging.getLogger()
