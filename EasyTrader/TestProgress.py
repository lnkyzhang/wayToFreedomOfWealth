from multiprocessing import Pool
import tushare as ts

class Foo():
    def work(self, i):
        print("this is work~~")
    def run(self):
        p = Pool()
        for i in range(4):
            p.apply_async(self.work, args=(i,))
        p.close()
        p.join()

if __name__ == '__main__':
    ts.set_token("d79c15feb3718d16953d1524f8076a076a33f55efb9eafa0d5484310")
    pro = ts.pro_api()
    df = pro.index_weight(index_code='399300.SZ', start_date='20210201', end_date='20210201')
    hs300List = df.con_code.apply(lambda x:x[0:6]).to_list()
    for i in range(len(hs300List)):
        print(hs300List[i] + ',',end='')