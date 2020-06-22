import pandas as pd

df = pd.DataFrame({'b':[1,2,3,2],'a':[4,3,2,1],'c':[1,3,8,2]},index=[2,0,1,3])

df = df.sort_values(by='b',ascending=False) #等同于df.sort_values(by='b',axis=0)

print(df)