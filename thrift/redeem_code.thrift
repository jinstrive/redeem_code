namespace py redeem_code


struct Code {
    1: required string code,
    2: optional string mark,
}


// 服务端异常错误
exception ServerError {
    1: required string rcode
    2: optional string message
}


service RedeemCode {
    string ping(),

    # 创建兑换码
    /*
     * bid: 业务ID 相同业务ID内 兑换码唯一(不同业务ID间兑换码不唯一)
     * quantity: 生成兑换码数量
     * bits: 兑换码位数   e.g. bits=6: '23f83x'  bits 为0 则生成 默认为4位兑换码
     * ctype: 兑换码类型  1: 只有数字， 2:不区分大小写字母 3: 区分大小写字母  4: 字母数字混合(不区分大小写) 5: 字母数字混合(区分大小写)
     * mark: 兑换码标记  无备注则填写''。如果传值，返回兑换码时携带mark信息
     * 返回所生成的兑换码
     */
    list<Code> create_codes(1:required string bid, 2:required i32 quantity, 3:required i32 bits, 4:required i32 ctype, 5:required string mark)
        throws (1:ServerError e)

    # 导入兑换码
    /*
     * bid: 业务ID 相同业务ID内 兑换码唯一(不同业务ID间兑换码不唯一)
     * codes: 需导入的兑换码
     * mark: 兑换码标记  可选。如果传值，返回兑换码时携带mark信息
     *
     */
    i32 load_codes(1:required string bid, 2:required list<Code> codes)
        throws (1:ServerError e)

    # 随机获取单个兑换码 视为已使用
    /*
     * bid: 业务ID 相同业务ID内 兑换码唯一(不同业务ID间兑换码不唯一)
     * gtype: 获取方式  1 仅获取   2 获取并销毁
     *
     */
    Code get_code(1:required string bid, 2:required i32 gtype) throws (1:ServerError e)

    # 随机获取多个兑换码 视为已使用
    /*
     * bid: 业务ID 相同业务ID内 兑换码唯一(不同业务ID间兑换码不唯一)
     * gtype: 获取方式  1 仅获取   2 获取并销毁
     * quantity: 获取数量
     */
    list<Code> get_codes(1:required string bid, 2:required i32 quantity, 3:required i32 gtype) throws (1:ServerError e)

    # 兑换码使用销毁
    /*
     * bid: 业务ID 相同业务ID内 兑换码唯一(不同业务ID间兑换码不唯一)
     * code: 兑换码
     * 兑换码使用后，应调用 code_redeem接口，释放资源。 也可再次生成
     */
    bool code_redeem(1:required string bid, 2:required string code) throws (1:ServerError e)

}
