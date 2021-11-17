from stealing.fire import one_stop,vally_stop,pct_targets,jenay
from stealing.fire import one_stop,vally_stop,pct_targets
from stealing.fire import scale
from stealing.fire import monthly_pull
from stealing.fire import sola
from stealing.fire import jenay
from stealing.fire import monthly_pull,monthly_push,weekly_pull,weekly_push,jenay
import cufflinks as cf
cf.go_offline(connected=False)
import pandas as pd
import numpy as np
import pandas_ta as pta
import os
import sqlalchemy as sql
import pandas as pd
cf.go_offline(connected = False)

results = []

import pandas_ta as pta 
import talib

def short_line_algo(df,plot=True,title=''):
    '''
    Short Line Candel Algo --- 
    '''
    #plot = True
    UP_PCT = 20
    DN_PCT = 10

    # +++ RSI +++ 
    RSI_THRESH = 30
    rsis       = [10,20,30]

    # +++ CONDITION +++ 
    CONDITION = 'rsi_below_thresh'
    #CONDITION = None

    # === XXX RSI_THRESH XXXI 
    # === 
    # === 
    # === 
    #for RSI_THRESH in rsis:
    if title != None:
        title = ('ShortLine:'+title)

    pct_targets(df,up_pct=UP_PCT,dn_pct=DN_PCT)
    df['SHORTLINE'] = talib.CDLSHORTLINE(df.open,df.high,df.low,df.close).replace(100,True)
    df['rsi']       = pta.rsi(df.close)
    df['rsi_below_thresh'] = df['rsi'] < RSI_THRESH

    #buy when the candle triggers and the mention thresh is met
    df['buy_sig'] = (df['SHORTLINE']==True) #& (df['mention_thresh_met']==True)

    #count how many buy signals you have
    #count_this(df,'buy_sig','close','buy_cnt')


    # if the buy signal is below the thresh its in play
    df['buy']     = (df['buy_sig']==True) # & (df['buy_cnt'].shift()<BUY_LIMIT)


    if CONDITION != None:
        df['buy'] = (df['buy'] == True ) & ( df[CONDITION] == True)

    if plot == True:
        jenay(df,scale_one='buy',title=title)


    # dont even run the backtest if theres no signals

    if len(df[df['buy']==True])>0:
        strat_name = 'Candel_'+'Mention:'+'-one_stop'+'_UP:'+str(UP_PCT) + '_DN:' + str(DN_PCT) 
        result = one_stop(df,plot=plot,strat_name=title)
        #result['ticker'] = col
        #result['buy_cap']= BUY_LIMIT
        results.append(result)



        strat_name ='Candel_'+ 'Mention:'+'-vally_stop'+'_UP:'+str(UP_PCT) + '_DN:' + str(DN_PCT) 
        result = vally_stop(df,plot=plot,strat_name=title)
        #result['ticker'] = col
        #result['buy_cap']= BUY_LIMIT
        results.append(result)

                    #


def First_Rsi_Telescope_Algo(df,plot=True):
    '''
    FRIST RSI TELESCOPE >>---->
    '''
    # Pull Weekly Time Frame Out
    #pull weekly out of daily
    wdf = weekly_pull(df)

    if plot == True:
        jenay(wdf)

    ### Now We Can Add Some Weekly Indicators

    wdf['rsi'] = pta.rsi(wdf.close)

    ### Mix It Back With The Daily Data Frame

    df = weekly_push(df,wdf)
    if plot == True:
        jenay(df,line_one='week_high',line_two='week_low')

    # Now Let's Add The Monthly Time Frame

    mdf = monthly_pull(df)
    if plot == True:
        jenay(mdf)

    pd.set_option('display.max_columns',None)

    mdf['rsi'] = pta.rsi(mdf.close)

    ### And Mix It Back With The Daily Time Frame

    df = monthly_push(df,mdf)


    sola(scale(df[['high','low','week_low','week_high','month_low','month_high']]))
    sola(df[['high','low','week_low','week_high','month_low','month_high']])

    # Structuring An Algo With Time Frames

    ### Telescope - algo first time daily-RSI is above weekly-RSI which is above monthly-RSI

    df['rsi'] = pta.rsi(df.close)
    df['rsi_telescope'] = (df['rsi'] > df['week_rsi']) & (df['week_rsi']> df['month_rsi'])
    df['buy'] = (df['rsi_telescope'].shift()== False) & (df['rsi_telescope']== True)
    if plot == True:
        jenay(df,scale_one='buy')

    sola(df[['rsi','week_rsi','month_rsi']])

    results = []

    # copy and paste this to send it to the refrence database
    strat = 'First-RSI-Telescop'
    target_type = 'percent'
    UP,DN = 50,25
    #ups = [5,15,25,50,75,100]
    #dns = [5,10,20,30,40]
    #for UP in ups:
    #   for DN in dns:
    if len(df[df['buy']==True]) > 0:
        strat_name = 'one_stop'+strat + 'UP_PCT:' + str(UP)+'DN_PCT:' + str(DN)
        pct_targets(df,up_pct = UP,dn_pct=DN)
        result = one_stop(df,strat_name=strat_name,plot=plot)
        result['up_target'] = UP
        result['dn_target'] = DN
        result['target_type'] = target_type
        #result['data']        = table_name
        results.append(result)

        strat_name = 'vally_stop' + strat + 'UP_PCT:' + str(UP)+'DN_PCT:' + str(DN)
        pct_targets(df,up_pct = UP,dn_pct=DN)
        result = vally_stop(df,strat_name=strat_name,plot=plot)
        result['up_target'] = UP
        result['dn_target'] = DN
        result['target_type'] = target_type
        #result['data']        = table_name
        results.append(result)


def momentum_strat_algo(df,RSI_THRESH=70,UP=9,DN=5,plot=True):
    '''
    Momentum Strat >>--->
    '''
    #plot = False

    from finding_fire import add_weekly
    add_weekly(df,True,plot=plot)

    # +++ RSI_THRESH +++ 
    #RSI_THRESH  = 70
    #rsis        = [60,70,80]

    # +++ TARGETS +++
    #ups = [10,15,20]
    #dns = [5,10,15]
    #UP  = 9
    #DN  = 5

    # +++ CONDITION +++  
    #condition  = 'wk_rsi_ab'

    # === XXX RSI_THRESH XXX
    # === 
    # === 
    #for RSI_THRESH in rsis:
    # === XXX UP XXX
    # === 
    # === 
    #for UP in ups:
    # === XXX DN  XXX
    # === 
    # === 
    #for DN  in dns:


    df['wk_rsi_ab'] = df['week_rsi']> RSI_THRESH
    if plot == True:
        jenay(df,scale_one='wk_rsi_ab')

    # This might be an operutun condition  to play a momentum strategy - 
    ### - build a confirmation validation strat with a trailing stop loss

    #results = []

    df['ma5'] = df['close'].rolling(5).mean().shift()


    df['buy'] = (df['close'] > df['ma5']) & (df[condition] == True ) & (df['close'].shift() < df['ma5'])

    # initial plot to get an idea of what it looks like
    if plot == True:
        jenay(df,scale_one=condition,scale_two='buy',line_one='ma5')

    if len(df[df['buy']==True]) > 0 :

        strat_name = 'up:'+str(UP)+'dn:'+str(DN) + 'func:'+'vally_stop'
        pct_targets(df,UP,DN)
        result = vally_stop(df,strat_name=strat_name,plot=plot,plot_capital=plot)
        result['up'] = UP
        result['dn'] = DN
        result['funct']  ='vally_stop'
        result['condition'] = condition
        result['sheet']     = col
        results.append(result)
        result


        strat_name = 'up:'+str(UP)+'dn:'+str(DN) + 'func:'+'one_stop'
        result = one_stop(df,strat_name=strat_name,plot=plot,plot_capital=plot)
        result['up'] = UP
        result['dn'] = DN
        result['funct']  ='one_stop'
        result['condition'] = condition
        result['sheet']     = col
        results.append(result)
        result
    



