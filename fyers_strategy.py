#!/usr/bin/env python
# coding: utf-8


import fyers_api
from fyers_api import accessToken
from fyers_api import fyersModel 
import pandas as pd
import yfinance as yf
import datetime
import time
import pytz

IST = pytz.timezone('Asia/Kolkata')

token = ""    #Enter the token you receive after authorization

is_async = False #(By default False, Change to True for asnyc API calls.)

fyers = fyersModel.FyersModel(is_async)



fyers_df = pd.read_csv("fyers.csv",index_col=0)
fyers_symbol = list(fyers_df['Symbol'])
nse_mas = pd.read_csv("nse.csv")
nse_mas['LTP'] = nse_mas['LTP'].str.replace(',','')
nse_mas['LTP'] = nse_mas['LTP'].astype('float') 
nse_mas = nse_mas[nse_mas['LTP']>=50].reset_index(drop=True)
scrips = list("NSE:" + nse_mas[nse_mas['Symbol'].isin(fyers_symbol)]['Symbol'] + "-EQ")
yf_scrips = list(nse_mas[nse_mas['Symbol'].isin(fyers_symbol)]['Symbol'] + ".NS")



def place_order(token,symb, qnty, order_side, lmt, stop_price, stop_loss, take_profit):
    fyers.place_orders(token = token,data = {"symbol" : symb,"qty" : qnty,"type" : 4,"side" : order_side,"productType" : "INTRADAY","limitPrice" : lmt,"stopPrice" : stop_price,"disclosedQty" : 0,"validity" : "DAY","offlineOrder" : "False","stopLoss" : stop_loss,"takeProfit" : take_profit})

def inside_bar(margin,token,symb,hi,lo,cl,op):
    len_ic = hi[-2] - lo[-2]
    body_ic = cl[-2] - op[-2]
    body_length = cl[-3] - op[-3]
    candle_length = hi[-3] - lo[-3]
    print("I am working!")
    if body_ic*body_length >= 0:
        return 0
    
    elif (abs(body_length) >= 0.6*candle_length and len_ic>0.2):
        if (lo[-2] > lo[-3]) and (hi[-2] <= hi[-3]):
            if body_length > 0:
                print("Going long for %s"%symb)
                qnty = margin//hi[-2]
                lt = 0.05 + hi[-2]
                order_data = place_order(token,symb,qnty,1,lt,hi[-2],len_ic,2*len_ic)
                order_ids.append(order_data['data']['id'])        #ToCheckAndVarify
                return 1
            else:
                print("Going short for %s"%symb)
                qnty = margin//lo[-2]
                lt = lo[-2] - 0.05
                order_data = place_order(token,symb,qnty,-1,lt,lo[-2],len_ic,2*len_ic)
                order_ids.append(order_data['data']['id'])      #ToCheckAndVerify             
                return -1
    else:
        return 0
                            
def to_tick(a, min_tick, decimal_place):
    return round(a+ min_tick - a%min_tick ,decimal_place) 





total_margin = pow(10,6)           #Total Capital for trading in INR
margin = total_margin/len(scrips)
interval = 5                      #Candle Interval (5,15,30,60)




while(1):
    a = list(map(int, datetime.datetime.now(IST).strftime("%H %M %S").split()))
    if a[1]%interval == 0:
        time_check = yf.Ticker(yf_scrips[0])
        chd = time_check.history(period='1d', interval = '5m')
        bar_time = list(map(int,chd[-1:].index.strftime("%H %M %S")[0].split()))
        if a[1] == bar_time[1]:
            print("Time Matched!")
            order_ids = []
            pos = fyers.positions(token = token)
            pos_list = []
            try:
                pos_list = list(pd.DataFrame(pos["data"]["netPositions"])['symbol'])
            except:
                pass
            for i in range(len(yf_scrips)):
                if scrips[i] in pos_list:
                    continue
                try :
                    tk = yf.Ticker(yf_scrips[i])
                    data = to_tick(tk.history(period='1d', interval ='5m'),0.05,2)
                except:
                    continue

                hi = list(data['High'])
                lo = list(data['Low'])
                op = list(data['Open'])
                cl = list(data['Close'])

                result = inside_bar(margin, token, scrips[i], hi, lo, cl, op)

            ct = list(map(int, datetime.datetime.now(IST).strftime("%H %M %S").split()))
            rem_time = (interval - ct[1]%interval-1)*60 + (60-ct[2])
            time.sleep(rem_time-5)
            for oid in order_ids:
                status =  fyers.order_status(token = token,data = {"id" : oid})
                if not status['data']['orderDetails']['status'] in [1,2,5]:
                    cancel_order = fyers.delete_orders(token = token,data = {"id" : oid})
    time.sleep(1)        
