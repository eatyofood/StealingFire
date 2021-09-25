from stealing.fire import std_targets
from stealing.fire import one_stop
from stealing.fire import count_this
from stealing.fire import falcon_backtest,pct_targets
from stealing.fire import hl,jenay
import pandas_ta as pta
import pandas as pd
import os 
from stealing.time import from_db,show_tables

def first_cloud_break_survivor(df,title='first cloud break survivor'):
    '''
    when the price was hanging out below the cloud for a while, after its first
    break, if that break can survive a corner above the cloud
    TRIGGER BUY
    returns:
        a dataframe with a bunch of columns add to it the most important one being 
        BUY
    '''
    # Add Cloud
    df[['span_a','span_b']] = pta.ichimoku(df.high,df.low,df.close)[0][['ISA_9','ISB_26']]
    #jenay(df,line_one='span_a',line_two='span_b')
    # Position Relative The Cloud
    df['ab_cld'] = df['low'] > df['span_a']
    df['bl_cld'] = df['high'] < df['span_b']
    #jenay(df,scale_one='ab_cld',scale_two='bl_cld')
    # fist with low above cloud
    df['first_break'] = ( df['ab_cld'] == True)& (df['ab_cld'].shift() == False )

    # see if it was last below. resets when ab cloud
    df['last_below'] = False
    for i in range(len(df)):
        if df['bl_cld'][i] == True:
            df['last_below'][i] = True
        elif df['ab_cld'][i] == True:
            df['last_below'][i] =  False
        else:
            df['last_below'][i] = df['last_below'][i-1]

    # its special when you get a break after being below
    df['break_when_last_below'] = (df['first_break']==True) & ( df['last_below'].shift() == True)
    jenay(df,scale_one='first_break',scale_two='break_when_last_below',line_one='span_a',line_two='span_b')

    #  it must survive a Corner
    df['riz'] = pta.rsi(df.close,length=2)
    df['up_corn'] = (df['riz'] > df['riz'].shift()) & ( df['riz'].shift() < df['riz'].shift(2))
    #jenay(df,line_one='riz',scale_one='up_corn')

    ## if first break wait for a corner
    df['waiting_for_corner'] = False
    for i in range(len(df)):
        if df['break_when_last_below'][i] == True:
            df['waiting_for_corner'][i] = True
        elif df['up_corn'][i] == True:
            df['waiting_for_corner'][i] == False
        else:
            df['waiting_for_corner'][i] = df['waiting_for_corner'][i-1]
    #jenay(df,scale_one='waiting_for_corner',scale_two='up_corn',line_one='span_a',line_two='span_b')

    # if we are waiting for a corner and its above
    df['survived_corner'] = False 
    for i in range(len(df)):
        if (df['up_corn'][i] == True) & (df['waiting_for_corner'][i-1]==True) & (df['ab_cld'][i-1]==True):
            df['survived_corner'][i] = True

    if title != None:
        title = title + 'Ichimoku'
    else:
        title = 'Ichimoku'
    jenay(df,scale_one='survived_corner',line_one='span_a',line_two='span_b',scale_two='bl_cld')
    df['buy'] = df['survived_corner']
    return df


from stealing.fire import bipolar

def back_burner_buysignal(df,RSI_THRESH=40,plot=True):
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
    #df['buy'] = df[buy]



    if plot == True:
        jenay(df,scale_one='waiting',scale_two='first_oversold')


def up_and_under(df,atr_multiple=2,ema_len=12,up_pct=10,dn_pct=2,plot_everything=True,plot=True):
    '''
    this algo buys when the ema is pointing up , but price falls below the ATR (std)
    that is offset by one period. 
    the idea is you have a sharp pullback when things are generally trending . 
    it comes with:
        pct targets but you dont have to use em
        its just to give the idea that if its 
        going to turn its going to turn NOW! 
    '''


    df = std_targets(df,atr_multiple,atr_multiple)
    #jenay(df,scale_one='survived_corner',line_list=['up_atr','dn_atr'])

    ## Lets try offsetting STD targets

    df['up_offset'] = df['up_atr'].shift()
    df['dn_offset'] = df['dn_atr'].shift()
    if plot_everything:
        jenay(df,line_list=['up_offset','dn_offset'],title='Atr Multiple You Choose')
    #plotting some other ATR multiples
    stds = []
    for iteration in range(1,8):
        std_targets(df,iteration,iteration)
        df['up_atr'] = df['up_atr'].shift()
        df['dn_atr'] = df['dn_atr'].shift()
        df = df.rename(columns={'up_atr':'up_atr'+str(iteration),'dn_atr':'dn_atr'+str(iteration)})
        stds.append('up_atr'+str(iteration))
        stds.append('dn_atr'+str(iteration))
    if plot_everything:

        jenay(df,line_list=stds,title='ATR Rainbow')

    #THE ALGO---------------
    df['ema'] = pta.ema(df.close,ema_len)
    # EMA is up
    df['ema_up']           = df['ema']>df['ema'].shift()
    # price is under last periods STD multiple
    df['under_std']        = df['low']<df['dn_offset']
    #both together
    df['up_and_under'] = (df['ema_up'] == True ) & ( df['under_std'] == True)
    if plot_everything or plot :

        jenay(df,line_one='ema',line_list=['up_offset','dn_offset'],scale_one='up_and_under',title='Up And Under Signals')
    df['buy'] = df['up_and_under']
    
    # TARGETS
    pct_targets(df,up_pct,dn_pct)
    return df
