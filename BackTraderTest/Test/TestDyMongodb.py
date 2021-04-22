import asyncio

from BackTraderTest.Test.DyStockMongoDbEngine import DyStockMongoDbEngine
import datetime

if __name__ == "__main__":
    _mongoDbEngine = DyStockMongoDbEngine(None, False)
    a = _mongoDbEngine.isTicksExisting("000001.SZ","2015-04-08")
    print(a)

    startDate = datetime.datetime.now()
    loop = asyncio.get_event_loop()

    for i in range(9000000):
        # print(i/9000000)
        loop.run_until_complete(_mongoDbEngine.isTicksExisting("000001.SZ" , "2015-04-08"))
        # _mongoDbEngine.isTicksExisting("000001.SZ" , "2015-04-08")
        if i == 10000:
            print((datetime.datetime.now() - startDate).seconds)

    # _mongoDbEngine.isTicksExisting(["000001.SZ"] * 10000, ["2015-04-08"] * 10000)
    # print((datetime.datetime.now() - startDate).seconds)