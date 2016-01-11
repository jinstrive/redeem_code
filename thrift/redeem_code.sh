#!/bin/sh
thrift -out ../bin/thrift_gen/ -gen py:new_style redeem_code.thrift
