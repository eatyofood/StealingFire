import re
import pandas as pd
import pretty_errors
import shutil 
from tqdm import trange
import time
import os
from datetime import datetime
import sqlalchemy as sql
import cufflinks as cf
import numpy as np
cf.go_offline(connected=False)
import pandas as pd
import numpy as np
import os
from tqdm import trange
import seaborn as sns
import pandas_ta as pta
import pandas_datareader as pdr
import time
from fastquant import backtest
import stealing.config as config
##from finding_fire import jenay, weekly_pull,weekly_push, monthly_pull,monthly_push,one_stop,vally_stop,bipolar,pct_targets,sobar,hl,sola,short_frame,the_twelve

# XXX XXX XXX XXX XXX XXX XXX XXX FINDING FIRE XXX XXX XXX XXX XXX XXX XXX XXX XXXXXXXXXXXXX


import pandas as pd
from tqdm import trange
import talib
import pandas_ta as pta
import os 

def drop_scales(df):
    '''
    dropz all the plot stuff from jenay
    
    '''
    
    drop_list = ['ma_10','ma_20','fast_above','200Day_MA','50Day_MA'] 
    [drop_list.append(col) for col in df.columns if 'scale' in col]
    for thing in drop_list:
        if thing in df.columns:
            try:
                df = df.drop(thing,axis=1)
            except Exception as e:
                print(e)
                print('nothing to drop')
            return df

def scale_to_close(df,col):
    new_col = col + '_scaled'
    df[new_col] = 0
    for i in range(len(df)):
        if df[col][i] == True:
            df[new_col][i] = df['close'][i]
    return df

      
def hl(df):
    def highlight(boo):
        criteria = boo ==True
        return['background-color: green'if i else '' for i in criteria]
    df = df.style.apply(highlight)
    return df


def one_stop(df,UP_TARG='up_targ',DN_TARG='dn_targ',BUY='buy',plot=False,plot_capital=False,strat_name='strat_name_here',limit='',fast_quant=True):
    '''
    one stop backtest shop... creates targets compiles the strat, plots the action and TODO: 1.return backtest results 2.name_strat
    TAKES:
        1.dataframe
        2.UP_TARG - where to set target when buy_trigger is hit, for profit EXAMPLE: pct , atr, bollinger_bands,
        3.DN_TARG - where to set stop when buy_trigger is hit, for loss
        4.plot    - plots the trades
        5.plot_cap- plots the scaled acnt
        6.limit   - this is where the entry level will be taken from 
            HOWEVER:
                YOU MUST build ARENESS that price went below your limit
                PRICE INTO THE BUY SIGNAL!
    RETURNS:
         results dataframe
        and plots
    LIMIT

    '''

    #FUNCTION
    df['buyy'] = df[BUY]
    df['trac'] = False
    df['STOP'] = 0.0
    df['TARG'] = 0.0
    df['OUT']  = False
    df['ENTRY']= 0.00
    df['EXIT'] = 0.00
    trac = df['trac']
    up   = df['TARG']
    dn   = df['STOP']
    out  = df['OUT']
    ent  = df['ENTRY']
    exit = df['EXIT']

    #the only difference with validation entry is this first row 
    #will have an eextra layer for waiting...

    ## then adding tranches will just go under each up and dn... 
    ## they will be independant acnts operating in the same frame work...
    # then get add together later with a weight values...


    ''' IF YOU GET TIERD:
        of this function erroring out just put this into the whole thing, however i would prefer
        for the backtest to stop before this stage if there are no buy signals'''
    #if len(df[df['buy']==True]) > 0

    

    ENTRY_PNT = 'close'
    if len(limit) > 0:
        ENTRY_PNT = limit


    for i in range(1,len(df)):
        if (trac[i-1]==False) & (df[BUY][i]==True):
            trac[i] = True
            up[i] = df[UP_TARG][i]
            dn[i] = df[DN_TARG][i]
            ent[i]= df[ENTRY_PNT][i]
        if (trac[i-1] == True)  & (df['low'][i]<dn[i-1]):
            out[i] = True
            trac[i] = False
            if (df['open'][i]<dn[i-1]):
                exit[i] = df['open'][i]
            else:
                exit[i] = dn[i-1]
        if (trac[i-1] == True) & (df['high'][i]> up[i-1]):
            out[i] = True
            trac[i] = False
            if (df['open'][i]> up[i-1]):
                exit[i] = df['open'][i]
            else:
                exit[i] = up[i-1]
        if (out[i-1] == False) & (trac[i-1]==True):
            up[i] = up[i-1]
            dn[i] = dn[i-1]
            trac[i] = trac[i-1]
            ent[i]  = ent[i-1]
    #df['ENTRY_scale']= df['ENTRY'].replace(True,1).replace(1,df.close)
    df = scale_to_close(df,'ENTRY')
    #need a candelstick PLT SUCKA!!!
    if plot == True:
        df = scale_to_close(df,'trac')
        df = scale_to_close(df,'TARG')
        df = scale_to_close(df,'STOP')
        df = scale_to_close(df,'OUT')

        #df['EXIT_scale'] = df['EXIT'].replace(True,1).replace(1,df.close)
        df = scale_to_close(df,'EXIT')

        df[['trac_scaled','close','TARG_scaled','STOP_scaled','ENTRY_scaled','OUT_scaled','EXIT_scaled']].iplot(theme='solar',fill=True,title=(strat_name+' Target - plot'))

    #grab the first buy to scale price
    first_buy = df[df[BUY]==True].close.iloc[0]
    df['SCALE_ACNT'] = first_buy

    #placeholders
    scale = df['SCALE_ACNT']
    df['TRAC'] = df['trac']
    df['PNL']  = 0.00
    df["PNL_PCT"] = 0.00

    hl(df)
    #thi should have been built into atr_targs
    #IM GOING TO ADD NON PYRIMIDING ACNT VALUE TO THIS AS WELL!!!
    
    # afirm that the last col is flat positions
    df['TRAC'][-1] = False
    exit[-2] = df.close[-2]
    #simulation results
    for i in trange(1,len(df)):
        if (df['TRAC'][i] == False) & (df['TRAC'][i-1]==True):
            df['PNL'][i] = exit[i-1] - df['ENTRY'][i-1]
            df['PNL_PCT'][i] = df['PNL'][i]/df['ENTRY'][i-1]
            scale[i] = (scale[i-1]*df['PNL_PCT'][i])+scale[i-1]
        else:
            scale[i] = scale[i-1]
    #plot_capital = True
    #if plot_capital == True:
    if plot == True:
        #jenay(df,line_one='ENTRY_scaled',line_two='SCALE')
        df[['ENTRY_scaled','close','SCALE_ACNT']].iplot(theme='solar',fill=True,title=(strat_name+' Capital Scaled'))
        #df = scale_to_close(df,'trac')
        #df = scale_to_close(df,'TARG')
        #df = scale_to_close(df,'STOP')
        #df = scale_to_close(df,'OUT')
#
        ##df['EXIT_scale'] = df['EXIT'].replace(True,1).replace(1,df.close)
        #df = scale_to_close(df,'EXIT')
        #
        #
        #line_one='TARG_scale'
        #line_two='STOP_scale'
        #scale_one='SCALE_ACNT'
        #jenay(df,line_one=line_one,line_two=line_two,scale_one=scale_one,title=strat_name)



    ### RESULTS MODS = [
    df['acnt'] = 1000
    for i in trange(1,len(df)):
        if df['PNL_PCT'][i] != 0:
            # adjust acnt value based on pct changes
            df['acnt'][i] = df['acnt'][i-1]+(df['PNL_PCT'][i]*df['acnt'][i-1])
        else:
            df['acnt'][i] = df['acnt'][i-1]
            
        
        
    
    
    
    df['win_cnt'] = df['PNL_PCT']>0
    df['los_cnt'] = df['PNL_PCT']<0
    
        
    win_cnt = df['win_cnt'].sum()
    los_cnt = df['los_cnt'].sum()
    total   = win_cnt+los_cnt
    win_pct = (win_cnt/total)
  
    ### RESULTS MODS     
    win_cnt = df['win_cnt'].sum()
    los_cnt = df['los_cnt'].sum()
    total   = win_cnt+los_cnt
    win_pct = (win_cnt/total)
    final_pnl= (df['acnt'][-1]-1000)/1000*100

    print('strat_name      :',strat_name)
    print('final_acnt value:',df['acnt'][-1])
    print('total_+trades   :',total)
    print('wins            :',win_cnt)
    print('loss            :',los_cnt)
    print('win_percent     :',(win_pct*100),'%')
    print('final_pnl       :',final_pnl,'%')

    d = {}
    li =[]
    
    d['strat_name']        = strat_name
    d['final_acnt_value']  = df['acnt'][-1]
    d['total_trades']      = total
    d['wins']              = win_cnt
    d['loss']              = los_cnt
    d['win_pct']           = win_pct*100
    d['final_pnl']         = final_pnl

    li.append(d)

    result = pd.DataFrame(li)

    ### RESULTS MODS END
    if plot_capital == True:
        result[['wins','loss']].sum().plot(kind='pie')


    if fast_quant == True:
        #PLACE NEW EASYBAKE QUANT HERE:
        print('INITIATING FAST QUANT')
        result = easybake_fastquant(df,result)
    return result


def pct_targets(df,up_pct=10,dn_pct=5,plot=False):
    '''
    TAKES:
        1.df
        2.up_pct - int < 100
        3.dn_pct - int < 100
    adds 
        up_pct band
        dn_pct band
            - to dataframe to be used as targets on a trigger
    '''
    up_pct = up_pct/100
    dn_pct = dn_pct/100

    df['up_targ'] = (df['close']*up_pct)+df['close']
    df['dn_targ'] = df['close'] - (df['close']*dn_pct)
    if plot == True:
        df[['dn_targ','close','up_targ']].iplot(theme='solar',fill=True)
    

import talib
def the_twelve(df,return_candlelist=False):
    '''
    adds candles to the data frame
    if return_candle_list is True:
        RETURNS:
            a list of the candels:
                [
                'DOJI',
                'EVENINGSTAR',
                'MORNINGSTAR',
                'SHOOTINGSTAR',
                'HAMMER',
                'INVERTEDHAMMER',
                'HARAMI',
                'ENGULFING',
                'HANGINGMAN',
                'PIERCING',
                'BELTHOLD',
                'KICKING',
                'DARKCLOUDCOVER'
    '''

    df['DOJI'] = talib.CDLDOJI(df.open,df.high,df.low,df.close)
    df['EVENINGSTAR'] = talib.CDLEVENINGSTAR(df.open,df.high,df.low,df.close)
    df['MORNINGSTAR'] = talib.CDLMORNINGSTAR(df.open,df.high,df.low,df.close)
    df['SHOOTINGSTAR'] = talib.CDLSHOOTINGSTAR(df.open,df.high,df.low,df.close)
    df['HAMMER'] = talib.CDLHAMMER(df.open,df.high,df.low,df.close)
    df['INVERTEDHAMMER'] = talib.CDLINVERTEDHAMMER(df.open,df.high,df.low,df.close)
    df['HARAMI'] = talib.CDLHARAMI(df.open,df.high,df.low,df.close)
    df['ENGULFING'] = talib.CDLENGULFING(df.open,df.high,df.low,df.close)
    df['HANGINGMAN'] = talib.CDLHANGINGMAN(df.open,df.high,df.low,df.close)
    df['PIERCING'] = talib.CDLPIERCING(df.open,df.high,df.low,df.close)
    df['BELTHOLD'] = talib.CDLBELTHOLD(df.open,df.high,df.low,df.close)
    df['KICKING'] = talib.CDLKICKING(df.open,df.high,df.low,df.close)
    df['DARKCLOUDCOVER'] = talib.CDLDARKCLOUDCOVER(df.open,df.high,df.low,df.close)
    if return_candlelist == True:
        candle_list = [
            'DOJI',
            'EVENINGSTAR',
            'MORNINGSTAR',
            'SHOOTINGSTAR',
            'HAMMER',
            'INVERTEDHAMMER',
            'HARAMI',
            'ENGULFING',
            'HANGINGMAN',
            'PIERCING',
            'BELTHOLD',
            'KICKING',
            'DARKCLOUDCOVER'
        ]
        return candle_list


def candle_buy(df,candle='',stoch=True,stoch_thresh=30,plot=True,return_list=False):
    '''
    adds buy candel of the 12 with the option of combining it with stochastic threshhold...
    TAKES:
        1.df
        2.stoch - bool True if you want to combine stoch condition
        3.stoch_thresh 
        4.plot - returns trigger plot
    returns:
        'buy' column for triggers and targets to be worked out
    '''
    the_twelve(df,return_list)
    #df['short_line'] = talib.CDLSHORTLINE(df.open,df.high,df.low,df.close)
    df['buy'] = df[candle].replace(100,True).replace(-100,False).replace(0,False)
    
    
    if stoch == True:
        df[['fast_sto','slow_sto']]  = pta.stoch(df.high,df.low,df.close)
        df['buy']                    = (df['buy']==True) & ( df['fast_sto']<stoch_thresh)
    if plot==True:
        df['buy_scale'] = df['buy'].replace(True,1).replace(1,df.close)
        df[['buy_scale','close']].iplot(theme='solar',fill=True)
        
        
        
def candle_pct(df,candle,up_pct=10,dn_pct=5,plot=False,stoch=False,stoch_thresh=30,return_list=False,condition=None):
    
    strat_name = candle + '_stoch:'+str(stoch_thresh)+'uppct:'+str(up_pct)+'dnpct'+str(dn_pct)
    print(strat_name)


    candle_buy(df,candle,stoch=stoch,stoch_thresh=stoch_thresh,plot=False,return_list=return_list)#,condition=condition)
    if condition != None:
        df['buy'] = (df['buy'] == True) & (df[condition].shift()==True)
    if len(df[df['buy']==True]) > 0:
        pct_targets(df,up_pct,dn_pct,plot)
        result =one_stop(df,strat_name=strat_name,plot=plot,plot_capital=plot)
        result['up_pct'] = up_pct
        result['dn_pct'] = dn_pct
        result['candle'] = candle
    else:
        result = None
    #og file
    
    return result


#candle_pct(df,'DOJI',15,5,plot=True,stoch=True,stoch_thresh=20,return_list=True)


def indicator_adder(df):
    '''
    this adds the most common indicators to a dataframe
    with lower case close open high low volume
    takes: dataframe
    returns : dataframe
    '''
    df['rsi'] = pta.rsi(df.close)
    df['riz'] = pta.rsi(df.close,length=2)
    df['vwap'] = pta.vwap(df.high,df.low,df.close,df.volume)
    df[['stoch_k','stoch_d']] = pta.stoch(df.high,df.low,df.close)
    if len(df)>20:
        df['ema'] = pta.ema(df.close,length=20)
    
    #if len(df)>6:
        #df        = super_trend(df)
    return df



def add_weekly(df,add_indicators=False,plot=True,other_indicator_function=None):
    '''
    -mixes weekly data with a smaller time frame dataframe

    Takes:
        1.df -  a daily or intra day datafame,
        2. add_indicators : bool adds [rsi , vwap, stochastic and ema ] to weekly dataframe
        3. plot? - bool
        4. other_indicator_function - function 
            ADD: a indicator function of your choosing!@@@@@@!! yeet yeet skeet skeet. wooh!
    RETURNS:
        df, - new and improved with weekly stuff

    '''
    df['week'] = df.index.week
    df['date'] = df.index.date
    df
    df['year'] = df.index.year
    df.head()

    df['week_year'] = df['year'].astype(str)+ '-'+ df['week'].astype(str)
    df

    df.groupby('week_year').agg('last')#.sort_values('date')

    week_high= df.groupby('week_year').agg('max')['high']
    week_low = df.groupby('week_year').agg('min')['low']
    week_close=df.groupby('week_year').agg('last').sort_values('date')['close']
    week_open =df.groupby('week_year').agg('first').sort_values('date')['open']
    week_date =df.groupby('week_year').agg('last').sort_values('date')['date']
    week_volume=df.groupby('week_year').agg('sum')['volume']

    week_columns= [week_high,week_low,week_close,week_open,week_volume,week_date]
    week_df = pd.DataFrame(week_columns).T
    week_df = week_df.sort_values('date')
    if add_indicators == True:
        week_df  = indicator_adder(week_df)
    week_df

    if other_indicator_function != None:
        other_indicator_function(week_df)

    from tqdm import trange



    for col in week_df.drop('date',axis=1).columns:
        week_df[col] = week_df[col].shift()
        new_col = 'week_'+col
        print(new_col)
        df[new_col] = 0.0
        for i in range(1,len(df)):
            week_year = df['week_year'][i]
            df[new_col][i] = week_df[col][week_year]

    if plot == True:
        #sola(df[['low','high','week_low','week_high']])
        #sola(df[['week_open','week_close','open','close']])
        jenay(df,line_one='week_open',line_two='week_close',title='Weekly Lines')


        


import pandas_ta as pta
def sola(df,title=None):
    return df.iplot(theme='solar',fill=True,title=title)


THIS_NEEDS_TO_BE_RENAMMED =''


def higher_highs_trendmap(df,plot=True,only_return_trend=False):#,return_frame=False):
    '''
    NEEDS TO BE TESTED!!! 
    TODO:
        1. VERIFY WITH tradingview
        2. a bunch of these loops if not all can go inside each other...
        
    tracks higher highs and higher lows, when you have one after the other 
       the column:
           trend_change_up == True

    RETURNS COLUMNS:
        'last_hl_uptrend' - when last high and last low were both higher
    '''
    
    df['riz'] = pta.rsi(df.close,legnth=2)

    df['up_corn'] = (df['riz']>df['riz'].shift()) & ( df['riz'].shift()<df['riz'].shift(2))
    df['dn_corn'] = (df['riz']<df['riz'].shift()) & ( df['riz'].shift()>df['riz'].shift(2))
    df['last_up_corn'] = 0.0
    df['last_dn_corn'] = 0.0
    df['higher_low']   = False
    df['higher_high']  = False
    df['lower_high']   = False
    df['lower_low']    = False

    for i in trange(1,len(df)):
        if df['up_corn'][i] == True:
            df['last_up_corn'][i] = df['close'][i]
        else:
            df['last_up_corn'][i] = df['last_up_corn'][i-1]
        if df['dn_corn'][i] == True:
            df['last_dn_corn'][i] = df['close'][i]
        else:
            df['last_dn_corn'][i] = df['last_dn_corn'][i-1]

        if (df['up_corn'][i] == True) & (df['last_up_corn'][i] > df['last_up_corn'][i-1]):
            df['higher_low'][i] = True
        if (df['dn_corn'][i] == True) & (df['last_dn_corn'][i] > df['last_dn_corn'][i-1]):
            df['higher_high'][i] = True

        if (df['up_corn'][i]==True) & (df['higher_low'][i]==False):
            df['lower_low'][i] = True
        if (df['dn_corn'][i] == True) & (df['higher_high'][i] == False):
            df['lower_high'][i] = True

    df['last_high_was_higher'] = False
    for i in trange(len(df)):
        if df['higher_high'][i] == True:
            df['last_high_was_higher'][i] = True
        elif df['lower_high'][i] == True:
            df['last_high_was_higher'][i] = False
        else:
            df['last_high_was_higher'][i] = df['last_high_was_higher'][i-1]

    df['last_high_was_lower'] = ( df['last_high_was_higher'] == False)     

    

    df['last_low_was_higher'] = False
    for i in trange(len(df)):
        if df['higher_low'][i] == True:
            df['last_low_was_higher'][i] = True
        elif df['higher_low'][i] == True:
            df['last_low_was_higher'][i] = False
        else:
            df['last_low_was_higher'][i] = df['last_low_was_higher'][i-1]

    df['last_low_was_lower'] = False
    for i in trange(len(df)):
        if df['lower_low'][i] == True:
            df['last_low_was_lower'][i] = True
        elif df['higher_low'][i] == True:
            df['last_low_was_lower'][i] = False
        else:
            df['last_low_was_lower'][i] = df['last_low_was_lower'][i-1]#.......................................................

    df['closee'] = df['close']  
    df['last_hl_uptrend'] = (df['last_high_was_higher']==True) & (df['last_low_was_higher']==True)
    df['last_low_was_higher'] = df['last_low_was_lower'] == False        
    df['trend_change']   = df['last_hl_uptrend'] != df['last_hl_uptrend'].shift()#...........................
    df['trend_change_up'] = (df['trend_change']==True) & ( df['last_hl_uptrend']==True)
    #df['datee']           = df.index.date
    if plot == True:
        df['last_hl_uptrend_scale'] = df['last_hl_uptrend'].replace(True,1).replace(1,df.close)
        df[['close','last_hl_uptrend_scale']].iplot(theme='solar',fill=True)
        jenay(df,scale_one='last_hl_uptrend',line_one='last_up_corn')



    if only_return_trend == True:
        loosers = ['riz','up_corn','dn_corn','last_up_corn','last_dn_corn','higher_low','higher_high','lower_high','lower_low','closee','last_low_was_higher','datee']
        df = df.drop(loosers,axis=1)
    
    return df

        
def short_frame(df,plot=False):
    '''
    this function is supposed to create a perfectly inverted dataframe of a stock data dataframe .
    to simplify the development of short strategys and/or sell signals as well as high probability downtrends. 

    strategys with positive alpha work in both directions...
    

    TAKES:
        1. dataframe - and subtracts the whole thing by the highest number in the 'high' column.
                    then adds the lowest number from min to set it back to scale... 
    '''
    if plot == True:
        jenay(df)
        #sola(df[['low','high']])

    #INVERT DATA
    big_num = df['high'].max()
    print(big_num)

    small_num = df['low'].min()
    print(small_num)

    price_columns = ['open','low','high','close']
    for col in price_columns:
        df[col] = (big_num - df[col]) + small_num


    

    # swap high and low since we inverted
    df[['high','low']] = df[['low','high']]
    if plot == True:
        jenay(df)
        #sola(df[['low','high']])
    df
    return df
    


def numdex(df):
    '''
    turns your dataframe's datetime index into an ordered numeric index
    with labeled dates.
    
    TAKES:
        DataFrame: with datetime index
    OUTPUT:
        DataFrame: now with string index (in order) with datetime as labels.
        
    
    '''
    #number of digits
    max_digs = len(str(len(df)))
    #copy of dataframe to reset index
    dfc = df.copy().reset_index()


    print('max digits:',max_digs)

    # copy index
    dfc['index_copy'] = dfc.index
    dfc['time']       = df.index
    # lose noice
    dfc = dfc[['time','index_copy']]
    # String Index Copy
    dfc['string_index'] = dfc['index_copy'].astype(str)

    dfc['num_of_digs'] = True
    dfc['string_stack']= 0
    dfc['dig_diff']    = 0
    dfc['we_short']    = False
    num_li             = []
    dfc['new_index']   =  0
    for i in range(len(dfc)):
        # Length Of Digits
        dig_len = len(dfc['string_index'][i])
        # Current Index Number 
        cur_num = dfc['string_index'][i]
        # Digit Difference
        dig_diff= max_digs - dig_len
        ### TEMP
        dfc['dig_diff'][i] = dig_diff
        ###
        if dig_diff > 0:
            ### TEMP
            dfc['we_short'][i] = True
            ### 
            for i in range(dig_diff):
                cur_num = '0' + cur_num 

        num_li.append(cur_num)





    dfc['new_index'] = num_li 
    dfc['new_index'] = dfc['new_index'].astype(str) + '|||' + dfc['time'].astype(str)
    dfc
    df.index = dfc['new_index']
    return df
        
import plotly.graph_objs as go
import plotly.offline    as pyo

from plotly.subplots import make_subplots
def jenay(df,fast=10,slow=20,title=None,line_one='',line_two='',line_list=None,scale_one='',scale_two='',numidex=False,lose_scales=True):

    '''
    ploting and scaling all in one
    TAKES:
 def jenay       1. df
        2. fast and slow ma
        3. line_one and line_two : default= 50dayma 200day ma (THEY FILL THEIR GAP )
        4. line_list : plots a list of column names into line traces 
        5. scale_one - takes bool and make true close for visual guid on signals
        6. numindex : turns a time series index into a string index ( while staying in order
                        and displaying date) . this makes some time series plots easier to read, when 
                        there are gaps in intraday or weekend data



    scale_one and scale_two
    
    '''
    if numidex == True:
        df = numdex(df)
    
    
    # name the avgs
    fname = 'ma_'+str(fast)
    sname = 'ma_'+str(slow)

    #create avgs
    df[fname] = df['close'].rolling(fast).mean().shift()
    df[sname] = df['close'].rolling(slow).mean().shift()
    # True if fast is above
    df['fast_above'] = df[fname]>df[sname]


    if len(line_one) == 0:
        line_one = '50Day_MA'
        df[line_one] = df['close'].rolling(50).mean().shift()
    if len(line_two) == 0:
        line_two = '200Day_MA'
        df[line_two] = df['close'].rolling(200).mean().shift()

    #and finally plot the shindig
    fig = make_subplots(rows=2, cols=1,row_width=[0.5,1],shared_xaxes=True)
    fig.add_trace(go.Candlestick(x=df.index,#x=df['date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color= 'cyan',
                    decreasing_line_color= 'gray'   
                                        ),row=1,col=1)
                         
                         #go.Scatter(x=df.index, y=df[fname] ,  name=fname,  line=dict(color='purple', width=3)),
                         #go.Scatter(x=df.index, y=df[sname],   name=sname, line=dict(color='yellow', width=3))

    fig.add_trace(go.Scatter(x=df.index, y=df[line_one],name=line_one ,line=dict(color='lightgreen', width=3)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[line_two],name=line_two ,line=dict(color='red', width=3)),row=1,col=1)

    # ATTEMPT TO ADD RSI
    df['rsi'] = pta.rsi(df.close)
    df['oversold']   = 30
    df['overbaught'] = 70
    df['exoversold']   = 10
    df['exoverbaught'] = 90
    #RSI
    fig.add_trace(
        go.Scatter(x=df.index, y=df.rsi,name='RSI'),
        row=2, col=1
        )
    #oversold
    fig.add_trace(
        go.Scatter(x=df.index, y=df.oversold,name='OverSold',mode='lines'),
        row=2, col=1
        )
    fig.add_trace(
        go.Scatter(x=df.index, y=df.overbaught,name='OverBought',mode='lines'),
        row=2, col=1
        )
    #FILL TRACE

    fig.add_trace(go.Scatter(x=df.index, y=df[line_one],
        mode='lines',
        name=line_one,
        opacity=0.09,
        fill='tonexty',
        line=dict(color='lightgreen')))
    
    if len(scale_one) > 0: 
        
        ## this is the pandas update issue
        df = scale_to_close(df,scale_one)
        scale_name = scale_one + '_scaled'

        fig.add_trace(go.Scatter(x=df.index, y=df[scale_name],
            mode='lines',
            name=scale_one,
            opacity=0.02,
            fill='tozeroy',
            line=dict(color='green')))

    
    if len(scale_two) > 0: 
        df = scale_to_close(df,scale_two)
        scale_name_two = scale_two + '_scaled'
        
        fig.add_trace(go.Scatter(x=df.index, y=df[scale_name_two],
            mode='lines',
            name=scale_two,
            opacity=0.02,
            fill='tozeroy',
            line=dict(color='orange')))


    fig.add_trace(go.Scatter(x=df.index, y=df[fname],
                        mode='lines',
                        name=fname,
                            marker=dict(
                            color='orange',
                            size=9
                            )
                            ))



    layout = go.Layout(
        xaxis = dict(
            rangeslider = dict(
                visible = False
            )
        )
    )
    
    
    # Add Lines From A List
    if line_list != None:
        for line in line_list:
            
            fig.add_trace(go.Scatter(x=df.index, y=df[line],
                mode='lines',
                name=line,
                opacity=0.60
                                    ))
    
    fig.update_layout(layout,template='plotly_dark',title=title)#template="plotly_dark",title='Candle')
    fig.show(theme='solar',yaxis = dict(fixedrange = False))
    if lose_scales == True:
        df = drop_scales(df)
    



import numpy as np


def vally_stop(df,UP_TARG='up_targ',DN_TARG='dn_targ',BUY='buy',plot=False,plot_capital=False,strat_name='strat_name_here',limit=''):
    '''
    basically - a version of one_stop with a moving stop loss...
        TODO- 
            >confirm buy with close > con_line
            >eliminate 'dn' updating' every row iteration

            > INSERT CANDLE PLOT!!!
                - replace 0 with np.nan

            >built in trailing pct stop

    one stop backtest shop... creates targets compiles the strat, plots the action and TODO: 1.return backtest results 2.name_strat
    TAKES:
        1.dataframe
        2.UP_TARG - where to set target when buy_trigger is hit, for profit EXAMPLE: pct , atr, bollinger_bands,
        3.DN_TARG - where to set stop when buy_trigger is hit, for loss
        4.plot    - plots the trades
        5.plot_cap- plots the scaled acnt
        6.limit   - this is where the entry level will be taken from 
            HOWEVER:
                YOU MUST build ARENESS that price went below your limit
                PRICE INTO THE BUY SIGNAL!
    RETURNS:
         results dataframe
        and plots
    LIMIT

    '''
    # create default validation column if its not been created 
    if DN_TARG == '5_ma':
        df[DN_TARG] = df['close'].rolling(5).mean()

    #FUNCTION
    df['buyy'] = df[BUY]
    df['trac'] = False
    df['STOP'] = 0.0
    df['TARG'] = 0.0
    df['OUT']  = False
    df['ENTRY']= 0.00
    df['EXIT'] = 0.00
    trac = df['trac']
    up   = df['TARG']
    dn   = df['STOP']
    out  = df['OUT']
    ent  = df['ENTRY']
    exit = df['EXIT']

    #the only difference with validation entry is this first row 
    #will have an eextra layer for waiting...

    ## then adding tranches will just go under each up and dn... 
    ## they will be independant acnts operating in the same frame work...
    # then get add together later with a weight values...
    
    #blue print for trailing stop statmnet
    #df['dn_moved_up'] = df[DN_TARG].shift() > df[DN_TARG].shift(2)
    #?? IF trailing == True: # pretty sure i can just add this to the thing
    #        if df['dn_moved_up'][i] == True:
    #        #if df[DN_TARG][i-1] > df[DN_TARG][i-2]:
    #            dn[i] = df[DN_TARG][i-1]

    ''' IF YOU GET TIERD:
        of this function erroring out just put this into the whole thing, however i would prefer
        for the backtest to stop before this stage if there are no buy signals'''
    #if len(df[df['buy']==True]) > 0

    ENTRY_PNT = 'close'
    if len(limit) > 0:
        ENTRY_PNT = limit

    '''i dont know why this line breaks it... maybe it cant be true so .shift'''
    df[BUY] = (df[BUY]==True) & ( df['close']>df[DN_TARG])

    for i in range(1,len(df)):
        if (trac[i-1]==False) & (df[BUY][i]==True):
            trac[i] = True
            up[i] = df[UP_TARG][i]
            dn[i] = df[DN_TARG][i]
            ent[i]= df[ENTRY_PNT][i]
        if (trac[i-1] == True)  & (df['low'][i]<dn[i-1]):
            out[i] = True
            trac[i] = False
            if (df['open'][i]<dn[i-1]):
                exit[i] = df['open'][i]
            else:
                exit[i] = dn[i-1]
        if (trac[i-1] == True) & (df['high'][i]> up[i-1]):
            out[i] = True
            trac[i] = False
            if (df['open'][i]> up[i-1]):
                exit[i] = df['open'][i]
            else:
                exit[i] = up[i-1]
        if (out[i-1] == False) & (trac[i-1]==True):
            up[i] = up[i-1]
            
            #i need dn to update based on which is bigger ( dn)

            dn_update = max(df[DN_TARG][i-1],dn[i-1])
            dn[i] = dn_update
            trac[i] = trac[i-1]
            ent[i]  = ent[i-1]

    
    #grab the first buy to scale price
    first_buy = df[df[BUY]==True].close.iloc[0]
    df['SCALE_ACNT'] = first_buy

    #placeholders
    scale = df['SCALE_ACNT']
    df['TRAC'] = df['trac']
    df['PNL']  = 0.00
    df["PNL_PCT"] = 0.00

    hl(df)
    #thi should have been built into atr_targs
    #IM GOING TO ADD NON PYRIMIDING ACNT VALUE TO THIS AS WELL!!!

    # afirm that the last col is flat positions
    df['TRAC'][-1] = False
    exit[-2] = df.close[-2]
    #simulation results
    for i in trange(1,len(df)):
        if (df['TRAC'][i] == False) & (df['TRAC'][i-1]==True):
            df['PNL'][i] = exit[i-1] - df['ENTRY'][i-1]
            df['PNL_PCT'][i] = df['PNL'][i]/df['ENTRY'][i-1]
            scale[i] = (scale[i-1]*df['PNL_PCT'][i])+scale[i-1]
        else:
            scale[i] = scale[i-1]
    #plot_capital = True
    if plot_capital == True:
        df['ENTRY_scale']= df['ENTRY'].replace(True,1).replace(1,df.close)
        df[['ENTRY_scale','close','SCALE_ACNT']].iplot(theme='solar',fill=True,title=(strat_name+' Capital Scaled'))

    
    #df['win_cnt'] = df['PNL_PCT']>0
    #df['los_cnt'] = df['PNL_PCT']<0  
    #win_cnt = df['win_cnt'].sum()
    #los_cnt = df['los_cnt'].sum()
    #total   = win_cnt+los_cnt
    #win_pct = (win_cnt/total)
    

    ### RESULTS MODS = [
    df['acnt'] = 1000
    for i in trange(1,len(df)):
        if df['PNL_PCT'][i] != 0:
            # adjust acnt value based on pct changes
            df['acnt'][i] = df['acnt'][i-1]+(df['PNL_PCT'][i]*df['acnt'][i-1])
        else:
            df['acnt'][i] = df['acnt'][i-1]
            
        
        
    
    df['win_cnt'] = df['PNL_PCT']>0
    df['los_cnt'] = df['PNL_PCT']<0
    win_cnt = df['win_cnt'].sum()
    los_cnt = df['los_cnt'].sum()
    total   = win_cnt+los_cnt
    win_pct = (win_cnt/total)
  
    ### RESULTS MODS     
    win_cnt = df['win_cnt'].sum()
    los_cnt = df['los_cnt'].sum()
    total   = win_cnt+los_cnt
    win_pct = (win_cnt/total)
    final_pnl= (df['acnt'][-1]-1000)/1000*100

    print('strat_name      :',strat_name)
    print('final_acnt value:',df['acnt'][-1])
    print('total_+trades   :',total)
    print('wins            :',win_cnt)
    print('loss            :',los_cnt)
    print('win_percent     :',(win_pct))
    print('final_pnl       :',final_pnl,'%')

    d = {}
    li =[]
    
    d['strat_name']        = strat_name
    d['final_acnt_value']  = df['acnt'][-1]
    d['total_trades']      = total
    d['wins']              = win_cnt
    d['loss']              = los_cnt
    d['win_pct']           = win_pct*100
    d['final_pnl']         = final_pnl

    li.append(d)

    result = pd.DataFrame(li)

    ### RESULTS MODS END
 
#need a candelstick PLT SUCKA!!!
    if plot == True:
        df['trac_scale'] = df['trac'].replace(True,1).replace(1,df.close) 
        df['TARG_scale'] = df['TARG'].replace(True,1).replace(1,df.close)#.replace(0,np.nan)
        df['STOP_scale'] = df['STOP'].replace(True,1).replace(1,df.close)#.replace(0,np.nan)
        df['OUT_scale']  = df['OUT'].replace(True,1).replace(1,df.close)
        df['ENTRY_scale']= df['ENTRY'].replace(True,1).replace(1,df.close)
        df['EXIT_scale'] = df['EXIT'].replace(True,1).replace(1,df.close)

        #[df['TARG_scale'][]]

        line_one='TARG_scale'
        line_two='STOP_scale'
        scale_one='SCALE_ACNT'
        jenay(df,line_one=line_one,line_two=line_two,scale_one=scale_one,title=strat_name)

        #df[['trac_scale','close','TARG_scale','STOP_scale','ENTRY_scale','OUT_scale','EXIT_scale']].iplot(theme='solar',fill=True,title=(strat_name+' Target - plot'))
   
    if plot == True:
        result[['wins','loss']].sum().plot(kind='pie')



    return result


from datetime import datetime
def riz_delta(df,DN_THRESH=7,UP_THRESH=95,buy_col=True,riz_to_high_level=60,riz_len= 2,limit_lookback=False,time_delta=52,plot=True,return_df=True):
    '''
    RETURNS:
        1.riz - results_dataFrame
        2. original df - if return_df==true
    
    Makes Riz Targets
        COLUMNS:
            1.rix_up - first up corner coming out of extream levels
            2.rix_dn - first dn corner coming out of extream levels
    TODO:        
            3.riz_buy
    '''
    li = []

    #Function
    if limit_lookback==True:
        last_year = datetime.now() - pd.Timedelta(weeks=time_delta)
        print('lastyear',last_year)
        df = df[df.index > last_year]

    ##from stealing_fire import sola,hl
    import pandas_ta as pta


    df['riz'] = pta.rsi(df.close,length=riz_len)
    d = {}
    DN_THRESH = 7
    UP_THRESH = 95

    #saving results for  documenting thee research
    #d['sheet']     = sheet
    d['DN_THRESH'] = DN_THRESH
    d['UP_THRESH'] = UP_THRESH

    print('DN_THRESH:',DN_THRESH)
    print('UP_THRESH:',UP_THRESH)



    df['low_ex'] = df['riz'] < DN_THRESH
    df['high_ex']= df['riz'] > UP_THRESH

    hl(df)

    # How Often do Riz Corners Signal a Push?

    hl(df)
    df['rix_up'] = (df['low_ex']==False) & (df['low_ex'].shift()==True)
    df['rix_dn'] = (df['high_ex']==False) & (df['high_ex'].shift()==True)
    hl(df)

    df['rix_bionary'] = False

    rib = df['rix_bionary']
    rix = df['rix_up']
    rixd= df['rix_dn']

    for i in range(1,len(df)):
        if rix[i] == True:
            rib[i] = True
        elif rixd[i] == True:
            rib[i] = False
        else:
            rib[i] = rib[i-1]

    hl(df)

    df['swix'] = rib != rib.shift()

    rixdf = df[df['swix'] == True]

    rixdf['low_to_high_ex_diff'] = rixdf['close'] - rixdf['close'].shift()

    rixdf['positive_delta']      = rixdf['low_to_high_ex_diff'] > rixdf['low_to_high_ex_diff'].shift()
    rixdf['negitive_delta']      = rixdf['low_to_high_ex_diff'] < rixdf['low_to_high_ex_diff'].shift()

    
    hl(rixdf.groupby('rix_up').agg('mean'))

    dflen = len(rixdf)/2
    if plot == True:
        jenay(df,scale_two='high_ex',scale_one='low_ex')
        rixdf.groupby('rix_up').agg('mean')['low_to_high_ex_diff'].iplot(theme='solar',kind='bar')    
        rixdf.groupby('rix_up').agg('sum')[['positive_delta','negitive_delta']].iloc[0].plot(kind='pie')

    rdf = rixdf.groupby('rix_up').agg('sum')[['positive_delta','negitive_delta']]

    po = rdf['positive_delta'].iloc[0]
    ne = rdf['negitive_delta'].iloc[0]

    delta_percent = str(round(po/(po+ne)*100)) + ' %'
    print('delta_percent',delta_percent)
    d['delta_percent']        = delta_percent
    rdf['rix_delta_accuracy'] = delta_percent

    start_date = df.index[0]
    end_date   = df.index[-1]
    print('start_date',start_date)
    print('end_date',end_date)
    d['start_date'] = start_date
    d['end_date']   = end_date
    d['TOTALTIME'] = end_date - start_date
    d['positive_delta'] = po
    d['negitive_delta'] = ne

    if buy_col == True:
        df['buy'] =  (df['rix_up']==True) & (df['riz'] < riz_to_high_level)


    li.append(d)
    rrdf = pd.DataFrame(li)
    
    ouput = rrdf
    if return_df == True:
        output = [rrdf,df]
    return output






'''
TREND MAP 
will be a funtion that add what ever trend criteria you 
want to test.
    EXAMPLE:    
        if you want a [dialy / weekly] :
            [hh_hl / riz ] 

'''
from sklearn.preprocessing import StandardScaler
def scale(df):
    scale = StandardScaler()
    scaled=scale.fit_transform(df)
    sdf   = pd.DataFrame(scaled,columns=df.columns)
    sdf.index = df.index
    return sdf


def count_this(df,thing,reset,col_name):
    '''
    creates a new col that keeps a rolling count of 'thing' until 'reset'
    ITS BIASED to the COUNT!! 
       if the counting thing is true it wont go through the other if statments
    
    TAKES:
        1.df
        2.thing- column of bools
        3.reset - column of bool
        4. columns name - str: the name of your new counting columns
    '''
    
    df[col_name] = 0
    for i in range(1,len(df)):
        if df[thing][i] == True:
            df[col_name][i] = 1 + df[col_name][i-1]
        elif df[reset][i] == True:
            df[col_name][i] = 0
        else:
            df[col_name][i] = df[col_name][i-1]
    return df




def bipolar(df,first,last,col):
    '''
    a quick way to have a bionary read on the world
    
    df[col] is true if first is true and remians true until last is true
    
    - good for wiating on multiple conditions
    
    returns a columns: 
        that stays true till 'last' becomes true
    '''
    df[col] = False
    for i in range(1,len(df)):
        if df[first][i] == True:
            df[col][i] = True
            
        elif df[last][i] == True:
            df[col][i] = False
        else:
            df[col][i] = df[col][i-1]



def vtrend(df,trend_thresh=8,plot=True ):
    '''
    TREND MAP - vma trend
    '''

    df['vma_green'] = df['vma'] > df['vma'].shift()
    df['vma_red'] = df['vma'] < df['vma'].shift()
    #hl(df)
    if plot == True:
        jenay(df,scale_one='vma_green',scale_two='vma_red')
        # counting the green moves
    df['green_cnt'] = 0
    df['red_cnt']   = 0
    for i in range(1,len(df)):
        if df['vma_green'][i] == True:
            df['green_cnt'][i] = 1 + df['green_cnt'][i-1]
            
        if df['vma_green'][i] == False:
            df['green_cnt'][i] = 0

        if df['vma_red'][i] == True:
            df['red_cnt'][i] = 1 + df['red_cnt'][i-1]

        if df['vma_red'][i] == False:
            df['red_cnt'][i] = 0

    # how many up bars on the vma before you condiser it up...
    df['up_trend'] = df['green_cnt'] > trend_thresh
    df['dn_trend'] = df['red_cnt'] > trend_thresh

    #creating a bionary columns of the last trend direction 
    bipolar(df,'up_trend','dn_trend','vma_uptrend')
    #the oposite of that column
    df['vma_dntrend'] = df['vma_uptrend'] == False

    if plot == True:
        # plotting the plot trend direction
        jenay(df,line_one='plot.3',line_two='vma',scale_one='vma_uptrend',scale_two='vma_dntrend')



def trendmap(df,vma=True,vtrend_thresh=8):
    if vma==True:
        if 'vma' in df.columns:
            vtrend(df,trend_thresh=vtrend_thresh)
        else:
            print('VMA is not in the dataframe')
    

def save_function(results,STUDY):
    '''
    concatonates a list of backtest results from a loop and appends or creates the aggrigated results csv
    or creates it (nd the directory ag_output/) if it doesnt exitst.
        does the same to the study sheet. 

    TAKES:
        1.results list -  ( of backtest dataframes from loops)
        2. STUDY - STR: the name of your particular study
    '''
    try: 
        '''
        -SAVE  RESULTS ZONE-|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
        '''
        rdf = pd.concat(results)
        rdf['study'] = STUDY

        # LAST ADDITIONS TO THE DATASET
        print('made it!')
        #rdf['backtest_time'   ] = str(datetime.now())
        #rdf['backtest_runtime'] = datetime.now() - start_time
        #rdf['mention_criteria'] = 'NONE'#condition
        #
        #'''
        #ADD GLOBAL STUDY VARIABLES TO THE RESULTS
        #'''
        #for key in study_traits:
        #    rdf[key] = study_traits[key]



        #output directory
        apath     =         'agg_ouput_data/'
        # aggrigated spreadsheet
        save_name =apath+   'collection.csv'

        #create directory if its not there
        if not os.path.exists(apath):
            os.mkdir(apath)
        #save results data if it not there
        if not os.path.exists(apath+save_name):
            rdf.to_csv(save_name,index=False)
        #otherwise append it
        else:
            ordf = pd.read_csv(save_name)#,index_col='index')
            ordf  = ordf.append(rdf)
            #drop duplicates
            ordf = ordf.drop_duplicates()
            ordf.to_csv(save_name,index=False)

        '''SAVE THE STUDY'''
        study_path = apath+STUDY+'_study.csv'

        if not os.path.exists(study_path):
            rdf.to_csv(study_path,index=False)
        else:
            rsdf = pd.read_csv(study_path)
            rsdf = rsdf.append(rdf)
            #drop duplicates
            rsdf = rsdf.drop_duplicates()
            rsdf.to_csv(study_path,index=False)
        print('\n.\n.\n. savef! \n .\n.\n.')
    except BaseException as b:
        print('no save cuz:')
        print(b)


def sobar(df,title='TITLE HERE'):
    '''
    bar plot
    '''
    df.iplot(theme='solar',kind='bar',title=title)

    
import numpy as np

import pandas as pd
import seaborn as sns

def grid_map(df,col_one,col_two,content_col='final_pnl',plot=True):
    '''
    makes a grid for plotting varable differances and shit. 
    '''
    
    cols = list(set(df[col_one].sort_values()))
    rows = list(set(df[col_two].sort_values()))
    rows
    zs = np.zeros((len(rows),len(cols)))
    gdf= pd.DataFrame(zs,columns=cols)
    gdf.index = rows 
    
    for col in gdf.columns:
        for row in gdf.index:
            mask = df[df[col_one]==col] #& df['slow']==row]  
            mask 
            gdf[col][row] = mask[mask[col_two]==row][content_col]
    # Sorting Values 
    gdf = gdf.T[sorted(gdf.index)].T
    gdf = gdf[sorted(gdf.columns)]
    
    if plot == True:
        sns.heatmap(gdf)
    
    return gdf
def weekly_pull(df):
    '''
    TAKES: dataframe
    RETURNS: weekly dataframe,  , with offset index to provide you with all the solid data
        you would for sure have acceess to 
        USEAGE:
            this is designed to be used with weekly_push so you can add
            indeicators to the weeklhy time frame and then push them
            back into your main timeframe dataframe...
    '''
    # extract weekly function
    df['week'] = df.index.week
    df['year'] = df.index.year
    df['week_id'] = df['year'].astype(str) + '_' + df['week'].astype(str)
    df['index'] = df.index
    df

    df.index

    df

    df.groupby('week_id').agg('last')['index']
    df.groupby('week_id').agg('first')['open']


    INDEX = df.groupby('week_id').agg('last')['index'].astype(str)#.shift()
    OPEN = df.groupby('week_id').agg('first')['open']
    CLOSE = df.groupby('week_id').agg('last')['close']
    HIGH = df.groupby('week_id').agg('max')['high']
    LOW = df.groupby('week_id').agg('min')['low']
    VOL = df.groupby('week_id').agg('sum')['volume']

    cols = [INDEX,OPEN,LOW,HIGH,CLOSE,VOL]

    wdf = pd.DataFrame(cols).T
    
    wdf['id'] = wdf.index
    # shift the index so as to only show known data 
    wdf['time'] = wdf['index']
    wdf = wdf.set_index('time')
    wdf.index = pd.to_datetime(wdf.index)
    wdf = wdf.sort_values(wdf.index.name)
    return wdf

def weekly_push(df,wdf):
    '''
    TAKES: merges weekly dataframe into one with a shorter timeframe index. 
    '''
    
    [wdf.rename(columns={col:('week_'+col)},inplace=True) for col in wdf.columns]

    
    wdf['week_index'] = wdf['week_index'].shift()
    wdf['week_id'] = wdf['week_id'].shift(-1)
    wdf = wdf.set_index('week_id')
    wdf


    # mix function 
    mixdf = df.set_index('week_id').join(wdf).set_index('index')
    mixdf.index = pd.to_datetime(mixdf.index)
    #mixdf = mixdf.sort_values(mixdf.index)
    mixdf

    mixdf = mixdf.groupby(mixdf.index).agg('first')#.sort_values(mixdf.index)
    return mixdf
def monthly_pull(df):
    '''
    TAKES: dataframe
    RETURNS: monthly dataframe,  , with offset index to provide you with all the solid data
        you would for sure have acceess to 
        USEAGE:
            this is designed to be used with monthly_push so you can add
            indeicators to the monthly time frame and then push them
            back into your main timeframe dataframe...
    '''
    # extract monthly function
    df['month'] = df.index.month
    df['year'] = df.index.year
    df['month_id'] = df['year'].astype(str) + '_' + df['month'].astype(str)
    df['index'] = df.index
    df

    df.index

    df

    df.groupby('month_id').agg('last')['index']
    df.groupby('month_id').agg('first')['open']


    INDEX = df.groupby('month_id').agg('last')['index'].astype(str)#.shift()
    OPEN  = df.groupby('month_id').agg('first')['open']
    CLOSE = df.groupby('month_id').agg('last')['close']
    HIGH  = df.groupby('month_id')['high'].agg('max') # IF YOU GET VALUE ERROR TOO MANY VALUES SWITCH COLUMN
    LOW   = df.groupby('month_id')['low'].agg('min')
    VOL   = df.groupby('month_id')['volume'].agg('sum')

    cols = [INDEX,OPEN,LOW,HIGH,CLOSE,VOL]

    wdf = pd.DataFrame(cols).T
    
    wdf['id'] = wdf.index
    # shift the index so as to only show known data 
    wdf['time'] = wdf['index']
    wdf = wdf.set_index('time')
    wdf.index = pd.to_datetime(wdf.index)
    wdf = wdf.sort_values(wdf.index.name)
    return wdf
    
def monthly_push(df,wdf):
    '''
    TAKES: merges monthly dataframe into one with a shorter timeframe index. 
    '''
    [wdf.rename(columns={col:('month_'+col)},inplace=True) for col in wdf.columns]

    
    wdf['month_index'] = wdf['month_index'].shift()
    wdf['month_id'] = wdf['month_id'].shift(-1)
    wdf = wdf.set_index('month_id')
    wdf


    # mix function 
    mixdf = df.set_index('month_id').join(wdf).set_index('index')
    mixdf.index = pd.to_datetime(mixdf.index)
    #mixdf = mixdf.sort_values(mixdf.index)
    mixdf

    mixdf = mixdf.groupby(mixdf.index).agg('first')#.sort_values(mixdf.index)
    return mixdf

    INDEX = df.groupby('week_id').agg('last')['index'].astype(str)#.shift()
    OPEN = df.groupby('week_id').agg('first')['open']
    CLOSE = df.groupby('week_id').agg('last')['close']
    HIGH = df.groupby('week_id').agg('max')['high']
    LOW = df.groupby('week_id').agg('min')['low']
    VOL = df.groupby('week_id').agg('sum')['volume']

    cols = [INDEX,OPEN,LOW,HIGH,CLOSE,VOL]

    wdf = pd.DataFrame(cols).T
    
    wdf['id'] = wdf.index
    # shift the index so as to only show known data 
    wdf['time'] = wdf['index']
    wdf = wdf.set_index('time')
    wdf.index = pd.to_datetime(wdf.index)
    wdf = wdf.sort_values(wdf.index.name)
    return wdf
def this_or_that(df,up_target,dn_target):
    '''
    TAKES: two targets, up and down and tells you which one will happen first in the future
    RETURNS:
        df['up_bf_dn'] - column: True if up target was hit before dn target
        df['up_bf_dn_x100'] - column: to scale with occilators like RSI
        
    '''
    df['up_bf_dn'] = None
    for i in trange(len(df)):
    #i = 0

        value = df['close'][i]
        index = df.index[i]
        uptarg= df[up_target][i]
        dntarg= df[dn_target][i]
        print('value:',value)
        print('index:',index)
        print('up:',uptarg)
        print('dn:',dntarg)

        #for i in range(len(df)):
        up_or_down = None
        qi   = i+1
        try:
            while up_or_down == None:

                if df['high'][qi] > uptarg:
                    up_or_down = True#'upped'
                if df['low'][qi] < dntarg:
                    up_or_down = False#'downed'
                else:
                    qi += 1
                print(qi)
            print(up_or_down)
            df['up_bf_dn'][i] = up_or_down
        except Exception:
            pass
    df['up_bf_dn'] = df['up_bf_dn'].replace(False,0)# = df['up_bf_dn']
    df['dn_bf_up'] = (df['up_bf_dn']==False)
    df['up_bf_dn_x100'] = df['up_bf_dn'] * 100
    
        
        
        

import pandas_ta as pta
def std_targets(df,up_multiple=2,dn_multiple=1):
    '''
    TAKES: df, up_mul , dn_mul
    RETURNS: 
        atr:
        up_atr : 
        dn_atr :
    '''
    df['atr'] =  pta.atr(df.high,df.low,df.close)
    df['up_atr'] = df['close'] + (df.atr * up_multiple)
    df['dn_atr'] = df['close'] - (df.atr * dn_multiple)
    
    df['up_targ'] = df['up_atr']
    df['dn_targ'] = df['dn_atr']

    return df
'''
DAILY DIGGS FUNCTIONS >>---->
'''
def say(words):
    engine.say(words)
    engine.runAndWait()



def is_algo_active_checker(df,algo_name,table_name):
    '''
    1)checks if the algo was triggered on df
    2) checks if buy was triggered ( and tells you if it is )
    3) appends a dictionary of current status on algo . 
    4) TODO : updates a database with --a) algo status --b) algo history #start with just a dataframe for starters
    5) TODO : plots data only if algo is active
    '''
    di = {}
    di['algo_name'] = algo_name
    di['table_name']= table_name
    hit = False
    if df['buy'][-1] == True: 
        say('buy signal on {}'.format(ticker+' '+time_frame))
        print('++++++++++++++++++++++++++++++++++++++++++++++BUY+++++++++++++++++++++++++++++++++++++++++',table_name)
        hit = True
        di['buy_signal_read'] = datetime.now()
        di['buy_signal_time'] = df.index[-1]
    if 'trac' in df.columns:
        if (df['trac'][-2] == True) or (df['TRAC'][-2] == True):
            hit = True
            say('algo is active on {}'.format(table_name))
            print('say algo is active on the thing!!!')
            di['active_algo'] = True
            di['target']      = df['TARG'][-2]
            di['stoploss']    = df['STOP'][-2]
            di['entry']       = df['ENTRY'][-2]
    # INSERT --TRACKING TABLE-- UPDATE LOGIC
    # if table_name in --TRACKING TABLE--.index 
    #      - check if the algo was last active
    #      - if was and is not now : 
    #             - say ( '!!! yo are you out of this trade because you should be!!!')
    #      - if it wasnt now it is :
    #             - say ( !!! YO GET IN THIS TRADE !!!!)
    #             - ASK ( ?DID YOU GET IN THIS TRADE YET?)
    #                   - UPDATE: an active log with answer
    # elif hit == True : ( and its not in --TRACKING TABLE--)
    #      - ADD IT ! 
    # this should also store a list of buy entry dates and check if there are new buy entry dates since last checking.
    # make a fucking database function already 
    if hit == False:
        di = {}
    return di 

def merge_tweets_with_price(ticker,plot=True):
    '''
    this takes the index from mention grid(df) and merges
    it with price data and plots it. 
    '''
    df['twitter_mentions'] = 0
    # get a list of times ticker was tweeted
    mention_dates = grid[grid[ticker]>0][ticker].index

    for m in trange(len(mention_dates)):
        try:
            # grab first row  from isolated data after event 
            first_data = df[df.index>mention_dates[m]].iloc[0].name
            # either grab the in dex or insert cell directly 
            df['twitter_mentions'][first_data] = 1
        except IndexError:
            pass

    if plot == True:
        jenay(df,scale_two='twitter_mentions',title=('TwitterMentions: '+ticker))
        
import sqlalchemy as sql
import pandas as pd
database        = 'twitter'
table_name      = 'mention_index'
merge_with_old  = True
add_new_columns = True
index_name      = None
if_exists       = 'append'
save_index      = True
set_n_sort_index= True
drop_duplicates = True
def save_database(df,table_name,database='twitter',merge_with_old=True,add_new_columns=True,index_name=None,if_exists='append',save_index=True,set_n_sort_inde=True,drop_duplicates=True):
    eng = sql.create_engine('postgresql://postgres:password@localhost/{}'.format(database))

    # List tables 
    con      = eng.connect()
    tables   = eng.table_names()
    table_df = pd.DataFrame(tables,columns=['tables'])
    #print(table_df)

    if (table_name in list(tables)) and (merge_with_old == True):
    #Load Data From The Base
        a=pd.read_sql_query('select * from "{}"'.format(table_name),con=eng)
        if set_n_sort_index:
            if index_name == None:
                a = a.set_index(df.index.name)
                a = a.sort_values(a.index.name)
            else:
                a = a.set_index(index_name)
                a = a.sort_values(index_name)
                    #Drop Duplicates
        if drop_duplicates == True:
            a = a.drop_duplicates()
            a = a[~a.index.duplicated(keep='first')]
        if merge_with_old == True:
            df = df[df.index>a.index[-1]]
            df = a.append(df)



        # Add Columns If Not In Database
        if add_new_columns == True:
            left_overs = set(df.columns) - set(a.columns)
            print('columns in Database:',len(left_overs),left_overs)
            if len(left_overs) > 0:
                for col in left_overs:
                    con.execute('ALTER TABLE {} ADD COLUMN "{}" TEXT NULL;'.format(table_name,col))
        else:
            # only append those that are already in database
            df = df[a.columns]

    
    # Save Data To Base
    df.to_sql(table_name,con,if_exists = if_exists, index = save_index)
    print('SAVED!:',table_name,'DATABASE:',database)

    con.close()

def pull_database( database,table_name=None):
    '''
    if table_name is None it will return list of tables
    '''
    eng = sql.create_engine('postgresql://postgres:password@localhost/{}'.format(database))
    # List tables 
    con      = eng.connect()
    tables   = eng.table_names()
    table_df = pd.DataFrame(tables,columns=['tables'])
    #print(table_df)
    if table_name == None:
        con.close()
        return table_df # this was tables i hope i didnt just break it...
    else:
        if table_name in tables:
            #Load Data From The Base
            a=pd.read_sql_query('select * from "{}"'.format(table_name),con=eng)
            return a 
ticker = 'ETH'
time_frame = '1d'
start_date = '2020-03-01-00-00'


cryptos = ['ELGD','BTC','ORN','ETH']
#if ticker in cryptos:
from Historic_Crypto import HistoricalData 

def get_crypto(ticker,time_frame,start_date = '2020-03-01-00-00'):
    coin = ticker.upper() + '-USD'
    print(coin)
    #timeframes
    if time_frame == '1d':
        seconds = 86400
    if time_frame == '1hr':
        seconds = 3600
    if time_frame == '15min':
        seconds = 900

    df = HistoricalData(coin,granularity=seconds ,start_date=start_date).retrieve_data()
    return df

def plot_n_scrape(ticker,time_frame='1hr',numidex=False,title=None,lineli=[],mask=None,h_line=None):
    '''
    scrapes a stock ticker , plots it and returns a dataframe as well as 
    updateing the 'stock' database
    TAKES:
        1.ticker : str
        2.time_frame : str
            a) '15min'
            b) '1hr'
            c) '1d'
        3. numidex : bool (replaces timeseries index with timeseries labeled string index 
                to eliminate gaps in the plot. ( gapless plots for intraday) )
        4. title : str . 
        5. h_line : int : this is just a horizontal line
    TODO: 
        - MAKE IT UPDATE DATABASE 
        - MAKE IS PULL FROM DATEBASE
        - MAKE IT INTEGRATE TWEETS OR OTHER EVENTS AUTOMATIACALLY 
    the new and improved plot n scrape...
    '''
    
    # Scrape The Data From Different Sources Depending On What Time Frame
    df    = get_some(ticker,time_frame=time_frame)
    # Mask Data If Specified
    #if mask != None:
    #    df = df[df.index>mask]
    # Name The Sheet With Ticker And Time Frame
    if title == None:
        title = ticker.upper() + '_' + time_frame
    if h_line != None:
        df['h_line'] = h_line
        lineli = ['h_line']
        
    # Box Chart Planning Function
    jenay(df,title=title,numidex=numidex,line_list=lineli)
    
    return df





# XXX XXX XXX XXX XXX XXX XXX XXX FINDING FIRE XXX XXX XXX XXX XXX XXX XXX XXX XXXXXXXXXXXXX


# XXX GOING TO BE CLEANINGN HOUSE SOON XXX 

'''
many of these functions are outdated. 
finding_fire will be researved for : 
    - RESEARCH
    - BACKTESTING
stealing_fire will be reserved for : 
    - databaseing
    - server interation
    - trading tools
    - broking api's
        - webull
        - coinbase
        - binance
        - exct. 
    - scraping tools 
    - twitter tools ... 


'''

# TODO: 
#      start going through and marking things for deconstruction or relocation
#      being carefull not to remove anything thats going to throw a wrench into 
#      perctectly nice functioning systems .... ohhhh boy!!! 
#
#      - clean twitter shit up

### ---MOVE THE ALGOS TO PHENIX--- ( needs a cooler name how about the : Temple_Of_AlgoRand...)
## and then battle ready algoFunctions go in active....



def easybake_fastquant(df,result):
    '''
    takes your backtest dataframe from one_stop or vally_stop
        RUNS THE SAME TEST WITH FAST QUANT : 
            and mixes the results
        
    '''
    
    from fastquant import backtest
    #CONVERS ONE_STOP BUY PROTOCAL INTO FASTQUANT
    df['fq_buy']  = (df['TRAC']==True)  & ( df['TRAC'].shift()==False)
    df['fq_sell'] = (df['TRAC']==False) & ( df['TRAC'].shift()==True)
    df['fq_buy'] = df['fq_buy'].replace(True,1).replace(False,0)
    df['fq_sell'] = df['fq_sell'].replace(True,100).replace(False,0)
    df['custom'] = df['fq_buy'] + df['fq_sell']
    #hl(df[['fq_buy','TRAC','fq_sell','custom']])

    fq_result = backtest('custom',
                            df,
                            plot=False,
                        init_cash=1000,
                            )

    # REMOVE THE DICTIONARY : ( DATABASES DONT LIKE EM )
    df_dic = fq_result['max'][0]
    for key in df_dic.keys():
        fq_result['max_'+key] = df_dic[key]
    fq_result = fq_result.drop('max',axis=1)
    print(fq_result.T)

    return result.join(fq_result)
      

def back_burner_buysignal(buy,RSI_THRESH=40):
    '''
    Adds Buy column
    BUY OPTIONS:
        1. first_oversold
        2. TODO: add more
        
    '''
    m1,m2,m3,m4,m5 = 5,15,25,50,100
    df['ma1']  = df.close.rolling(m1).mean()
    df['ma2']  = df.close.rolling(m2).mean()
    df['ma3']  = df.close.rolling(m3).mean()
    df['ma4']  = df.close.rolling(m4).mean()
    df['ma5']  = df.close.rolling(m5).mean()
    df['reset'] = df['ma4'] < df['ma5']
    df['bull_run'] = (df['ma1']>df['ma2']) & ( df['ma2']>df['ma3'])&(df['ma3']>df['ma4'])&(df['ma4']>df['ma5'])
    df['first_bull'] = (df['bull_run'] == True ) & (df['bull_run'].shift() == False )
    #RSI
    
    df['rsi']              = pta.rsi(df.close)
    df['low_rsi']          = df['rsi'] < RSI_THRESH
    df['last_rsi_was_low'] = df['low_rsi'].shift()
    #Alternate between First Bull Run and Signal
    bipolar(df,'first_bull','low_rsi','waiting')
    #Buy signals
    df['first_oversold'] = (df['waiting'].shift() == True) & ( df['low_rsi']==True) #& (df['waiting_on_bullrun']==False)
    ## for now the only one
    df['buy'] = df[buy]



    if plot == True:
        jenay(df,scale_one='waiting',scale_two='first_oversold')


def falcon_backtest(df,mydic,research_project=None):
    '''
    TAKES: 
        1) price dataframe with buy signals 
        2) paramater_dictionary
        3) and research_project name (optional)
    RETURNS:
        1) backtest results in the form of oa dataframe. 
        2) appends the data to the research dump database table
        3) creates or appends a :'research_project' table 
            - for what ever specific project  you are working on  
    '''
    if len(df[df['buy'] == True]):
        # Simulate Trades
        result = one_stop(df,
                  strat_name=str(mydic),
                  plot=plot,
                  plot_capital=plot)
        # Add Conditions & Params to Results Data
        #for i in mydic.keys():
        #    if mydic[i] != None:
        #        result[i] = mydic[i]
        result['target_type'] = 'one_stop' 
        #Fast Quant Your Face
        try:
            result = easybake_fastquant(df,result)
        except:
            pass

        result['algo_type']    = 'one_stop' 
        result['start_date']   = df.index[0]
        result['end_date']     = df.index[-1]
        if '.csv' in sheet:
            result['security'] = sheet.split(' ')[1]
        results.append(result)
        
        '''
        DATABASE ZONE:
            1. save to repo-dump
            2. if project_name is not none. also save everything in that project table
            
            SIDENOTE: IF THIS SLOWS BACKTEST'S DOWN TO MUCH 
                GOBACK, to doing them in bundles...
        '''
        push_database(result,'ResearchDump','research',save_index=True,drop_duplicates=True,time_series=False)#,index_name='strat_name')
        if research_project != None:
            push_database(result,research_project,'research',save_index=True,drop_duplicates=True,time_series=False)#,index_name='strat_name')

        return result
        
        

def push_database(df,table_name,database='twitter',time_series=True,add_new_columns=True,index_name=None,if_exists='append',save_index=True,set_n_sort_index=True,drop_duplicate_index=True,drop_duplicates=True,address= None):
    '''
    SIMPLIFY SIMPLIFY SIMPLIFY - dave
    takes a pandas dataframe . 
        - creates table if not exissts
        - or appends the original ( droping duplicates)
            - including adding columns that wern't there. 

    
    '''
    if address == None:
        address = 'postgresql://postgres:password@localhost/'
    eng = sql.create_engine(f'{address}{database}')
    
    # List tables 
    con      = eng.connect()
    tables   = eng.table_names()
    table_df = pd.DataFrame(tables,columns=['tables'])
    #print(table_df)

    if (table_name in list(tables)) :#and (merge_with_old == True):
    #Load Data From The Base
        a=pd.read_sql_query('select * from "{}"'.format(table_name),con=eng)
        
        saved_already = False
        if drop_duplicate_index == True:
            print('dropping duplicated index')
            a = a.drop_duplicates()
            a = a[~a.index.duplicated(keep='first')]
        if drop_duplicates == True:
            a = a.drop_duplicates()

        if time_series == True:
            print('time series data')
            print('original length:',len(df))
            df = df[df.index>a.index[-1]]
            print('length after mask:',len(df))
            print('origianl data series:',len(a))
            df = a.append(df)
            print('now with updated data:',len(df))
        
        # Add Columns If Not In Database - 
        '''
        THIS IS THE QUICKEST SOLUTION  FOR NOT ADDING COLUMNS. 
            - im just replace the database table after merging old and new in pandas
        '''
        if add_new_columns == True:
            left_overs = set(df.columns) - set(a.columns)
            print('columns in Database:',len(left_overs),left_overs)
            if len(left_overs) > 0:
                print('you have new columns:')


                df = a.append(df)
                # Save Data To Base
                df.to_sql(table_name,con,if_exists = 'replace' , index = save_index)
                print('REPLACED!:',table_name,'DATABASE:',database)
                print('had to replace it with new columns')
                saved_already = True
                #for col in left_overs:
                #    con.execute('ALTER TABLE "{}" ADD COLUMN "{}" TEXT NULL;'.format(table_name,col))
        if set_n_sort_index:
            if index_name == None:
                try:
                    a = a.set_index(df.index.name)
                    a = a.sort_values(a.index.name)
                except:
                    pass
            else:
                try:
                    a = a.set_index(index_name)
                    a = a.sort_values(index_name)
                        #Drop Duplicates
                except:
                    pass
            


        if saved_already == False:
            if drop_duplicates == True:
                # Save Data To Base
                df.drop_duplicates().to_sql(table_name,con,if_exists = if_exists, index = save_index)
                print('SAVED!:',table_name,'DATABASE:',database)
            else:
                # Save Data To Base
                df.to_sql(table_name,con,if_exists = if_exists, index = save_index)
                print('SAVED!:',table_name,'DATABASE:',database)
    else:
        df.to_sql(table_name,con,if_exists = if_exists, index = save_index)
        print('SAVED!:',table_name,'DATABASE:',database)

    
    
    con.close()
        


def pull_database( database,table_name=None):
    '''
    simplify returning a database...
    if table_name is None it will return list of tables
    '''
    eng = sql.create_engine('postgresql://postgres:password@localhost/{}'.format(database))
    # List tables 
    con      = eng.connect()
    tables   = eng.table_names()
    table_df = pd.DataFrame(tables,columns=['tables'])
    #print(table_df)
    if table_name == None:
        con.close()
        return table_df
    else:
        if table_name in tables:
            #Load Data From The Base
            a=pd.read_sql_query('select * from "{}"'.format(table_name),con=eng)
            return a 

'''
-----------------------------------------PRICE SCRAPE--------------------------------------------------------
'''

from urllib.request import urlopen
import json
import os
import pandas as pd
import stealing.config
import pandas_datareader as pdr 
from Historic_Crypto import HistoricalData


def get_crypto(ticker,time_frame,start_date = '2020-03-01-00-00'):
    coin = ticker + '-USD'
    print(coin)
    #timeframes
    if time_frame == '1d':
        seconds = 86400
    if time_frame == '1hr':
        seconds = 3600
    if time_frame == '15min':
        seconds = 900

    df = HistoricalData(coin,granularity=seconds ,start_date=start_date).retrieve_data()
    return df


def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)


def dnld_daily(ticker):
    '''
    This downloads free daily data by scraping yahoo finace
    '''
    print('getting daily')
    df = pdr.get_data_yahoo(ticker)
    [df.rename(columns={col:col.lower()},inplace=True) for col in df.columns]
    os.system('figlet {}'.format(ticker))
    #print(df)
    return df

def get_some(ticker,time_frame='1hr'):
    '''
    time_frame(s): str
        a) 15min
        b) 1hr
        c) 1d
    '''
    #standardize time frame 
    time_frame = time_frame.lower()
    ticker     = ticker.upper()
    cryptos = ['EGLD','BTC','ORN','ETH','CEL']
    if ticker in cryptos:
        print('[[[[[[[[[[[[[[[[[[[[[[[[CRYPTO {}]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]'.format(ticker))
        df = get_crypto(ticker,time_frame,start_date = '2020-03-01-00-00')
        
    #download daily data --- it has to parsed diffrently b/c you are recievie data in a dictionary
    elif time_frame == '1d':
        
        dtype = 'historical-price-full'
        #ticker= 'TSLA'

        # set endpoint & get json
        url  = (f"https://financialmodelingprep.com/api/v3/{dtype}/{ticker}?apikey={config.fin_mod_api}")
        data = get_jsonparsed_data(url)

        df   = pd.DataFrame(data['historical']).sort_values('date').set_index('date')
        df

    
    else:
        # download hourly data
        if time_frame == '1hr':
            dtype = 'historical-chart/1hour'

        # down load 15minute data
        if time_frame == '15min':
            dtype = 'historical-chart/15min'

        url  = (f"https://financialmodelingprep.com/api/v3/{dtype}/{ticker}?apikey={config.fin_mod_api}")
        data = get_jsonparsed_data(url)

        df = pd.DataFrame(data)
        if 'date' in df.columns:
            df = df.set_index('date')
            # is this fixed?------this may still eror out so shift this under the if statment
            df.index = pd.to_datetime(df.index)

            df = df.sort_values('date')
    return df 





def price(ticker,time_frame,plot=False):
    '''
    downloads and saves stock data to database
    Takes:
        1. TICKER : str
        2. TIME_FRAME : str
            a) 15min
            b) 1hr
            c) 1d
    '''

    df = get_some(ticker,time_frame)

    table_name = ticker + '_' +time_frame
    odf=pd.read_sql_query('select * from "{}"'.format(table_name),con=eng).set_index('date')
    
    df.to_sql(table_name,con,if_exists = 'append', index = True)
    print('DOWNLOADED:',ticker,' :',time_frame)
    
    if plot == True:
        jenay(df)
    return df


def price_updater(ticker):
    '''
     ::: daily maintenince to update database :::
    '''
    # Download Fifteen Minute
    dtype  = '15min'
    df = get_some(ticker,dtype)

    table_name = ticker + '_' +dtype

    df.to_sql(table_name,con,if_exists = 'append', index = True)
    print('DOWNLOADED:',ticker,' :',dtype)
    df
    time.sleep(2)

    # Download One Hour
    dtype  = '1hr'
    df = get_some(ticker,dtype)

    table_name = ticker + '_' +dtype

    df.to_sql(table_name,con,if_exists = 'append', index = True)
    print('DOWNLOADED:',ticker,' :',dtype)
    df    
    time.sleep(2)
    
    # Daily Data
    dtype = '1d'
    df = get_some(ticker,dtype)
    
    table_name = ticker + '_' + dtype
    
    # save to db
    df.to_sql(table_name,con,if_exists = 'append', index = True)
    print('DOWNLOADED:',ticker,' :',dtype)
    





'''
------------------------------------------TWITTER ZONE ---------------------------------------------------------------------------------
'''


import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate',150)
def say(words):
    engine.say(words)
    engine.runAndWait()


def merge_tweets_with_price(ticker,plot=True):
    '''
    this takes the index from mention grid(df) and merges
    it with price data and plots it. 
    TAKES:
        1. ticker_col from grid_df
        2. mixes it with whatever datetime frame df is ...( also global ) 
        3. plot the mentions
    '''
    df['twitter_mentions'] = 0
    # get a list of times ticker was tweeted
    mention_dates = grid[grid[ticker]>0][ticker].index

    for m in trange(len(mention_dates)):
        try:
            # grab first row  from isolated data after event 
            first_data = df[df.index>mention_dates[m]].iloc[0].name
            # either grab the in dex or insert cell directly 
            df['twitter_mentions'][first_data] = 1
        except IndexError:
            pass

    if plot == True:
        jenay(df,scale_two='twitter_mentions',title=('TwitterMentions: '+ticker))

def first_mentions(grid):
    '''
    Cross refrences twitter database with fresh tweets coming in to identify anything new
        - archives the first date new data was loged 
        - as well as the datetime of tweet 
        - 
    '''


    # pull old data
    table_name = 'mention_index'
    try:
        idf = pull_database('twitter',table_name).set_index('ticker')
        index_list = idf.index
    except:
        index_list = []
    # frame the grid
    gdf = pd.DataFrame(grid.sum(),columns=['mentions'])
    gdf = gdf[gdf['mentions']>0]
    df  = grid[gdf.index]
    df  = df.sort_values(df.index.name)
    #get first dates
    
    li = []
    for col in df.columns:
        di = {}
        di['ticker']          = col
        di['first_mentioned'] = df[df[col]>0].index[0]
        di['discovered']      = datetime.now()
        li.append(di)
        print(di)
    fmdf = pd.DataFrame(li).set_index('ticker')
    print(fmdf)
    unlisted = [t for t in fmdf.index if t not in index_list ]
    if len(unlisted) > 0:
        for i in unlisted:
            message = 'new ticker mentioned {}'.format(i)
            say(message)
            print(message)
        # isolate unseen tickers
        fmdf = fmdf.T[unlisted].T
        #append database
        save_database(fmdf,table_name,save_index=True,merge_with_old=False)
    else:
        print('no new tickers')
        say('no new tickers')




# Imports
import tweepy
import pandas as pd
import time

## Credentials and Authorization
from stealing.config import consumer_key
from stealing.config import consumer_secret
from stealing.config import access_token
from stealing.config import access_token_secret


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)

tweets = []

def username_tweets_to_csv(username,count):
    try:      
        # Creation of query method using parameters
        tweets = tweepy.Cursor(api.user_timeline,id=username).items(count)

        # Pulling information from tweets iterable object
        tweets_list = [[tweet.created_at, tweet.id, tweet.text] for tweet in tweets]

        # Creation of dataframe from tweets list
        # Add or remove columns as you remove tweet information
        tweets_df = pd.DataFrame(tweets_list,columns=['Datetime', 'Tweet Id', 'Text'])

        # Converting dataframe to CSV 
        import os
        tpath='fresh_data/'
        if not os.path.exists(tpath):
        	os.mkdir(tpath)
        
        #ARCHIVE HERE!
        tweets_df = tweets_df.set_index('Datetime')
        # subtract 4 hours from GMT to be EST: best time ever!
        tweets_df.index = tweets_df.index - pd.Timedelta(hours=4)

        sheet = (tpath+'{}-tweets.csv'.format(username))
        
        tweets_df.to_csv(sheet)
        
    except BaseException as e:#except BaseException as e:
          print('failed on_status,',str(e))
          time.sleep(3)



def extract_tickers(s):
    '''
    give me tweets i spit out a list of words with NO DIGITS that had
    hash tag "$" in the word
    '''
    punc = '''!()-[]{};:'"\, <>./?@#$%^&*_~'''
    #s = df['Text'][5]
    #print(s)
    # grab Dollars
    s = [w for w in s.split(' ') if '$' in w]
    #print(s)
    goodli = []
    for w in s:
        w = w.replace('\n','').upper()#.replace('(','')
        for c in w:
            if c in punc:
                w = w.replace(c,'')
                #print('removing-------------',c)
        result = ''.join([i for i in w if not i.isdigit()])
        #print('RESULT:',result, 'WORD:',w)
        
        
        if (len(w) == len(result)) & (len(w)>0):
            #print('====GOOD====',w)
            
            goodli.append(re.sub(r'\d+', '', w.replace('$','')))
        else:
            #print('====NAH====',w)
            pass
    #print(goodli)
    return goodli



def twit_grid(df,username):
    '''
    turns "hash" column ( list of tickers ) into a datetime grid (dataframe)
    '''


    for i in trange(len(df)):
        ticli = df['hash'][i]

        for tic in ticli:
            tic = tic.upper()
            if tic not in df.columns:
                df[tic] = 0
            else:
                df[tic][i] = 1


    # eliminate rows that dont contain ticker symbols
    df = df[df['hash'].apply(len)>0]

    boring = ['Tweet Id','Text','hash','tic_count']
    #hl(df)

    sola(df.drop(boring,axis=1).rolling(12).sum(),title='Rolling Twelve')

    # Grid
    df = df.drop(boring,axis=1)

    # Now Create Data Tables For Grid
    eng = sql.create_engine('postgresql://postgres:password@localhost/twitter')
    
    # List tables 
    con = eng.connect()
    table_name = username + '_grid'
    tables = eng.table_names()
    print(tables)
    print(table_name)

    if table_name in tables:
        #Load Data From The Base
        a=pd.read_sql_query('select * from "{}"'.format(table_name),con=eng).set_index('Datetime')

        # Add Columns If Not In Database
        left_overs = set(df.columns) - set(a.columns)
        left_overs = [col for col in left_overs if len(col)> 0]
        print('columns in Database:',len(left_overs),left_overs)
        if len(left_overs) > 0:
            for col in left_overs:
                
                con.execute('ALTER TABLE {} ADD COLUMN "{}" TEXT NULL;'.format(table_name,col))

    # Save Data To Base
    df.to_sql(table_name,con,if_exists = 'append', index = True)

    con.close()
    return df

def twitter(username,count):
    '''
    UPDATES A DATABASE WITH TWEETS:
    RETURNS:
        1) tweet_df 
        2) grid_df
        

    '''
    table_name = username.replace('@','')

    # Established Database Connection
    eng = sql.create_engine('postgresql://postgres:password@localhost/twitter')
    con = eng.connect()
    # Table Names
    print()
    tables = eng.table_names()
    if table_name in tables:
        a=pd.read_sql_query('select * from "{}"'.format(username),con=eng).set_index('Datetime')
        ## TODO: ADD THE UNIQUE ROWS SCRIPT HERE!!

    # Next Up: Insert Scrape Function
    #from Scrape import username_tweets_to_csv


    # SCRAPING USERNAME
    username_tweets_to_csv(username, count)

    # Load Data
    df = pd.read_csv('fresh_data/'+username+'-tweets.csv').set_index('Datetime')

    df['hash'] = df['Text'].apply(extract_tickers)
    df

    #df = df[df['hash'].apply(len)>0]

    df['tic_count']  = df['hash'].apply(len)
    # List tables 


    # Save Data To Base
    df.to_sql(table_name,con,if_exists = 'append', index = True)

    # Table Names
    print(eng.table_names())


    #Load Data From The Base
    #a=pd.read_sql_query('select * from "PW_15min"',con=eng)



    con.close()
    print('IT WORKED')
    
    # if returned tweets dont have any ticker symbols dont try to make a grid 
    #try:
    grid = twit_grid(df,username)
    #except:
    #    grid = None
        
    return df,grid



tweets = []

def text_query_to_csv(text_query,count):

    '''
    SCRAPE TWITTER BASED ON TEXT / HASH TAG
    '''

    #try:
    # Creation of query method using parameters
    tweets = tweepy.Cursor(api.search,q=text_query).items(count)

    # Pulling information from tweets iterable object
    tweets_list = [[tweet.created_at, tweet.id, tweet.text,tweet.retweet_count,tweet.favorited,tweet.author.followers,tweet.user] for tweet in tweets]

    # Creation of dataframe from tweets list
    # Add or remove columns as you remove tweet information
    tweets_df = pd.DataFrame(tweets_list,columns=['Datetime', 'Tweet Id', 'Text','retweet_count','favorited','followers','user'])

    # Converting dataframe to CSV 
    tweets_df.to_csv('{}-tweets.csv'.format(text_query), sep=',', index = False)
    return tweets_df



def twitter_hashtag(text,count,plot=True):
    '''
    returns rates of tweets and retweet rates. 
    saves an archive of that ino
    the actual tweet dataframe is saved in the retweet_df column. ( if its not being retweeted its not worth it)
    returns the info df
    '''
    # tweepy function
    df = text_query_to_csv(text,count)

    # Fix  Index and Run Calculations

    df = df.set_index('Datetime')
    df.index = df.index - pd.Timedelta(hours=4)

    # aggrigating usefull data to archive for backtest's
    tweet_retweeted = len(df[df['retweet_count']>0])
    retweet_df      = df[df['retweet_count']>0]
    fav_len         = len(df[df['favorited']==True])
    retweet_sum = retweet_df['retweet_count'].sum()
    fav_len         = len(df[df['favorited']==True])
    start_time      = df.index[0]
    last_time       = df.index[-1]
    time_delta      = start_time - last_time
    rate_multiple   = pd.Timedelta(hours=1)/time_delta
    tweets_per_hour = 400 * rate_multiple


    # Save To a Dictionary

    di = {}
    di['fav_len']        = fav_len
    di['start_time']     = start_time
    di['last_time']      = last_time
    di['time_delta']     = time_delta
    di['rate_multiple']  = rate_multiple
    di['tweets_per_hour']= tweets_per_hour
    di['tweet_retweeted'] = tweet_retweeted
    di['retweet_df']      = retweet_df
    di['fav_len']         = fav_len
    di['retweet_sum']     = retweet_sum
    # tweet info df
    tidf = pd.DataFrame([di])
    tidf['tweets_per_second'] = (tidf['tweets_per_hour']/60)/60
    tidf

    text
    
    # append archive or create it if not exists
    apath = text+'_tweetArchive.csv'
    if not os.path.exists(apath):
        tidf.to_csv(apath,index=False)
        print('doesnt exist: createing sheet')
    else:
        oldf = pd.read_csv(apath)
        ndf  = oldf.append(tidf)
        ndf.to_csv(apath,index=False)
        print('it exists: appending it')



    print('tweets_per_hour:',tweets_per_hour)

    # Data Log
    ndf

    #making the index the last recorded data
    ndf = ndf.set_index('last_time')
    ndf

    # Plots


    if plot == True:
        ###from finding_fire import sola,sobar

        sola(ndf[['rate_multiple','tweet_retweeted']],title='Retweets And RateMultiple')

        sola(ndf['tweets_per_hour'],title='Tweets Per Hour')
        
    return ndf

###--------------------------------------------------------------------------------------------------
# XXX MOVE TO FINDING XXX
#SMAC - CON VAL FUNTION
def smac_with_confirmation(df,validation,fast,slow,want_plot=False,standard_names=False):
    '''
    This function uses a fast Moving acg above a slow one 
    as a condition to buy confirmation:
        ( when price is above a really fast avg ex: 5 )
    
    TAKES:
    1. df : pandas.DataFrame
    2. validation - the fastest movingAvg - when price is above this 
        it will trigger BUT if fast_Ma > slow_ma
    3. fast - Your fast moving avg 
    4. slow - slow moving avg
    5. want_plot - Bool True if you want to plot
    6. standard_names - BOol - if this is true it will will not iclude
        the value names in the columns
        INSTEAD OF:
            'ma:6','ma:10','ma:20'
        YOU GET:
            'val', 'fast', 'slow'
    
    OUTPUT:
    1. df    pd.DataFrame with columns
    2. columns: 'buy', 'sell' - to either send to a backtest or apply 
        add conditions
    3. scaled 'buy' , 'sell'
    '''
    fastn      = 'ma:'+str(fast)
    slown      = 'ma:'+str(slow)
    valn       = 'ma_val:'+str(validation)
    df[fastn]  = df['close'].rolling(fast).mean()
    df[slown]  = df['close'].rolling(slow).mean()
    df[valn]   = df['close'].rolling(validation).mean()
    
    df[valn]   = df[valn].shift()
    
    if want_plot:
        df[[valn,slown,'close',fastn]].iplot(theme='solar',fill=True)

    df['fast_above']      = df[fastn]>df[slown]
    df['price_above_val'] =df['close']>df[valn]
    df['conditions_met']  = (df['fast_above']==True)&(df['price_above_val']==True)
    #..................................................................................................
    
    df['buy'] = (df['conditions_met']==True) & (df['conditions_met'].shift()==False)
    df['sell']= (df['conditions_met']==False)& (df['conditions_met'].shift()==True)
    
    #scales the signals for plotting
    df['buyscale'] = df['buy'].replace(True,1).replace(1,df.close)
    df['sellscale']= df['sell'].replace(True,1).replace(1,df.close)
    
    #plots with buy and sell triggers
    if want_plot:
        df[[valn,slown,'close',fastn,'sellscale','buyscale']].iplot(theme='solar',fill=True)

    #scales the signals for plotting
    df['buyscale'] = df['buy'].replace(True,1).replace(1,df.close)
    df['sellscale']= df['sell'].replace(True,1).replace(1,df.close)
    df.buyscale = df['buyscale'].replace(0,np.nan)
    df.sellscale= df['sellscale'].replace(0,np.nan)
    
    #give standard names 
    if standard_names:
        df = df.rename(columns={valn:'val',
                               fastn:'fast',
                               slown:'slow'})
    

    return df


# OUTDATED?
#FUNCTION
def compile_signals(df,buy='buy',sell='sell'):
    '''
    TAKES:
    1. pandas dataframe
    2. buy column
    3. sell column
    >Takes a df and columns that trigger a buy and sell: defualt:'buy'&'sell'
    compiles that into a column named ='trac' 
        - trac becomes true when you get a buy signal
          and stays true until you get a sell signal
            ( so you can tell if you are in a trade or not)
    
    >then compiles that and retuns it with buy and sell signals in one column
    for fastuants backtest
    
    >fastquant custom backtest takes on column with
    buy = 1
    sell = -1
    else = 0
    '''

    
    # MAKE TRADE TRACKING COLUMN (trac)
    df['trac'] = False

    for i in trange(1,len(df)):
        if df[buy][i] == True:
            df['trac'][i] = True
        elif df[sell][i]==True:
            df['trac'][i]=False
        else:
            df['trac'][i]=df['trac'][i-1]

    #MAKE FASTQUANT SIGNAL COLUMN!!!
    df['signal'] = 0
    for i in trange(1,len(df)):
        if (df['trac'][i]==True) & ( df['trac'][i-1]==False):
            df['signal'][i]=1
        elif (df['trac'][i]==False) & ( df['trac'][i-1]==True):
            df['signal'][i]=-1
    df['tracscale'] = df['trac'].replace(True,1).replace(1,df.close)
    return df

        
def hl(df):
    def highlight(boo):
        criteria = boo ==True
        return['background-color: green'if i else '' for i in criteria]
    df = df.style.apply(highlight)
    return df

#DAMN USEFULL
def load_data(path,all_columns=False):
    df = pd.read_csv(path)
    [df.rename(columns={col:col.lower()},inplace = True) for col in df.columns]
    if 'time' in df.columns:
        df = df.set_index('time')
        df.index = pd.to_datetime(df.index,unit='s')
    else:
        df = df.set_index('date')
        df.index = pd.to_datetime(df.index)
    df
    col_list = ['open','close','low','high']
    if 'volume' in df.columns:
        col_list.append('volume')
    
    #only condence if true
    if all_columns==False:
        df = df[col_list]
    return df

# BRING IT BACK (but also ) XXX MOVE TO FINDING XXX

def my_backtest(df,custom_column='trac',plot_capital=False,return_df=False,strat_name='PUT STRATEGY HERE'):
    '''
    Takes a pandas.DataFrame with a boolean column called:
    1. trade tracking colum  : str
        default : "trac"
    2. plot_capital: bool do you want to plot capital with 
        default : False
    3. return_df: bool
        default : False
    RERUTNS,  
            1. the results dataframe with backtest shit metrics...
        OPTIONAL: 
            2. capital plot
            3. df
            4.strat name : strat_name='PUT STRATEGY HERE'
    '''
    
    df['entry'] = 0.0
    df['pnl']   = 0.0
    for i in trange(1,len(df)):
        if (df['trac'][i]==True)&(df['trac'][i-1]==False):
            df['entry'][i] = df['close'][i]
        else:
            df['entry'][i] = df['entry'][i-1]


        if (df['trac'][i]==False)&(df['trac'][i-1]==True):
            df['pnl'][i] = df['close'][i]-df['entry'][i]


    df['pnl'].sum()

    df['pnl_pct'] = 0
    df['acnt'] = 1000
    df['scaled_acnt'] = df['close'][0]
    #what is this? the same?
    
    for i in trange(1,len(df)):
        if df['signal'][i]!=0:
            df['pnl_pct'][i] =(df['pnl'][i]/df['entry'][i])
            #df['acnt'][i] = (df['pnl_pct'][i]*df['acnt'][i-1])+df['acnt'][i-1]
    
    df['pnl_pct'] = df['pnl']/df['entry']
    df = df.fillna(0)
    for i in trange(1,len(df)):
        if df['pnl_pct'][i] != 0:
            delta         = df['pnl_pct'][i]*df['acnt'][i-1]
            #print(delta)
            df['acnt'][i] = df['acnt'][i-1]+(df['pnl_pct'][i]*df['acnt'][i-1])
            df['scaled_acnt'][i] = df['scaled_acnt'][i-1]+(df['pnl_pct'][i]*df['scaled_acnt'][i-1])
        else:
            df['acnt'][i] = df['acnt'][i-1]
            df['scaled_acnt'][i] = df['scaled_acnt'][i-1]
            
    df['win_cnt'] = df['pnl_pct']>0
    df['los_cnt'] = df['pnl_pct']<0
    
        
    win_cnt = df['win_cnt'].sum()
    los_cnt = df['los_cnt'].sum()
    total   = win_cnt+los_cnt
    win_pct = (win_cnt/total)
    final_pnl= (df['acnt'][-1]-1000)/1000*100


    print('final_acnt value:',df['acnt'][-1])
    print('total_+trades:',total)
    print('wins        :',win_cnt)
    print('loss        :',los_cnt)
    print('win_percent :',(win_pct))
    print('final_pnl   :',final_pnl,'%')

    d = {}
    li =[]
    
    d['strat_name']        = strat_name
    d['final_acnt value']  = df['acnt'][-1]
    d['total_trades']      = total
    d['wins']              = win_cnt
    d['loss']              = los_cnt
    d['win_percent']       = win_pct*100
    d['final_pnl']         = final_pnl

    li.append(d)


    # PLOT IF SPECIFIED
    if plot_capital == True:
        #df['acnt'].iplot(theme='solar',fill=True)
        df[['high','low' ,'scaled_acnt', ]].iplot(theme='solar',fill=True)


    result = pd.DataFrame(li)
    #OUPUT -  default: results data , unless you want the df bvak for ploting, and combining strats
    output = result
    if return_df ==True:
        output = result,df
    
    return output


def plot_grid(path):
    
    df = pd.read_csv(path,index_col='Unnamed: 0')
    sns.heatmap(df)



# THIS HAS BEEN REPLACE : std_targets
#ATR TARG - STOP GENERATOR - EXITS
def atr_exits(df,dn_mul=1,up_mul=2,buy_trigger='buy'):
    '''
    standar
    
    '''
    df['atr'] = pta.atr(df.high,df.low,df.close)
    df['atr_up'] = df['close'] +(df['atr']*up_mul)
    df['atr_dn'] = df['close'] -(df['atr']*up_mul)
    
    
    #BUY COLUMN TRIGGERS NEW TARGET AND STOPS TO BE CREATED
    #create placeholders
    df['atr_targ'] = df['atr_up']
    df['atr_stop'] = df['atr_dn']
    #identify
    for i in range(1,len(df)):
        if df[buy_trigger][i]>0:
            df['atr_targ'][i]=df.atr_up[i]
            df['atr_stop'][i]=df.atr_dn[i]
        else:
            df['atr_targ'][i]=df.atr_targ[i-1]
            df['atr_stop'][i]=df.atr_stop[i-1]
    
    #
    
    #create exit triggers
    df['stop_hit'] =( df['close'].shift()>df.atr_stop ) & (df['close']<df.atr_stop)  
    df['targ_hit'] =( df['close'].shift()<df.atr_targ ) & (df['close']>df.atr_targ)
    df['atr_sell'] = (df['stop_hit']==True) | (df['targ_hit']==True)
    return df


# XXX TRASH XXX 
def plot_targets(df,title='ATR TARGETS'):
    '''
    takes:
        pandas DataFrame with columns: 
            trac
            atr_targ
            atr_stop
            scaled acnt 
                ( plot_acnt has to be true in compile_signals function)
                 (and return_df has to be true in compile_signals)
    returns:
        cufflinks plot of targets when buy was triggered, 
        with 
        '''
    # drops atr when not in a trade for clean plotting
    for i in range(1,len(df)):
        if df['trac'][i-1] == 0:
            df['atr_targ'][i]= np.nan
            df['atr_stop'][i]= np.nan
    df[['atr_stop','close','atr_targ','scaled_acnt']].iplot(theme='solar',title=title,fill=True)




# XXX TRASH XXX 
#ARCHIVE FUNCTION
def archive_data(path,sheet,df):
    '''
    CREATING AND UPDATEING AN ARCHIVE FUNCTION:
    df MUST have a datetimeindex
    TODO: test it!
   
   TAKES: 
    1. path = str: the directory you want to save in (this'll create it if it isnt real yet)
    2. sheet= str: whatever your archive is named, or what you would like to name it
    3. df   = pd.DataFrame: if the archive has not been concived yet this will be the first data in it

    '''
    #standardize the index's ... indi indices ??? indy
    df.index.name = 'Datetime'
    #sort it
    df['index_copy'] = df.index
    df = df.sort_values('index_copy')
    df = df.drop('index_copy',axis=1)

    # SAVING - create dirs if they dont exists

    if not os.path.exists(path):
        os.mkdir(path)
    # if the archive doesnt exist this creates it
    if not os.path.exists(path+sheet):
        df.to_csv(path+sheet)

    df

    #load up old data - drop overlapping rows and update
    oldf = pd.read_csv(path+sheet).set_index('Datetime')
    oldf.index = pd.to_datetime(oldf.index)
    #most recent date
    last_date = oldf.index[-1]

    #set mask
    print('Last todolist in archive is from:',last_date)
    #filter
    newdf = df[df.index>last_date]

    if len(newdf)>0:
        #filtered new data
        print('Most recent backtest is from:',newdf.index[-1])
        oldf = oldf.append(newdf)
        print('the archive has been updated [o_0]')
        oldf.to_csv(path+sheet)
        print(oldf)
    else:
        print('--there are no new recent data to append--')



def save_stuff(path,strat_name,batch_time,rdf,df,info,time_delta):
    '''
    TAKES:
        1.path - from the original sheet
        2.strat_name - str
        3.batch_time - the datetime the batch started
        4.rdf        - results dataframe ( all the loops mixed together)
        5. df - the orgiginal stock data
        6. info - the backtestresults df best preforming row ( which becomes used as a column in the info archive)
        7. time_delta - datetime diffrence of how long it took to run the notebook
    RETURNS:
        info dataframe
    '''

    #ESTABLISH NAMES
    save_name = path.split('.')[0].split('/')[-1].replace(' ','_')
    save_path = save_name + '/'
    grid_path = save_path+'grids/'
    info_path = save_path+'info.csv'
    all_path  = 'Aggrigate/'
    #the name of the current gridplot
    grid_name = strat_name.replace(' ','_')+str(batch_time).split('.')[0].replace(' ','_').replace('2020-','20')+'.csv'

    #METRICS 
    best_pnl = str(int(rdf['final_pnl'].iloc[0]))+'%'
    #establish baseline pnl - buy and hold
    buynhold = ((df['close'][-1]- df['close'][0])/df['close'][0])*100

    #saving the info
    info['save_name'] = save_name
    info['grid_name '] = grid_name
    info['best_pnl  '] = best_pnl
    info['buyholdpnl'] = buynhold
    info['batch_time'] = batch_time
    info['time_delta'] = time_delta
    #li.append(info)
    #info = pd.DataFrame(li).set_index('batch_time')
    #info=info.T
    #info.index.name = 'batch_time'
    info



    #create directorys if they dont exist
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    if not os.path.exists(grid_path):
        os.mkdir(grid_path)
    #SAVE INFO - if sheet doent exists

    #................................................................................................................................................

    #SAVING RESULTS:
    # 

    #archive_data(path=save_path,sheet=save_name,df=info)
    #rdf = rdf.set_index('batch_time')
    archive_data(path=save_path,sheet='results.csv',df=rdf)
    archive_data(path='Aggrigate/',sheet='results.csv',df=rdf)

    #CREATE DIRECTORYS- SAVE INFO FRAME IF IT DOES NOTE EXITST
    path='Aggrigate/'
    iname='info.csv'
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.exists(path+iname):
        info.to_csv(path+iname)
    else:
        idf = pd.read_csv('Aggrigate/info.csv').set_index('Datetime')
        idf[info.T.columns[0]]= info.T
        idf.to_csv('Aggrigate/info.csv')


    if not os.path.exists(save_path+iname):
        info.to_csv(save_path+iname)
    else:
        idf = pd.read_csv(save_path+'info.csv').set_index('Unnamed: 0')
        idf[info.T.columns[0]]= info.T
        idf.to_csv(save_path+'info.csv')
    return rdf



def sma_up_validation(df,sma_variable,long_sma,strat_name,look_back,rdf,plot_capital=False):
    '''
    takes:
        1.df
        2.sma - float, when price is above this sma it will by ...
        3.long_sma - float, will only buy if this is pointing up
        4. results dataframe to append results to 
    returns:
        final_acnt value for grid plot
    '''
    df = df[['close','low','open','high']]
    
    df['longer_sma']   = df['close'].rolling(long_sma).mean().shift()
    df['moving_avg']   = df['low'].rolling(sma_variable).mean().shift()
    df['price_abv_ma'] = df['close']>df['moving_avg']
    df['buy_sma']      = (df['price_abv_ma']==True)&(df['price_abv_ma'].shift()==False)
    df['sell']         = (df['price_abv_ma']==False)&(df['price_abv_ma'].shift()==True)
    df['longer_up']    = (df['longer_sma']>df['longer_sma'].shift(look_back))
    df['buy']          = (df['buy_sma']==True) & (df['longer_up']==True) 
    #.....................................................................................................
    
    df = compile_signals(df)
    result = my_backtest(df,strat_name='SMA-Price-CROSS',plot_capital=plot_capital) 
    #print(result)
    result['validation'] = sma_variable
    result['sma_has_to_be_up'] = long_sma
    rdf = rdf.append(result)
    result['look_back'] = look_back
    return result['final_acnt value'][0],result

def sola(df,title=None):
    return df.iplot(theme='solar',fill=True,title=title)



def scale_close(column):
    col_name   = column+'scale'
    df[col_name] = df[column].replace(True,1).replace(1,df.close)
    return df

def make_sma_targets(df,fast,slow):
    df['fast'] = df['close'].rolling(fast).mean()
    df['slow'] = df['close'].rolling(slow).mean()
    df['fast_below'] = df['slow']>df['fast']
    #...............................................................................................
    df['was_ab_now_bl']=(df['fast_below'].shift()==False)&(df['fast_below']==True)
    df['was_bl_now_ab']=(df['fast_below'].shift()==True)&(df['fast_below']==False)
    df['abovescale']   = df['was_ab_now_bl'].replace(True,1).replace(1,df.close)
    df['belowscale']   = df['was_bl_now_ab'].replace(True,1).replace(1,df.close)
    #FAST IS GOIN UP
    df['fast_rising']  = (df['fast']>df['fast'].shift()) & (df['fast'].shift()<df['fast'].shift(2))
    return df

def delta_maker(df,THRESH,deal_breaker = 'delta_ab_thresh'):
    #DELTA ABOVE THRESH
    #THRESH = 2
    
    # THE DIFFERENCE FROM FASTSMA AND ITS LAST PERIOD - AS A PERCENT X 1000
    df['fast_delta']   = ((df['fast'] - df['fast'].shift())/df['fast'].shift())*1000
    df['delta_ab_thresh']= df['fast_delta']>THRESH
    df['delta_bl_thresh']= df['fast_delta']<THRESH
    #deal breaker means its gone up by some messure and lost its apeal
    #really its porlly gonna be a buy signal most the time
    
    df['waiting'] = False
    for i in range(1,len(df)):
        if df['was_ab_now_bl'][i]==True:
            df['waiting'][i] = True
        elif df[deal_breaker][i-1] == True:
            df['waiting'][i]==False
        else:
            df['waiting'][i]=df['waiting'][i-1]
    return df

def checkpoint(df,check_without_asking=False,title=''):
    '''
    this script saves any dateframe in the directory: checkpoints
    TAKES:
        1.dataframe- save
        2.save_without_asking : bool - copy when ever called    
        3.titls   : str  - optional title
    RETURNS: - nothing    
        1.CREATES DIRECTORY:
            "checkpoints"
        2.SAVES DATAFRAME
            - with the time check point was made
        
    '''
    
    if check_without_asking == True:
        yn = 'y'
    else:
        yn = str(input('do you want to save a checkpoint?:'))
    #save reults or what evetever data frame
    if yn.lower() == 'y':
        checkpath = 'checkpoints/'
        if not os.path.exists(checkpath):
            os.mkdir(checkpath)
        checkpoint = title+checkpath+(str(datetime.now()).split('.')[0].split(' ')[1])+'checkpoint.csv'
        df.to_csv(checkpoint)
        print('cool saved it! [0_0] ')
#..............................................................................................




def buy_delta(df,THRESH,SELL,condition,plot=False):
    
    
    df  = delta_maker(df,THRESH)

    BUY = 'delta_ab_thresh'
    df['buy'] = (df[BUY].shift()==False) & ( df[BUY]==True) & (df[condition]==True)
    df['sell'] = (df[SELL].shift()==False) & ( df[SELL]==True)
    df = compile_signals(df)
    result = my_backtest(df,
                       plot_capital=plot,
                       strat_name='delta_experiments'
                      )

    result['delta_thresh'] = THRESH
    return result





def all_delta_and_what_not(df,fast,slow,THRESH):
    '''
    TAKES:
        1.df
        2.fastma variable
        3.slowma variable
        4.DELTA THRESH
        5.sell
    '''
    df    = df[['open','low','high','close']]
    df    = make_sma_targets(df,fast,slow)
    sell   = 'was_ab_now_bl'
    result = buy_delta(df,THRESH,SELL)
    result['fast'] = fast
    result['slow'] = slow
    result['delta_thresh'] = THRESH
    return result



def scale_close(column,df):
    col_name   = column+'scale'
    df[col_name] = df[column].replace(True,1).replace(1,df.close)
    return df


def collect_stock_data(ticker):
    get_price_data(ticker,'15min')
    get_price_data(ticker,'1hour')
    ddf = pdr.get_data_yahoo(ticker)
    ddf.to_csv('data/'+ticker+'daily.csv')



from datetime import datetime
def iteration_loop(strat_function,path,var1_name,var2_name,var_1s,var_2s):
    df = load_data(path)
    #ESTABLISH BATCH TIME AS ID
    batch_time = datetime.now()
    #placeholder df
    grid = np.zeros((len(var_1s),len(var_2s)))
    #set_index
    gdf  = pd.DataFrame(grid,columns=var_2s)
    gdf.index = var_1s
    gdf

    #placehold loop for all results
    results = []
    print('shape is:',grid.shape)
    for var_1 in var_1s:
        for var_2 in var_2s:
            #[[[[[[[[[[[[[[[[[[STAT FUNCTION]]]]]]]]]]]]]]]]]]]]]]] 
            result,strat_name = strat_function(df,var_1,var_2)


            #[[[[[[[[[[[[[[[[[[[[[[[[[[ENDS HERE]]]]]]]]]]]]]]]]]]]]]]]]]]


            #SAVE GRID
            final_pnl         = result['pnl'][0]
            result['final_pnl']= final_pnl
            gdf[var_2][var_1] = final_pnl
            print('final_pnl:',final_pnl)

            #ADD STUFF TO RESULTS
            result['batch_time'] = batch_time
            result['run_time']   = datetime.now()
            #result['run_time']     = datetime.now()
            results.append(result)


    #TIME TO RUN
    time_delta = datetime.now()-batch_time

    #ADD SOME BASIC INFO TO THE SHEET
    print('loop ran in:',time_delta)
    if 'pnl' in result.columns:
        result['final_pnl'] = result['pnl']
    rdf = pd.concat(results).sort_values('final_pnl')[::-1]
    rdf['save_name'] = path.replace('data/','').replace('.csv','').replace(' ','_')
    rdf['time_delta'] = time_delta
    rdf['buyholdpnl'] = ((df['close'][-1]- df['close'][0])/df['close'][0])*100
    rdf['sheet_path'] = path
    rdf['var_1'] = var1_name
    rdf['var_2'] = var2_name

    #print('final_pnl:',rdf.final_pnl[0])
    print()
    pd.DataFrame(rdf.iloc[0]).drop(['batch_time','run_time'],axis=0)

    # the goal is to find the center of this thing


    rdf.columns

    # CREATE DIRECTORYS

    #NAME PATH TO SAVE RESULTS
    master_out  = 'output/'
    if not os.path.exists(master_out):
        os.mkdir(master_out)
    output_path = master_out + path.replace('data/','').replace('.csv','/').replace(' ','_') 
    #CREATE DIRECTORY IF IT DOESNT EXIST
    if not os.path.exists(output_path):
        os.mkdir(output_path)
        print('created:',output_path)
    else:
        print('directory exists!',output_path)
    #CREATE A DIRECTORY TO SAVE GRID
    grid_path = output_path + 'grids/'
    if not os.path.exists(grid_path):
        os.mkdir(grid_path)
        print('created:',grid_path)
    else:
        print('directory exists!:',grid_path)


    #.............................................................................................

    #SAVE GRID





    # DESCRIBE VARIABLE RANGE
    var1_name =var1_name +str(var_1s).replace(' ','')
    var2_name =var2_name +str(var_2s).replace(' ','')
    #var3_name =var3_name +str(slow).replace(' ','')
    #CREATE GRID NAME
    grid_name=  grid_path+strat_name+var1_name+var2_name+'.csv'
    # SAVE GRID
    gdf.to_csv(grid_name)
    print('saved grid to:',grid_name)

    #if in a notebook plot the grid
    #import seaborn as sns
    #sns.heatmap(gdf)
    #gdf

    # SAVE RESULTS

    rdf = rdf.set_index('run_time')
    # establish results path name. 
    results_path = output_path + 'results.csv'
    print(results_path)

    # if path doesnt exists just save the reuslts
    if not os.path.exists(results_path):
        rdf.to_csv(results_path)
        print('results dataframe created:',results_path)
    else:
        print('results dataframe exists!',results_path)
        rdf
        #load old results
        old_results = pd.read_csv(results_path).set_index('run_time')
        #append old results
        results_mixed = old_results.append(rdf)
        #save combined results
        results_mixed.to_csv(results_path)
        print('updated:',results_path)

    # SAVE INFO

    #taking the best preforming strat for info archive
    info = pd.DataFrame(rdf.set_index('batch_time').iloc[0])
    info.index.name = 'batch_time'
    info = info.T
    info.index.name = 'batch_time'
    info

    info_path = output_path+'info.csv'
    if not os.path.exists(info_path):
        print('creating info sheet')
        info.to_csv(info_path)
    else:
        print('info sheet exists!',info_path)
        old_info = pd.read_csv(info_path).set_index('batch_time')
        old_info
        idf = info
        #idf.index.name = 'batch_time'
        idf

        mixed_info = old_info.append(idf)
        mixed_info.to_csv(info_path)
        print('info sheet updated!')

    ## LAST STEP IS TO APPEND THE ALL RESULTS

    ## save all results in Aggrigate! 

    output_path = 'Aggrigate/'
    #CREATE DIRECTORY IF DOESNT EXISTS
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    #rdf = rdf.set_index('run_time')
    # establish results path name. 
    results_path = output_path + 'results.csv'
    print(results_path)

    # if path doesnt exists just save the reuslts
    if not os.path.exists(results_path):
        rdf.to_csv(results_path)
        print('results dataframe created:',results_path)
    else:
        print('results dataframe exists!',results_path)
        rdf
        #load old results
        old_results = pd.read_csv(results_path).set_index('run_time')
        #append old results
        results_mixed = old_results.append(rdf)
        #save combined results
        results_mixed.to_csv(results_path)
        print('updated:',results_path)

    info_path = output_path+'info.csv'
    if not os.path.exists(info_path):
        print('creating info sheet')
        info.to_csv(info_path)

    else:
        print('info sheet exists!',info_path)
        old_info = pd.read_csv(info_path).set_index('batch_time')
        old_info

        idf = info.T
        idf.index.name = 'batch_time'
        idf

        mixed_info = old_info.append(idf)
        mixed_info.to_csv(info_path)
        print('info sheet updated!',info_path)


from fastquant import backtest

def macd_backtest(df,var1,var2,plot=False):
    '''
    var1 = fast_period - should be smaller than slow_upper
    var2 = slow_period - shoudl be larget than fast_upper
    '''
    
    result = backtest('macd',
                      df,
                     fast_period=var1,
                     slow_period=var2,
                      signal_period=14,
                      #allowance = 6,
                     init_cash=1000,
                     plot=plot)
    result['allowance']    = 6
    result['signal_period']=14
    strat_name = 'macd:'
    result['strat_name']   = strat_name
    
    return result,strat_name

def smac_backtest(df,var1,var2,plot=False):
    '''
    var1 = fast
    var2 = slow
    '''
    result = backtest('smac',
                     df,
                     fast_period=var1,
                     slow_period=var2,
                     init_cash  = 1000,
                     plot       = plot)
    strat_name = 'smac'
    result['strat_name'] = 'smac'
    return result,strat_name
    

def emac_backtest(df,var1,var2,plot=False):
    '''
    var1 = fast
    var2 = slow
    '''
    result = backtest('emac',
                     df,
                     fast_period=var1,
                     slow_period=var2,
                     init_cash  = 1000,
                     plot       = plot)
    strat_name = 'emac:'
    result['strat_name'] = 'emac:'
    return result,strat_name
    

def rsi_backtest(df,var1,var2,plot=False):
    '''
    var1 - rsi_lower
    var2 - rsi_upper
    '''
    result = backtest('rsi',
                      df,
                     rsi_lower=var1,
                     rsi_upper=var2,
                     init_cash=1000,
                     plot=plot)
    strat_name = 'rsi-14:'
    result['strat_name'] = strat_name
    
    return result,strat_name


#from fastquant import backtest

def macd_backtest(df,var1,var2,plot=False):
    '''
    var1 = fast_period - should be smaller than slow_upper
    var2 = slow_period - shoudl be larget than fast_upper
    '''
    
    result = backtest('macd',
                      df,
                     fast_period=var1,
                     slow_period=var2,
                      signal_period=14,
                      #allowance = 6,
                     init_cash=1000,
                     plot=plot)
    result['allowance']    = 6
    result['signal_period']=14
    strat_name = 'macd:'
    result['strat_name']   = strat_name
    
    return result,strat_name

def smac_backtest(df,var1,var2,plot=False):
    '''
    var1 = fast
    var2 = slow
    '''
    result = backtest('smac',
                     df,
                     fast_period=var1,
                     slow_period=var2,
                     init_cash  = 1000,
                     plot       = plot)
    strat_name = 'smac'
    result['strat_name'] = 'smac'
    return result,strat_name
    

def emac_backtest(df,var1,var2,plot=False):
    '''
    var1 = fast
    var2 = slow
    '''
    result = backtest('emac',
                     df,
                     fast_period=var1,
                     slow_period=var2,
                     init_cash  = 1000,
                     plot       = plot)
    strat_name = 'emac:'
    result['strat_name'] = 'emac:'
    return result,strat_name
    

def rsi_backtest(df,var1,var2,plot=False):
    '''
    var1 - rsi_lower
    var2 - rsi_upper
    '''
    result = backtest('rsi',
                      df,
                     rsi_lower=var1,
                     rsi_upper=var2,
                     init_cash=1000,
                     plot=plot)
    strat_name = 'rsi-14:'
    result['strat_name'] = strat_name
    
    return result,strat_name


BACKCURNNER = ''
import pandas_ta as pta

def after_burner(df,condition,oversold = 30,ma0 = 5,ma1 = 15,ma2 = 25,ma3 = 50,ma4 = 100,plot=False,plot_capital=False):
    '''
    takes:
        dataframe
        oversold condition
        condition - column in df thats true when in play
        moving avgs: when all the shorter ones are yup its considered abull run
    retuns:
        backtest results
    '''




    df['rsi'] = pta.rsi(df.close)
    df['ma0'] = df.close.rolling(ma0).mean().shift()
    df['ma1'] = df.close.rolling(ma1).mean().shift()
    df['ma2'] = df.close.rolling(ma2).mean().shift()
    df['ma3'] = df.close.rolling(ma3).mean().shift()
    df['ma4'] = df.close.rolling(ma4).mean().shift()

    

    df['bull_run'] = (df['ma0']>df['ma1']) & (df['ma1']>df['ma2']) &(df['ma2']>df['ma3']) &(df['ma3']>df['ma4']) #.............................
    df['reset']    = (df['ma4']>df['ma3']) & (df['ma4'].shift()<df['ma3'].shift())
    df['oversold'] = df['rsi']<oversold

    

    df['waiting'] = False
    for i in range(1,len(df)):
        if df['bull_run'][i] == True:
            df['waiting'][i]=True
        elif df['oversold'][i] == True:
            df['waiting'][i] = False
        else:
            df['waiting'][i] = df['waiting'][i-1]


    
    df['oversold_cnt'] = 0
    for i in range(1,len(df)):
        if (df['oversold'][i]==True) & (df['oversold'][i-1]==False):
            df['oversold_cnt'][i] = df['oversold_cnt'][i-1] + 1
        elif (df['reset'][i] == True):
            df['oversold_cnt'][i] = 0
        else:
            df['oversold_cnt'][i] = df['oversold_cnt'][i-1]


    df['first_time'] = (df['oversold_cnt']==1)
    
    
    
    if plot == True:
        df['first_time_scale'] = df['first_time'].replace(True,1).replace(1,df.close)
        df['bull_run_scale'] = df['bull_run'].replace(True,1).replace(1,df.close)
        df['reset_scale'] = df['reset'].replace(True,1).replace(1,df.close)
        df['oversold_scale'] = df['oversold'].replace(True,1).replace(1,df.close)
        df['waiting_scale'] = df['waiting'].replace(True,1).replace(1,df.close)
        sola(df[['ma0','ma1','ma2','ma3','ma4','close']])
        sola(df[['reset_scale','close','bull_run_scale','oversold_scale']])
        sola(df[['reset_scale','close','first_time_scale']])
        sola(df[['waiting_scale','close']])



    #hl(df)

    df['tranch1'] = (df['first_time'].shift()==False) & (df['first_time']==True)
    df['buy_first']  = (df['tranch1']==True) & ( df[condition]==True)
    #hl(df)

    # ok im going to do multiple sell tranches as well 

    df['validation'] = (df['close']<df['ma0']) & (df['close'].shift()>df['ma0'].shift())

    ## apply strat...

    #from backend import atr_exits,compile_signals


    #buy = 'first_time'
    buy = 'buy_first'
    sell= 'validation'
    strat_name = 'AFTER_BURNNER:first_tranche-validation '
    df  = compile_signals(df,buy,sell)
    print(strat_name)
    result = my_backtest(df,strat_name=strat_name,plot_capital=plot_capital)
    return result



candle_list = ['two_crow','three_black_crows','threeinside updown','threelinestrike','3outside','3starsinsouth','3WHITESOLDIERS','ABANDONEDBABY','ADVANCEBLOCK','BELTHOLD','BREAKAWAY','CLOSINGMARUBOZU','CONCEALBABYSWALL','COUNTERATTACK','DARKCLOUDCOVER','DOJI','DOJISTAR','DRAGONFLYDOJI','ENGULFING','EVENINGDOJISTAR','EVENINGSTAR','GAPSIDESIDEWHITE','GRAVESTONEDOJI','HAMMER','HANGINGMAN','HARAMI','HARAMICROSS','HIGHWAVE','HIKKAKE','HIKKAKEMOD','HOMINGPIGEON','IDENTICAL3CROWS','INNECK','INVERTEDHAMMER','KICKING','KICKINGBYLENGTH','LADDERBOTTOM','LONGLEGGEDDOJI','LONGLINE','MARUBOZU','MATCHINGLOW','MATHOLD','MORNINGDOJISTAR','MORNINGSTAR','ONNECK','PIERCING','RICKSHAWMAN','RISEFALL3METHODS','SEPARATINGLINES','SHOOTINGSTAR','SHORTLINE','SPINNINGTOP','STALLEDPATTERN','STICKSANDWICH','TAKURI','TASUKIGAP','THRUSTING','TRISTAR','UNIQUE3RIVER','UPSIDEGAP2CROWS','XSIDEGAP3METHODS']

import talib

def all_candels(df):
    df['two_crow'] = talib.CDL2CROWS(df.open,df.high,df.low,df.close)
    df['three_black_crows'] = talib.CDL3BLACKCROWS(df.open,df.high,df.low,df.close)
    df['threeinside updown'] = talib.CDL3INSIDE(df.open,df.high,df.low,df.close)
    df['threelinestrike'] = talib.CDL3LINESTRIKE(df.open,df.high,df.low,df.close)
    df['3outside'] = talib.CDL3OUTSIDE(df.open,df.high,df.low,df.close)
    df['3starsinsouth'] = talib.CDL3STARSINSOUTH(df.open,df.high,df.low,df.close)
    df['3WHITESOLDIERS'] = talib.CDL3WHITESOLDIERS(df.open,df.high,df.low,df.close)
    df['ABANDONEDBABY'] = talib.CDLABANDONEDBABY(df.open,df.high,df.low,df.close)
    df['ADVANCEBLOCK'] = talib.CDLADVANCEBLOCK(df.open,df.high,df.low,df.close)
    df['BELTHOLD'] = talib.CDLBELTHOLD(df.open,df.high,df.low,df.close)
    df['BREAKAWAY'] = talib.CDLBREAKAWAY(df.open,df.high,df.low,df.close)
    df['CLOSINGMARUBOZU'] = talib.CDLCLOSINGMARUBOZU(df.open,df.high,df.low,df.close)
    df['CONCEALBABYSWALL'] = talib.CDLCONCEALBABYSWALL(df.open,df.high,df.low,df.close)
    df['COUNTERATTACK'] = talib.CDLCOUNTERATTACK(df.open,df.high,df.low,df.close)
    df['DARKCLOUDCOVER'] = talib.CDLDARKCLOUDCOVER(df.open,df.high,df.low,df.close)
    df['DOJI'] = talib.CDLDOJI(df.open,df.high,df.low,df.close)
    df['DOJISTAR'] = talib.CDLDOJISTAR(df.open,df.high,df.low,df.close)
    df['DRAGONFLYDOJI'] = talib.CDLDRAGONFLYDOJI(df.open,df.high,df.low,df.close)
    df['ENGULFING'] = talib.CDLENGULFING(df.open,df.high,df.low,df.close)
    df['EVENINGDOJISTAR'] = talib.CDLEVENINGDOJISTAR(df.open,df.high,df.low,df.close)
    df['EVENINGSTAR'] = talib.CDLEVENINGSTAR(df.open,df.high,df.low,df.close)
    df['GAPSIDESIDEWHITE'] = talib.CDLGAPSIDESIDEWHITE(df.open,df.high,df.low,df.close)
    df['GRAVESTONEDOJI'] = talib.CDLGRAVESTONEDOJI(df.open,df.high,df.low,df.close)
    df['HAMMER'] = talib.CDLHAMMER(df.open,df.high,df.low,df.close)
    df['HANGINGMAN'] = talib.CDLHANGINGMAN(df.open,df.high,df.low,df.close)
    df['HARAMI'] = talib.CDLHARAMI(df.open,df.high,df.low,df.close)
    df['HARAMICROSS'] = talib.CDLHARAMICROSS(df.open,df.high,df.low,df.close)
    df['HIGHWAVE'] = talib.CDLHIGHWAVE(df.open,df.high,df.low,df.close)
    df['HIKKAKE'] = talib.CDLHIKKAKE(df.open,df.high,df.low,df.close)
    df['HIKKAKEMOD'] = talib.CDLHIKKAKEMOD(df.open,df.high,df.low,df.close)
    df['HOMINGPIGEON'] = talib.CDLHOMINGPIGEON(df.open,df.high,df.low,df.close)
    df['IDENTICAL3CROWS'] = talib.CDLIDENTICAL3CROWS(df.open,df.high,df.low,df.close)
    df['INNECK'] = talib.CDLINNECK(df.open,df.high,df.low,df.close)
    df['INVERTEDHAMMER'] = talib.CDLINVERTEDHAMMER(df.open,df.high,df.low,df.close)
    df['KICKING'] = talib.CDLKICKING(df.open,df.high,df.low,df.close)
    df['KICKINGBYLENGTH'] = talib.CDLKICKINGBYLENGTH(df.open,df.high,df.low,df.close)
    df['LADDERBOTTOM'] = talib.CDLLADDERBOTTOM(df.open,df.high,df.low,df.close)
    df['LONGLEGGEDDOJI'] = talib.CDLLONGLEGGEDDOJI(df.open,df.high,df.low,df.close)
    df['LONGLINE'] = talib.CDLLONGLINE(df.open,df.high,df.low,df.close)
    df['MARUBOZU'] = talib.CDLMARUBOZU(df.open,df.high,df.low,df.close)
    df['MATCHINGLOW'] = talib.CDLMATCHINGLOW(df.open,df.high,df.low,df.close)
    df['MATHOLD'] = talib.CDLMATHOLD(df.open,df.high,df.low,df.close)
    df['MORNINGDOJISTAR'] = talib.CDLMORNINGDOJISTAR(df.open,df.high,df.low,df.close)
    df['MORNINGSTAR'] = talib.CDLMORNINGSTAR(df.open,df.high,df.low,df.close)
    df['ONNECK'] = talib.CDLONNECK(df.open,df.high,df.low,df.close)
    df['PIERCING'] = talib.CDLPIERCING(df.open,df.high,df.low,df.close)
    df['RICKSHAWMAN'] = talib.CDLRICKSHAWMAN(df.open,df.high,df.low,df.close)
    df['RISEFALL3METHODS'] = talib.CDLRISEFALL3METHODS(df.open,df.high,df.low,df.close)
    df['SEPARATINGLINES'] = talib.CDLSEPARATINGLINES(df.open,df.high,df.low,df.close)
    df['SHOOTINGSTAR'] = talib.CDLSHOOTINGSTAR(df.open,df.high,df.low,df.close)
    df['SHORTLINE'] = talib.CDLSHORTLINE(df.open,df.high,df.low,df.close)
    df['SPINNINGTOP'] = talib.CDLSPINNINGTOP(df.open,df.high,df.low,df.close)
    df['STALLEDPATTERN'] = talib.CDLSTALLEDPATTERN(df.open,df.high,df.low,df.close)
    df['STICKSANDWICH'] = talib.CDLSTICKSANDWICH(df.open,df.high,df.low,df.close)
    df['TAKURI'] = talib.CDLTAKURI(df.open,df.high,df.low,df.close)
    df['TASUKIGAP'] = talib.CDLTASUKIGAP(df.open,df.high,df.low,df.close)
    df['THRUSTING'] = talib.CDLTHRUSTING(df.open,df.high,df.low,df.close)
    df['TRISTAR'] = talib.CDLTRISTAR(df.open,df.high,df.low,df.close)
    df['UNIQUE3RIVER'] = talib.CDLUNIQUE3RIVER(df.open,df.high,df.low,df.close)
    df['UPSIDEGAP2CROWS'] = talib.CDLUPSIDEGAP2CROWS(df.open,df.high,df.low,df.close)
    df['XSIDEGAP3METHODS'] = talib.CDLXSIDEGAP3METHODS(df.open,df.high,df.low,df.close)
    return df

candle_list = ['DOJI', #0
               'EVENINGSTAR', #1
               'MORNINGSTAR',#2
               'SHOOTINGSTAR',#3
               'HAMMER',#4
               'INVERTEDHAMMER',#5
               'HARAMI',#6
               'ENGULFING',#7
               'HANGINGMAN',#8
               'PIERCING',#9
               'BELTHOLD',#10
               'KICKING',#11
               'DARKCLOUDCOVER']#12


def candle_buysignals(df,CANDLE,UP_PCT=20,DN_PCT=10,plot=False,CONDITION=None,STOCH=False,RSI_THRESH=None,RIZ_THRESH=None,*args,**kwargs):
    '''
    you can bring your own condition or 
        built in conditions:
            1.low_rsi
            2.last_rsi_was_low
            3.riz_corn
            4.200_is_up
            5.50_is_up
            
    '''
    
    # add main candles
    the_twelve(df)
    #Creating Conditions
    #rsi --
    df['rsi']              = pta.rsi(df.close)
    df['low_rsi']          = df['rsi'] < RSI_THRESH
    df['last_rsi_was_low'] = df['low_rsi'].shift()
    
    #riz -- 
    df['riz']              = pta.rsi(df.close,length=2)
    df['low_riz']          = df['riz'] < RIZ_THRESH
    df['riz_corn']         = (df['low_riz']==False) & (df['low_riz'].shift()==True)
    df['last_riz_was_low'] = df['low_riz'].shift() == True

    #ma -- 200
    df['ma_200']            = df.close.rolling(200).mean()
    df['200_is_up']         = df['ma_200'] > df['ma_200'].shift()
    #ma -- 50
    df['ma_50']             = df.close.rolling(50).mean()
    df['50_is_up']          = df['ma_50'] > df['ma_50'].shift()


    #riz and forward facing ma
    df['riz_and_upslug'] = (df['200_is_up'] == True) & (df['low_riz'] == True)

    #buy
    df['buy'] = df[CANDLE].replace(100,True).replace(-100,False).replace(0,False)

    if CONDITION != None:
        if plot == True:
            # i could pass a dic into jenay , hahahah already did 
            jenay(df,scale_one=CONDITION,scale_two='buy',title =CANDLE+ ' Condition: ' + CONDITION )
            
    print(len(df[df['buy']==True]))
    if CONDITION != None:
            # add condition to buy column
            df['buy'] = (df['buy'] == True) & (df[CONDITION]==True)
            
    print(len(df[df['buy']==True]))
    if STOCH == True:
        df[['fast_sto','slow_sto']]  = pta.stoch(df.high,df.low,df.close)
        df['buy']                    = (df['buy']==True) & ( df['fast_sto']<STOCH_THRESH)
    
    if plot  == True:
        if CONDITION != None:
            jenay(df,scale_one = CONDITION,scale_two='buy')
        else:
            jenay(df,scale_two='buy')
            



def show_tweets(TICKER,rm_rt=False):
    indi = []
    for i in range(len(tdf)):
        for t in tdf['hash'][i]:
            if t == TICKER.upper():
                
                indi.append(tdf.index[i])
    # Define Isolated Data Frame
    stdf = tdf.T[indi].T
    
    if (rm_rt == True) & ( len(stdf) > 0 ):
        badli = []
        for i in trange(len(stdf)):
            
            if "RT" in stdf['Text'][i].upper() :
                print(f'retweet in: {stdf.index[i]}')
                badli.append(stdf.index[i])
        stdf = stdf.drop(badli,axis=0)

def mix_twitter_data_with_price(df,ttdf,tic):
    '''
    mixes price (df) with top tweets (ttdf) on the mentioned (tic)
    returns a mixed dataframe
    '''
    # create placeholder columns
    df['twitter_mention'] = False
    df['rolling_total']   = 0
    df['new_king']        = False 
    df['mentioned_before']= False 
    df['mention_date']    = ''
    df

    tweet_df = ttdf[ttdf['top_ticker']==tic]
    tweet_df


    # get the previouse date and the next date
    df['date'] = df.index.date

    df['last_date'] = df.index.date[0]
    for i in range(1,len(df)):
        if df['date'][i] != df['date'][i-1]:
            df['last_date'][i] = df['date'][i-1]
        else:
            df['last_date'][i] = df['last_date'][i-1]
        

    df = df[::-1]
    df['next_date'] = df.index.date[0]
    for i in range(1,len(df)):
        if df['date'][i] != df['date'][i-1]:
            df['next_date'][i] = df['date'][i-1]
        else:
            df['next_date'][i] = df['next_date'][i-1]
        

    df = df[::-1]


    
    print('mixing price and twitter data for:',tic)

    for i in trange(len(tweet_df)):
        mention_date  = tweet_df.index[i]
        rolling_total = tweet_df['rolling_total'][i]
        new_king      = tweet_df['new_king'][i] 

        # isolate and adjust the row thats relevant

        for row in range(1,len(df)-1): 
            if (df['last_date'][row] < mention_date) & ( df['next_date'][row] >mention_date):
                #print('got it at',df.index[row])
                df['twitter_mention'][row] = True
                df['rolling_total'][row]   = rolling_total 
                df['new_king'][row]        = new_king
                df['mention_date'][row]    = str(mention_date) 

    ## now you need mark the first mention

    # grab the first mentiondate
    index_mask = df[df['twitter_mention']==True].index[0]

    # loop to determain if each row is before or after first mention
    for row in range(len(df)):
        if df.index[row] > index_mask:
            df['mentioned_before'][row] = True
    return df

def hilary(df,fast=10,slow=20,title=None,line_one='',line_two='',line_list=None,scale_one='',scale_two='',numidex=False):

    '''
    ploting and scaling all in one
    TAKES:
        1. df
        2. fast and slow ma
        3. line_one and line_two : default= 50dayma 200day ma (THEY FILL THEIR GAP )
        4. line_list : plots a list of column names into line traces 
        5. scale_one - takes bool and make true close for visual guid on signals
        6. numindex : turns a time series index into a string index ( while staying in order
                        and displaying date) . this makes some time series plots easier to read, when 
                        there are gaps in intraday or weekend data



    scale_one and scale_two
    
    '''
    if numidex == True:
        df = numdex(df)
    
    
    # name the avgs
    fname = 'ma_'+str(fast)
    sname = 'ma_'+str(slow)

    #create avgs
    df[fname] = df['close'].rolling(fast).mean().shift()
    df[sname] = df['close'].rolling(slow).mean().shift()
    # True if fast is above
    df['fast_above'] = df[fname]>df[sname]


    if len(line_one) == 0:
        line_one = '50Day_MA'
        df[line_one] = df['close'].rolling(50).mean().shift()
    if len(line_two) == 0:
        line_two = '200Day_MA'
        df[line_two] = df['close'].rolling(200).mean().shift()

    #and finally plot the shindig
    fig = go.Figure(data=[go.Candlestick(x=df.index,#x=df['date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color= 'cyan',
                    decreasing_line_color= 'gray'   
                                        ),
                         go.Scatter(x=df.index, y=df[line_one],name=line_one ,line=dict(color='lightgreen', width=3)),
                         go.Scatter(x=df.index, y=df[line_two],name=line_two ,line=dict(color='red', width=3)),
                         #go.Scatter(x=df.index, y=df[fname] ,  name=fname,  line=dict(color='purple', width=3)),
                         #go.Scatter(x=df.index, y=df[sname],   name=sname, line=dict(color='yellow', width=3))

                         ])
    
#FILL TRACE

    fig.add_trace(go.Scatter(x=df.index, y=df[line_one],
        mode='lines',
        name=line_one,
        opacity=0.09,
        fill='tonexty',
        line=dict(color='lightgreen')))
    
    if len(scale_one) > 0: 
        
        ## this is the pandas update issue
        df = scale_to_close(df,scale_one)
        scale_name = scale_one + '_scaled'

        fig.add_trace(go.Scatter(x=df.index, y=df[scale_name],
            mode='lines',
            name=scale_one,
            opacity=0.02,
            fill='tozeroy',
            line=dict(color='green')))

    
    if len(scale_two) > 0: 
        df = scale_to_close(df,scale_two)
        scale_name_two = scale_two + '_scaled'
        
        fig.add_trace(go.Scatter(x=df.index, y=df[scale_name_two],
            mode='lines',
            name=scale_two,
            opacity=0.02,
            fill='tozeroy',
            line=dict(color='orange')))


    fig.add_trace(go.Scatter(x=df.index, y=df[fname],
                        mode='lines',
                        name=fname,
                            marker=dict(
                            color='orange',
                            size=9
                            )
                            ))



    layout = go.Layout(
        xaxis = dict(
            rangeslider = dict(
                visible = False
            )
        )
    )
    
    
    # Add Lines From A List
    if line_list != None:
        for line in line_list:
            
            fig.add_trace(go.Scatter(x=df.index, y=df[line],
                mode='lines',
                name=line,
                opacity=0.60
                                    ))
    
    fig.update_layout(layout,template='plotly_dark',title=title)#template="plotly_dark",title='Candle')
    fig.show(theme='solar',yaxis = dict(fixedrange = False))

    

def add_twitter_condition(df,plot=True):
    '''
    just makes sure the 'mentioned_before column is ticked off before you buy'
    '''
    if plot == True:
        jenay(df,scale_one='buy',line_one='span_a',line_two='span_b',title='buy before twitter condition')
    df['buy'] = (df['buy'] == True ) & ( df['mentioned_before']==True )
    if plot == True:
        jenay(df,scale_one='buy',line_one='span_a',line_two='span_b',
              title='buy with twitter condition')
    return df

def only_buy_cnt(df,buy_cnt_thresh=1,plot=True):
    '''
    COUNTS HOW MANY BUY SIGNALS YOU GET . 
        - cuts em off after the thresh
    '''
    col_name       = 'buy_count'
    df['blank']    = False
    df             = count_this(df,'buy','blank',col_name)
    df['b_n_u']    = (df['buy']==True) & (df['buy_count']<=buy_cnt_thresh)
    if plot == True:
        jenay(df,scale_one='buy',scale_two='b_n_u')
    df['buy']      = df['b_n_u']
    return df