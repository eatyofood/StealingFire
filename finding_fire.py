import pandas as pd
from tqdm import trange
import talib
import pandas_ta as pta
import os
      
def hl(df):
    def highlight(boo):
        criteria = boo ==True
        return['background-color: green'if i else '' for i in criteria]
    df = df.style.apply(highlight)
    return df


def one_stop(df,UP_TARG='up_targ',DN_TARG='dn_targ',BUY='buy',plot=False,plot_capital=False,strat_name='strat_name_here',limit=''):
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
    df['ENTRY_scale']= df['ENTRY'].replace(True,1).replace(1,df.close)
    #need a candelstick PLT SUCKA!!!
    if plot == True:
        df['trac_scale'] = df['trac'].replace(True,1).replace(1,df.close) 
        df['TARG_scale'] = df['TARG'].replace(True,1).replace(1,df.close)
        df['STOP_scale'] = df['STOP'].replace(True,1).replace(1,df.close)
        df['OUT_scale']  = df['OUT'].replace(True,1).replace(1,df.close)
        
        df['EXIT_scale'] = df['EXIT'].replace(True,1).replace(1,df.close)


        df[['trac_scale','close','TARG_scale','STOP_scale','ENTRY_scale','OUT_scale','EXIT_scale']].iplot(theme='solar',fill=True,title=(strat_name+' Target - plot'))

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
        df[['ENTRY_scale','close','SCALE_ACNT']].iplot(theme='solar',fill=True,title=(strat_name+' Capital Scaled'))



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
    if plot_capital == True:
        result[['wins','loss']].sum().plot(kind='pie')



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
    


import plotly.graph_objects as go

def jenay(df,fast=10,slow=20,title=None,line_one='',line_two='',scale_one='',scale_two=''):

    '''
    ploting and scaling all in one
    TAKES:
        1.df
        2.fast and slow ma
        3.line_one and line_two : default= 50dayma 200day ma (THEY FILL THEIR GAP )
        4.scale_one - takes bool and make true close for visual guid on signals



    scale_one and scale_two
    
    '''

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
        scale_name = scale_one + '_scale'
        df[scale_name] = df[scale_one].replace(True,1).replace(1,df.close)
        fig.add_trace(go.Scatter(x=df.index, y=df[scale_name],
            mode='lines',
            name=scale_one,
            opacity=0.02,
            fill='tozeroy',
            line=dict(color='green')))

    
    if len(scale_two) > 0: 
        scale_name_two = scale_two + '_scale'
        df[scale_name_two] = df[scale_two].replace(True,1).replace(1,df.close)
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
    fig.update_layout(layout,template='plotly_dark',title=title)#template="plotly_dark",title='Candle')
    fig.show(theme='solar',yaxis = dict(fixedrange = False))

    



       #buy strace

    '''fig.add_trace(go.Scatter(x=df.index, y=df['val'],
                            mode='lines',name='Validation',
                             line=dict(color='lightskyblue',
                                      )
                            ))
    #                    mode='markers',
    #                    name='markers'))
'''
'''
    SO THESE ARE NEAT AND TIDY 


    fig.add_trace(go.Scatter(x=df.index, y=df['buyscale'],
                        mode='markers',
                        name='BUY',
                            marker=dict(
                            color='seagreen',
                            size=8
                            )
                            ))




    fig.add_trace(go.Scatter(x=df.index, y=df['sellscale'],
                        mode='markers',
                        name='SELL',
                                     marker=dict(
                                     color='#d62728',
                                     size=8,)


                            ))


#FILL TRACE

    fig.add_trace(go.Scatter(x=df.index, y=df['tracscale'],

    mode='lines',
    name='BUY',
    opacity=0.09,
    fill='tozeroy',
                            line=dict(color='lightgreen')))

''' 


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

    from stealing_fire import sola,hl
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
    df.iplot(theme='solar',kind='bar',title=title)import numpy as np



import pandas as pd
import seaborn as sns

def make_a_grid(df,col_one,col_two,content_col='final_pnl',plot=True):
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
        
    if plot == True:
        sns.heatmap(gdf)

    return gdf
