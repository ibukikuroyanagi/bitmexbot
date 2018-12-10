import sys,os
import datetime,time
import ccxt,calendar, requests
import pandas as pd
import numpy as np
from time import sleep
import matplotlib.pyplot as plt

def str_to_unixtime(time_str):
    time_datetime = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    time_datetime=datetime.datetime(year=time_datetime.year, month=time_datetime.month, day=time_datetime.day, hour=time_datetime.hour, minute=time_datetime.minute, second=0, microsecond=0, tzinfo=None)
    time_sec = time_datetime.timestamp()
    return int(time_sec)

def get_data(symbol,period,start_time,last_time):
    # APIリクエスト(1時間前から現在までの5m足OHLCVデータを取得)
    try:
        param = {"symbol": symbol,"period": period, "from": start_time, "to":last_time }
        url = "https://www.bitmex.com/api/udf/history?symbol={symbol}&resolution={period}&from={from}&to={to}".format(**param)
        res = requests.get(url)
        data = res.json()
    except WantReadError:
        print('sleep 30 sec')
        sleep(30)

    #レスポンスのjsonデータからOHLCVのDataFrameを作成
    df = pd.DataFrame({
                "timestamp": data["t"],
                "open":      data["o"],
                "high":      data["h"],
                "low":       data["l"],
                "close":     data["c"],
                "volume":    data["v"],
            }, columns = ["timestamp","open","high","low","close","volume"])
    return df
#選択した配列のみを取得
def make_select_array(order_list,symbol,side):
    select_array = []
    for line in order_list:
        if line[3] == symbol and line[4] == side:
            select_array.append(line)
    return select_array

#選択した配列から必要な列を抜き出す
def separete_array(select_array):
    x = np.array([str_to_unixtime(row[1]) for row in select_array])
    y = np.array([float(row[8]) for row in select_array])
    return x,y


"""メイン関数"""
try:
    fname = sys.argv[1]
except IndexError:
    print('このファイルはbitmexのbotが実際に取引した価格を表示させるものです。\n第一引数に解析したいtxtファイルを記入して下さい。')
    sys.exit()

#ファイル読み込み
with open(fname,'r',encoding = 'utf_8') as r:
    text = r.read()
print('ファイル読み込み完了')
#読み込んだデータを一行ごとにリストにして、その要素を","で分割
all_list = text.split('\n')
data = []
for line in all_list:
    element = line.split(',')
    data.append(element)

#売買取引したデータのみを取得
order_list = []
for line in data:
    if line[0] == 'MSG-O':
        order_list.append(line)

symbol1=order_list[0][3]
symbol2=order_list[1][3]

#開始時刻のデータ取得時刻
start_time = float(all_list[1])
start_time = int(start_time) #- 60*60*9
#最終時刻のデータ取得時刻
last_time_str = data[len(data)-2][1]
last_time = str_to_unixtime(last_time_str) + 60*5 #- 60*60*9
print(start_time,type(start_time))
print(last_time,type(last_time))

symbol1_buy  = make_select_array(order_list,symbol1,'Buy')
symbol1_sell = make_select_array(order_list,symbol1,'Sell')
symbol2_buy  = make_select_array(order_list,symbol2,'Buy')
symbol2_sell = make_select_array(order_list,symbol2,'Sell')

buy_x1,buy_y1   = separete_array(symbol1_buy)
sell_x1,sell_y1 = separete_array(symbol1_sell)
buy_x2,buy_y2   = separete_array(symbol2_buy)
sell_x2,sell_y2 = separete_array(symbol2_sell)

# print(symbol1_buy,buy_x1,buy_y1)
# print(symbol2_buy,buy_x2,buy_y2)
# print(type(symbol1_buy),type(buy_x1[0]),type(buy_y1[0]))

# bitMEX使用宣言
bitmex = ccxt.bitmex()
# テストネット使用宣言（本番時はコメントアウトする）
bitmex.urls["api"] = bitmex.urls["test"]

print('apiからデータ取得開始')
df1 = get_data(symbol=symbol1,period=1,start_time=start_time,last_time=last_time)
df2 = get_data(symbol=symbol2,period=1,start_time=start_time,last_time=last_time)
print('apiからデータ取得完了')
df3 = df1 - df2

data_x1 = np.array(df1['timestamp'])
data_y1 = np.array(df1['close'])
data_x2 = np.array(df2['timestamp'])
data_y2 = np.array(df2['close'])

print(data_x1,data_y1)

"""グラフの表示"""
print('青がbuy,赤がsell')
fig = plt.figure()
ax1 = fig.add_subplot(1,2,1)
ax2 = fig.add_subplot(1,2,2,sharey=ax1)

ax1.set_title(symbol1+' blue is buy, red is sell')
ax1.plot(data_x1,data_y1,c='g',label=symbol1)
ax1.scatter(buy_x1,buy_y1,s=150,c='b')
ax1.scatter(sell_x1,sell_y1,s=150,c='r')
plt.xlabel("timestamp [sec]")
plt.ylabel("price [{0}]".format(symbol1))

ax2.set_title(symbol2+' blue is buy, red is sell')
ax2.plot(data_x2,data_y2,c='c',label=symbol2)
ax2.scatter(buy_x2,buy_y2,s=150,c='b')
ax2.scatter(sell_x2,sell_y2,s=150,c='r')
plt.tight_layout()
plt.savefig('share_y.png')
plt.show()

fig = plt.figure()
ax1 = fig.add_subplot(3,1,1)
ax2 = fig.add_subplot(3,1,2,sharex=ax1)
ax3 = fig.add_subplot(3,1,3,sharex=ax1)

ax1.set_title(symbol1+' blue is buy, red is sell')
ax1.plot(data_x1,data_y1,c='g',label=symbol1)
ax1.scatter(buy_x1,buy_y1,s=150,c='b')
ax1.scatter(sell_x1,sell_y1,s=150,c='r')
plt.xlabel("timestamp [sec]")
plt.ylabel("price [{0}]".format(symbol1))

ax2.set_title(symbol2+' blue is buy, red is sell')
ax2.plot(data_x2,data_y2,c='c',label=symbol2)
ax2.scatter(buy_x2,buy_y2,s=150,c='b')
ax2.scatter(sell_x2,sell_y2,s=150,c='r')

ax3.set_title(symbol1 + ' - ' + symbol2)
ax3.plot(data_x1,df3['close'],label=symbol1 + ' - ' + symbol2)
plt.tight_layout()
plt.savefig('share_x.png')
plt.show()

print(df3)
print(order_list)
