from backtrader.indicators import BaseApplyN
import backtrader as bt
import enum

from BackTraderTest.BackTraderFunc.Indicator.JXMJInd import JXMJIndicator


def findExtreme(x, direction):
    '''
    查找极值
    :param x: 输入的array
    :param direction: 'peak' 'bottom'
    :return:
    '''
    func = None
    if direction == "peak":
        func = max
    elif direction =="bottom":
        func = min
    centerIndex = int((len(x) - 1) / 2)

    #if func(x) == x[centerIndex]:
    if (x.index(func(x))) == centerIndex:
        return x[centerIndex]
    else:
        return float('nan')


class State(enum.Enum):
    prepare_intensive = 1             # 行情启动前准备期
    prepare_shock = 2 # 均线密集震仓


    divergence = 10          # 大幅乖离期
    react = 20               # 中期回调后稳定
    rise = 30                # 上涨
    fall = 40                # 下跌


class StateInd(bt.Indicator):
    '''
    prepare启动前准备：
        近期21日均线密集19日以上
    divergence大幅乖离：
        状态进入：
        20日均线与60日均线乖离率在过去144天内高于99%
        20日均线与120日均线乖离率在过去144天内高于99%
        状态解除：
        20日均线与60日均线乖离率在过去144天内低于90%
        20日均线与120日均线乖离率在过去144天内低于90%
        natr在过去144天内低于60%
    react中期回调后稳定：
        ？
    rise上涨：
        均线多头排列
    fall下跌：
        均线空头排列


    '''
    # alias = ('PctRankAbs',)
    lines = ('State','priceIntense','natrIntense','bollIntense')
    plotinfo = dict(
        subplot=True, plotlinelabels=True,
    )

    # plotlines = dict(
    #     Peaks=dict(marker='*', markersize=8.0, color='black', fillstyle='full'),
    #     Bottoms=dict(marker=".", markersize=8.0, color='black', fillstyle='full'),
    #     # expired=dict(marker='s', markersize=8.0, color='red', fillstyle='full')
    # )

    params = (
        ('period', 9),
        # ('func', func),
        # ('func', lambda d: fsum(abs(x) < abs(d[-1]) for x in d) / len(d)),
    )

    def __init__(self):
        self.jxmj = JXMJIndicator(self.data)
        self.l.State = bt.If(self.jxmj.l.JXMJ == 1, 1, self.l.State)
        self.l.priceIntense = bt.If(self.jxmj.l.priceIntense == 1, 0.7, float('nan'))
        self.l.natrIntense = bt.If(self.jxmj.l.natrIntense == 1, 0.4, float('nan'))
        self.l.bollIntense = bt.If(self.jxmj.l.bollIntense == 1, 0.1, float('nan'))



    def next(self):
        pass