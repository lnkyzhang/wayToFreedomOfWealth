from mt_com_setting import *
from mt_read_data import *



code_df = pd.DataFrame()
def mt_add_suffix_name(code, rule=1):
    '''
    给rqalpha添加后缀名，比如000651返回000651.xshe
    如果传入的code是包含后缀名的，则直接返回
    .xshe:深证    SZ
    .xshg:上海    SH
    @param code: 股票的string
    @return: 返回带有后缀名的string
    @param rule:    rule=1,则添加后缀名为.XSHE XSHG .
                    rule=2，则添加后缀名为SZ,SH
    '''

    global code_df
    if code_df.empty:
        code_df = mt_read_stock_basic("2020-04-01")

        def func(x):
            code_str = x['ts_code']
            if '.SZ' in code_str:
                result = code_str.replace('.SZ', '.XSHE')
            elif '.SH' in code_str:
                result = code_str.replace('.SH', '.XSHG')

            return result

        if rule == 1:
            code_df['suffix_name'] = code_df.apply(func, axis=1, args=())
        elif rule == 2:
            code_df['suffix_name'] = code_df['ts_code']

    if isinstance(code, list):
        code_suffix = code_df.loc[code_df['symbol'].isin(code)]['suffix_name'].to_list()
    elif isinstance(code, pd.Series):
        code_suffix = code_df.loc[code_df['symbol'].isin(code)]['suffix_name']
    elif isinstance(code, str):
        if ".XSH" in code:
            return code
        code_suffix = code_df[code_df['symbol'] == code]['suffix_name'].values[0]

    return code_suffix


def mt_select_stocklist(factors_data, stock_counts):
    """
    首先处理NaN值情况.选股时的日线数据不能是复权的数据，否则计算的pe等值是不正确的
    打分的具体步骤、返回股票池
    因子升序从小到大分10组，第几组为所在组得分
    市值-market_cap、市盈率-pe_ratio、市净率-pb_ratio
    因子降序从大到小分10组，第几组为所在组得分
    ROIC-return_on_invested_capital、inc_revenue-营业总收入 和inc_profit_before_tax-利润增长率
    @param stock_counts: 排名前多少个
    @param factors_data:
    @return:
    """
    factors_data.to_csv('factor.csv', mode='a')
    # 循环每个因子去处理
    factors_data = factors_data.dropna(axis=0, how='all')

    sort_up = ['market_cap', 'pe_ratio', 'pb_ratio']
    for name in factors_data.columns:
        if name in sort_up:
            factor = factors_data.sort_values(by=name)[name]
        else:
            factor = factors_data.sort_values(by=name, ascending=False)[name]

        factor = pd.DataFrame(factor)
        factor[name + '_score'] = 0

        # 进行打分
        # 先求出每组数量，然后根据数量一次给出分数
        stock_groupnum = len(factors_data) // 10
        for i in range(10):
            if i == 9:
                factor.loc[(i + 1) * stock_groupnum:, name + '_score'] = i + 1
            factor.loc[i * stock_groupnum: (i + 1) * stock_groupnum, name + '_score'] = i + 1
        factors_data = pd.concat([factors_data, factor[name + '_score']], axis=1, sort=False)

    all_score = factors_data[
        ['market_cap_score', 'pe_ratio_score', 'pb_ratio_score', 'roic_score', 'ors_score',
         'npgr_score']].sum(1).sort_values()

    # tem_df = pd.DataFrame([factors_data])
    # tem_df["date"] = str(self.running_time)[:10]
    factors_data.to_csv('all_score.csv', mode='a')

    hold_list = all_score.index[:stock_counts].tolist()
    return hold_list


