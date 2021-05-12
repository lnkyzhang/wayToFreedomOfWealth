import argparse
import datetime

import backtrader as bt

from BackTraderTest.BackTraderFunc.Indicator.StateInd import StateInd
from BackTraderTest.BackTraderFunc.MacdDivergence import macd_extend_data
from BackTraderTest.BackTraderFunc.Strategy.LeiGongSt import LeiGoneSt
from BackTraderTest.BackTraderFunc.Strategy.MacdDivergenceSt import MacdDivergenceSt
from BackTraderTest.BackTraderFunc.Strategy.lnkyzhangSt import lnkyzhangSt
from BackTraderTest.BackTraderFunc.TestBoll import pandas_divergence
from BackTraderTest.BackTraderFunc.makeData import QAStock2btData, QAStock2btDataOnline
from BackTraderTest.BackTraderFunc.DataReadFromCsv import read_dataframe, readFromDb


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro(cheat_on_open=True)
    cerebro.broker.setcommission(commission=0.0012, stocklike=True)
    # cerebro.broker.set_coo(True)

    # Data feed kwargs
    # '15min', '30min', '60min',
    # dataframe = read_dataframe(args.data, args.years, ['15min', '60min', 'd'])
    # dataframe = readFromDb(args.data, args.fq, args.years, ["5min", '15min', '60min', 'd'])
    # dataframe = readFromDb(args.data, args.fq, args.years, ['d'])
    # for i in range(len(dataframe)):
    #     cerebro.adddata(bt.feeds.PandasData(dataname=dataframe[i]))


    # for i in range(len(dataframe)):
    #     temp_df = macd_extend_data(dataframe[i])
    #     cerebro.adddata(pandas_divergence(dataname=temp_df,
    #                                       divergence_top=temp_df.columns.to_list().index('divergence_top'),
    #                                       divergence_bottom=temp_df.columns.to_list().index('divergence_bottom')))

    # dataframe = QAIndex2btData("159934", '2014-01-01', '2020-10-13')
    dataframe = QAStock2btData("000002", '2008-01-01', '2021-04-30')
    # dataframe = read_dataframe('000651.csv', '2014-2020', ['d'])[0]
    cerebro.adddata(bt.feeds.PandasData(dataname=dataframe))

    cerebro.addstrategy(lnkyzhangSt)
    # cerebro.addstrategy(MacdDivergenceSt)
    # cerebro.addstrategy(LeiGoneSt)

    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')

    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    strat = cerebro.run(stdstats=True, runonce=False)

    drawDown = strat[0].analyzers.DrawDown.get_analysis()
    print("max drawdown: %f", drawDown.max.drawdown)
    annualReturn = strat[0].analyzers.AnnualReturn.get_analysis()
    print("annualReturn: %s", annualReturn)

    pyfoliozer = strat[0].analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

    transactions.to_csv("transtion.csv")
    if args.plot:
        # cerebro.plot(style='line')
        cerebro.plot(style='candle',iplot=False)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,
                        default='000030.SZ',
                        help='Data to be read in')

    parser.add_argument('--fq', required=False,
                        default='hfq',
                        help='fq')

    parser.add_argument('--years', default='2010-2021',
                        help='Formats: YYYY-ZZZZ / YYYY / YYYY- / -ZZZZ')

    parser.add_argument('--multi', required=False, action='store_true',
                        help='Couple all lines of the indicator')

    parser.add_argument('--plot', required=False, action='store_true',
                        default=True,
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
