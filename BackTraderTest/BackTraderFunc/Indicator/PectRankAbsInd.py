from backtrader.indicators import BaseApplyN
from mpmath import fsum


class PercentRankAbs(BaseApplyN):

    alias = ('PctRankAbs',)
    lines = ('pctrank',)
    params = (
        ('period', 50),
        ('func', lambda d: fsum(abs(x) < abs(d[-1]) for x in d) / len(d)),
    )