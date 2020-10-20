import easytrader
import easyquotation

user = easytrader.use('htzq_client')

user.prepare(user='2630104957', password='900303', comm_password='900303', exe_path=r'd:\海通证券委托\xiadan.exe')

# print(user.balance)
#
# print(user.position)

# user.buy('000651', price=0.55, amount=100)

quotation = easyquotation.use('tencent') # 新浪 ['sina'] 腾讯 ['tencent', 'qq']

# quotation.market_snapshot(prefix=True)

while(True):
    res = quotation.real('000002')
    # print(res)
    print("current price : %d, current time :%s",res['000002']['now'], res['000002']['datetime'])

    # if res['000002']['now'] <= 27.70:
    #     print("sell wanke")
    #     user.sell('000002',price=27.70,amount=100)