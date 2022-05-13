# -*- coding: UTF-8 -*-
import baostock as bs
import numpy as np
import pandas as pd
import datetime as dt
import requests
import os

SCKEY=os.environ.get('SCKEY')

def send_server(title, text):
    print(title)
    print()
    print(text)

    if SCKEY == '' or SCKEY is None:
        print("\nWarning: 微信消息无法发送，请设置sendkey!")
        return

    api = "https://sctapi.ftqq.com/{}.send".format(SCKEY)
    content = text.replace('\n','\n\n')
    data = {
            'text':title, #标题
            'desp':content} #内容
    res = requests.post(api, data = data)
    return(res)

def get_stock_code_name(stock_code):
    # 获取证券基本资料
    rs = bs.query_stock_basic(code=stock_code)
    # rs = bs.query_stock_basic(code_name="浦发银行")  # 支持模糊查询

    # 打印结果集
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    return result.loc[0,'code_name']

def calc_MA2500(stock_code):
    t = dt.datetime.utcnow()
    t = t + dt.timedelta(hours=8)               # 当前的北京时间
    t11 = t + dt.timedelta(days=-365*11-3)      # 得到11年前的时间，减去3个闰年
    d = t.strftime('%Y-%m-%d')
    d11 = t11.strftime('%Y-%m-%d')
    #TIME
    result = pd.DataFrame()

    stock_name = get_stock_code_name(stock_code)
    # 得到三栏的表格: date日期, code证卷代码, close收盘的点数。
    k = bs.query_history_k_data_plus(stock_code,"date,code,close",start_date=d11, end_date=d,frequency="d", adjustflag="3")
    # 得到k线数据
    result = pd.concat([result,k.get_data()],axis=0,ignore_index=True)
    result.date = pd.to_datetime(result.date)
    result = result.sort_values(by='date',ascending=False)        # 按日期排序，今天日期放在最上面
    result = result.reset_index(drop=True)

    today = pd.DataFrame()
    # 得到最近2500天的收盘点数列表
    today['close'] = result.nlargest(2500,'date').close
    # 计算MA2500均值
    MA2500 = today.close.astype(float).mean()
    # 计算MA2500的上下约20%的浮动区间, 并且只取两位小数
    MAdiv = int(MA2500/1.2*100)/100
    MAmul = int((MA2500*1.2)*100)/100
    MA2500 = int(MA2500*100)/100
    # 今天的收盘
    close_today = int(float(result.loc[0,'close'])*100)/100
    date_today = result.loc[0,'date']
    date_today_str = str(date_today.date()) + ": "

    '''
    # for debug purpose
    print()
    print("{}{}收盘点数: {}".format(date_today_str, stock_name, close_today))
    print("MA2500÷1.2点数: {}".format(MAdiv))
    print("MA2500    点数: {}".format(MA2500))
    print("MA2500x1.2点数: {}".format(MAmul))
    print()
    '''

    # recommend:
    #     低于÷1.2线:   ✔
    #     高于÷1.2线:   ✓
    #     高于MA2500线: =
    #     高于x1.2线:   ✗
    #
    if (close_today <= MAdiv):
        recommend = "✔"
        title = date_today_str + stock_name + "低于÷1.2线" + ": " + recommend
    else:
        if (close_today <= MA2500):
            judge = "÷1.2"
            recommend = "✓"
        elif (close_today <= MAmul):
            judge = "MA2500"
            recommend = "="
        else:
            judge = "*1.2"
            recommend = "✗"
        title = date_today_str + stock_name + "高于"+judge+"线" + ": " + recommend

    #GENERATE TITLE
    # 斜杠用来代码换行
    text = date_today_str + stock_name + "收盘: " + str(close_today) + \
           "\n" + date_today_str + "MA2500数据" +                 \
           "\n\t *1.2点数: " + str(MAmul) +    \
           "\n\t 均值点数 "   + str(MA2500) +   \
           "\n\t /1.2点数: " + str(MAdiv)

    return title, text

def main():
    title = "每周MA2500计算服务异常"
    text = "登录获取股市数据失败"

    try:
        # login boastock server first
        lg = bs.login()
        if (lg.error_code == '0'):
            title = ''
            text = ''

            STOCK_CODES = os.environ.get('STOCK_CODES')
            if STOCK_CODES == '' or STOCK_CODES is None:
                STOCK_CODES = 'sh.000001'

            for code in STOCK_CODES.split():
                brief, content = calc_MA2500(code)
                if title == "":
                    title = brief

                text += brief + "\n"
                text += content  + "\n"

            send_server(title, text)

            # logout at last
            bs.logout
    except Exception:
        print(Exception)
        send_server(title, text)

if __name__ == '__main__':
    main()
