# coding: utf-8
import os
import sys

from util.logger import initlog


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_PATH = os.path.dirname(ROOT_PATH)
GRAY_VERSION = os.path.basename(ROOT_PATH)
log = initlog({
    'INFO': '%s/log/redeem_code_info_%s.log' % (PROJECT_PATH, GRAY_VERSION),
    'NOTE': '%s/log/redeem_code_note_%s.log' % (PROJECT_PATH, GRAY_VERSION),
    'WARN': '%s/log/redeem_code_info_%s.log' % (PROJECT_PATH, GRAY_VERSION),
    'ERROR': '%s/log/redeem_code_error_%s.log' % (PROJECT_PATH, GRAY_VERSION),
}, backup_count=0, console=True)

