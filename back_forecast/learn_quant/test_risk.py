from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA

portfolio="x565"
account_info=QA.QA_fetch_account({'account_cookie':'xxx4','portfolio_cookie':'x565'})
# risk_info=QA.QA_fetch_risk({'account_cookie':'xxx1'})
print(type(account_info))
print(type(account_info[0]))
for i in account_info[0].keys():
    print('key is : %s , value is : %s' % (i,account_info[0][i]))

for index in account_info[0]['history']:
    print(index)
# print(account_info)
# print(type(risk_info))
# print(risk_info)


# stock_list = QA.QA_fetch_stock_day_adv('000651', '2009-5-01', '2019-09-01')
#
# print(stock_list.to_qfq().data)