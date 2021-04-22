from backtrader.indicators import BaseApplyN
import backtrader as bt


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




class PeaksInd(bt.Indicator):
    alias = ('PctRankAbs',)
    lines = ('Peaks','Bottoms')
    plotinfo = dict(
        subplot=False, plotlinelabels=True,
    )

    plotlines = dict(
        Peaks=dict(marker='*', markersize=8.0, color='black', fillstyle='full'),
        Bottoms=dict(marker=".", markersize=8.0, color='black', fillstyle='full'),
        # expired=dict(marker='s', markersize=8.0, color='red', fillstyle='full')
    )

    params = (
        ('period', 9),
        # ('func', func),
        # ('func', lambda d: fsum(abs(x) < abs(d[-1]) for x in d) / len(d)),
    )

    def next(self):
        dataHighArray = self.data.high.get(int((self.p.period - 1) / 2), self.p.period)
        dataLowArray = self.data.low.get(int((self.p.period - 1) / 2), self.p.period)
        if len(dataHighArray) < self.p.period:
            return
        else:
            self.l.Peaks[0] = findExtreme(dataHighArray, 'peak')
            self.l.Bottoms[0] = findExtreme(dataLowArray, 'bottom')