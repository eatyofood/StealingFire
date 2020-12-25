import pandas as pd
from tqdm import trange
import talib
import pandas_ta as pta
      
def hl(df):
    def highlight(boo):
        criteria = boo ==True
        return['background-color: green'if i else '' for i in criteria]
    df = df.style.apply(highlight)
    return df


def one_stop(df,UP_TARG='up_targ',DN_TARG='dn_targ',BUY='buy',plot=True,plot_capital=True,strat_name='strat_name_here',limit=''):
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

    #need a candelstick PLT SUCKA!!!
    if plot == True:
        df['trac_scale'] = df['trac'].replace(True,1).replace(1,df.close) 
        df['TARG_scale'] = df['TARG'].replace(True,1).replace(1,df.close)
        df['STOP_scale'] = df['STOP'].replace(True,1).replace(1,df.close)
        df['OUT_scale']  = df['OUT'].replace(True,1).replace(1,df.close)
        df['ENTRY_scale']= df['ENTRY'].replace(True,1).replace(1,df.close)
        df['EXIT_scale'] = df['EXIT'].replace(True,1).replace(1,df.close)


        #df[['trac_scale','close','TARG_scale','STOP_scale','ENTRY_scale','OUT_scale','EXIT_scale']].iplot(theme='solar',fill=True)

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

    #simulation results
    for i in trange(1,len(df)):
        if (df['TRAC'][i] == False) & (df['TRAC'][i-1]==True):
            df['PNL'][i] = exit[i-1] - df['ENTRY'][i-1]
            df['PNL_PCT'][i] = df['PNL'][i]/df['ENTRY'][i-1]
            scale[i] = (scale[i-1]*df['PNL_PCT'][i])+scale[i-1]
        else:
            scale[i] = scale[i-1]
    #plot_capital = True
    if plot == True:
        df[['ENTRY_scale','close','SCALE_ACNT']].iplot(theme='solar',fill=True)
        
        
        
    
    
    
    df['win_cnt'] = df['PNL_PCT']>0
    df['los_cnt'] = df['PNL_PCT']<0
    
        
    win_cnt = df['win_cnt'].sum()
    los_cnt = df['los_cnt'].sum()
    total   = win_cnt+los_cnt
    win_pct = (win_cnt/total)
    
    #FIGURE OUT PNL AND WHICH ONE TO USE
    #final_pnl= (df['acnt'][-1]-1000)/1000*100
    
    # accumulitive PNL
    acc_pnl   = ((df['SCALE_ACNT'].iloc[-1] - first_buy)/first_buy*100)
    final_pnl = str(round(acc_pnl))# +str('%')
    acc        = True

    #non accumulitive PNL
    non_acc_pnl = df['PNL_PCT'].sum()

    #which one is better?
    if (acc_pnl < non_acc_pnl):
        acc = False
    #non accumulitive pnl
    non_acc_final_pnl = str(round(non_acc_pnl))

    print('STRAT_NAME   :',strat_name)
    print('final_acnt value:',df['SCALE_ACNT'].iloc[-1])
    print('total_+trades:',total)
    print('wins        :',win_cnt)
    print('loss        :',los_cnt)
    print('win_percent :',(win_pct))
    print('final_pnl   :',final_pnl,'%')

    d = {}
    li =[]
    
    d['strat_name']        = strat_name
    d['final_acnt value']  = df['SCALE_ACNT'].iloc[-1]
    d['total_trades']      = total
    d['wins']              = win_cnt
    d['loss']              = los_cnt
    d['win_percent']       = win_pct*100
    d['final_pnl']         = final_pnl
    d['accumulitive_pnl']  = acc
    d['non_acc_final_pnl'] = non_acc_final_pnl
    
    li.append(d)
    result = pd.DataFrame(li)
    return result


def pct_targets(df,up_pct=10,dn_pct=5,plot=True):
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
        
        
        
def candle_pct(df,candle,up_pct=10,dn_pct=5,plot=False,stoch=False,stoch_thresh=30,return_list=False):
    
    strat_name = candle + '_stoch:'+str(stoch_thresh)+'uppct:'+str(up_pct)+'dnpct'+str(dn_pct)
    print(strat_name)


    candle_buy(df,candle,stoch=stoch,stoch_thresh=stoch_thresh,plot=False,return_list=return_list)#,condition=condition)
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
