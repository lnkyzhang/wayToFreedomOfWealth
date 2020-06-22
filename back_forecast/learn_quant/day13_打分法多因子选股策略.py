# 可以自己import我们平台支持的第三方python模块，比如pandas、numpy等。
# - 1、回测区间：
#   - 2010-01-01  ~  2018-01-01
# - 2、选股：
#   - 选股因子：6个已知方向的因子
#     - 市值-market_cap、市盈率-pe_ratio、市净率-pb_ratio
#     - ROIC-return_on_invested_capital、inc_revenue-营业总收入 和inc_profit_before_tax-利润增长率
#   - 数据处理：处理缺失值
#   - 选股权重：
#     - 因子升序从小到大分10组，第几组为所在组得分
#     - 因子降序从大到小分10组，第几组为所在组得分
#   - 选股范围：
#       - 选股的指数、模块：全A股
# - 3、调仓周期：
#   - 调仓：每月进行一次调仓选出20个排名靠前的股票
#   - 交易规则：卖出已持有的股票
#   - 买入新的股票池当中的股票
import pandas as pd


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # # 在context中保存全局变量
    # context.s1 = "000001.XSHE"
    # # 实时打印日志
    # logger.info("RunInfo: {}".format(context.run_info))
    # 限定股票池的股票数量
    context.stocknum = 20

    context.up = ['market_cap', 'pe_ratio', 'pb_ratio']

    # 运行按月定时函数
    scheduler.run_monthly(score_select, tradingday=1)


def score_select(context, bar_dict):
    """打分法选股函数
    """
    # 1、选出因子数据、进行缺失值处理
    q = query(
        fundamentals.eod_derivative_indicator.market_cap,
        fundamentals.eod_derivative_indicator.pe_ratio,
        fundamentals.eod_derivative_indicator.pb_ratio,
        fundamentals.financial_indicator.return_on_invested_capital,
        fundamentals.financial_indicator.inc_revenue,
        fundamentals.financial_indicator.inc_profit_before_tax
    )

    fund = get_fundamentals(q)

    factors_data = fund.T

    factors_data = factors_data.dropna()

    # 2、定义打分函数、确定股票池
    select_stocklist(context, factors_data)

    # 3、定义调仓函数
    rebalance(context)


def select_stocklist(context, factors_data):
    """打分的具体步骤、返回股票池
    因子升序从小到大分10组，第几组为所在组得分
        市值-market_cap、市盈率-pe_ratio、市净率-pb_ratio
    因子降序从大到小分10组，第几组为所在组得分
        ROIC-return_on_invested_capital、inc_revenue-营业总收入 和inc_profit_before_tax-利润增长率
    """
    # 循环每个因子去处理
    for name in factors_data.columns:

        # 因子升序的，进行升序排序
        if name in context.up:

            factor = factors_data.sort_values(by=name)[name]

        else:
            # 因子降序的，进行降序排序

            factor = factors_data.sort_values(by=name, ascending=False)[name]

        # 对单个因子进行打分处理
        # 新建一个因子分数列
        factor = pd.DataFrame(factor)

        factor[name + 'score'] = 0

        # 进行打分
        # 先求出每组数量，然后根据数量一次给出分数
        stock_groupnum = len(factors_data) // 10

        for i in range(10):

            if i == 9:
                factor[name + 'score'][(i + 1) * stock_groupnum:] = i + 1

            factor[name + 'score'][i * stock_groupnum: (i + 1) * stock_groupnum] = i + 1

        # 把每个因子的得分进行合并到原来因子数据当中
        factors_data = pd.concat([factors_data, factor[name + 'score']], axis=1)

    # logger.info(factors_data)
    # 对6个因子的分数列进行求和
    all_score = factors_data[
        ['market_capscore', 'pe_ratioscore', 'pb_ratioscore', 'return_on_invested_capitalscore', 'inc_revenuescore',
         'inc_profit_before_taxscore']].sum(1).sort_values()

    # 定义股票池
    context.stock_list = all_score.index[:context.stocknum]

    logger.info(context.stock_list)


def rebalance(context):
    """
    调仓函数
    卖出、买入
    """
    # 卖出
    for stock in context.portfolio.positions.keys():

        if stock not in context.stock_list:
            order_target_percent(stock, 0)

    # 买入
    for stock in context.stock_list:
        order_target_percent(stock, 1.0 / len(context.stock_list))


# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    pass


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑

    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合信息

    # 使用order_shares(id_or_ins, amount)方法进行落单

    # TODO: 开始编写你的算法吧！
    # order_shares(context.s1, 1000)
    pass


# after_trading函数会在每天交易结束后被调用，当天只会被调用一次
def after_trading(context):
    pass