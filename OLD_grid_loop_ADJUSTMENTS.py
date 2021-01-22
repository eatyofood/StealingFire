from datetime import datetime
start_time = datetime.now()
from stealing_fire import make_sma_targets,buy_delta,all_candels
from stealing_fire import my_backtest,compile_signals,after_burner,atr_exits

import pandas as pd
import numpy as np
#import cufflinks as cf
#cf.go_offline(connected=False)
import os
from tqdm import trange
from finding_fire import candle_pct,the_twelve



# SORTING DATA 
path = 'data/'
di   = os.listdir(path)
print(pd.DataFrame(di))


daily_data = [sheet for sheet in di if '1D' in sheet]
hourly_data = [sheet for sheet in di if '60' in sheet]
fifteen_data = [sheet for sheet in di if '15' in sheet]
fourhour_data = [sheet for sheet in di if '240' in sheet]
all_data = os.listdir(path)

data_options= [
    daily_data,
    hourly_data,
    fifteen_data,
    fourhour_data
]


'''==VARIABLES=='''
WHICH_DATA     = all_data
STOCH_THRESH   = 20
OUTPUT_PATH    = ''
SHORT_STRATS   = False
UP_PCT_TARGETS =  [6,8,10,11,12,13]
DN_PCT_TARGETS =  [1,2,3,4,5,6]




def rolling_mentions(df,ment_since,ment_thresh,plot=False):
    '''
    takes:
        1.the dataframe
        2.ment_since - int: how far back you want the sum of the mentions
        3.ment_thresh- int: mention threshold
    returns:
        1.dataframe
        2. condition - str: the col name that will be true when your condition is met :)
    example:
        df,condition = rolling_mentions(df,ment_since=30,ment_thresh=5,plot=True)
    '''


    
    rolling_name     = 'rolling_sum:'+str(ment_since)
    df[rolling_name] = df[col].rolling(ment_since).sum()
    
    ment_name        = 'mentioned:'+str(ment_thresh)+'_times_since:'+str(ment_since) 
    df[ment_name]    = df[rolling_name] > ment_thresh
    #return the ment_name WHICH IS : condition and df
    condition        = ment_name
    if plot == True:
        df[ment_name] = df[ment_name].replace(True,1)

        df[[col,rolling_name,ment_name,'close']].iplot(theme='solar',fill=True)
        
    return df,condition

def trigger_condition_mesh(buy_trigger,how_many,trend):
    '''
    takes:
        columns
            buy_trigger - the og signal
            how many - how many signals would you give a shot
            trend    - true when trend is up...
    returns
        buy trigger
    '''

    df['buy_trigger_wtrend'+condition]= (df[buy_trigger] == 100)&(df['condition_met']==True)&(df[trend]==True)
    buy = buy_trigger+'_'+condition
    df[buy] = (df[buy_trigger] == 100)&(df['condition_met']==True)


    df['cnt'] = 0
    cnt_thresh = how_many
    for i in trange(1,len(df)):
        if df[buy][i] ==True:
            df['cnt'][i]=df['cnt'][i-1]+1
        else:
            df['cnt'][i]=df['cnt'][i-1]

    df[buy] = (df[buy]==True)& (df['cnt']<=cnt_thresh)
##hl(df)



#inputs


def pct_targ_stop(df,buy,targ_pct=10,stop_pct=10):
    '''
    takes :
        1.dataframe,
        2. a buy trigger column,
        3.targ_pct, : int 
        4.stop_pct : int
    returns:
        creates columns with buy/exit triggers, ready for a backtest:
        'strat' - column 
            1= buy 
            -1=sell
        'buy' = bool
        'sell'= bool
        
    '''
    #Function

    #name columns
    stop_col = 'stop:'+str(stop_pct)
    targ_col = 'targ:'+str(targ_pct)
    #adjust to pct
    stop_pct = stop_pct/100
    targ_pct = targ_pct/100


    close    = df['close']
    stop_col = 'stop:'+str(stop_pct)
    df[stop_col] = close - (close*stop_pct)
    df[targ_col] = close + (close*targ_pct)

    df

    df["closee"] = df['close']

    #hl(df)

    # Target based entry 

    df['trac'] = False
    df['targ'] = 0
    df['stop']   = 0
    for i in range(1,len(df)):
        if (df[buy].iloc[i] == True) & (df['trac'].iloc[i-1]==False):
            df['targ'].iloc[i] = df[targ_col].iloc[i]
            df['stop'].iloc[i]   = df[stop_col].iloc[i]
            df['trac'].iloc[i]   = True
        elif (df['trac'].iloc[i-1]==True)&(df['stop'].iloc[i-1]>df['low'].iloc[i]):
            df['trac'].iloc[i]   = False
        elif (df['trac'].iloc[i-1]==True)&(df['targ'].iloc[i-1]<df['high'].iloc[i]):
            df['trac'].iloc[i]   = False
        else:
            df['targ'].iloc[i]   = df['targ'].iloc[i-1]
            df['stop'].iloc[i]   = df['stop'].iloc[i-1]
            df['trac'].iloc[i]   = df['trac'].iloc[i-1]




    df['High'] = df['high']
    df['Low'] = df['low']

    df['buy'] = (df['trac'].shift()==False)&(df['trac']==True)
    df['sell'] = (df['trac'].shift()==True)&(df['trac']==False)
    df['signal'] = 0
    for i in range(len(df)):
        if df['buy'][i]==True:
            df['signal'][i]=1
        elif df['sell'][i]==True:
            df['signal'][i]=-1
            
    return df




def once_mentioned_inplay(col):
    df['mentioned_yet'] = False
    for i in trange(1,len(df)):
        if df[col][i] > 0:
            df['mentioned_yet'][i] = True
        else:
            df['mentioned_yet'][i] = df['mentioned_yet'][i-1]

            
def five_ma_buy(condition):
    '''
    creates buy triggers whenever price closed above 5ma
    just give is a condition like
        examples:
            1. tweets over thresh
            2. trending up 
            3. sentiment ab thresh. 
            4. rsi_weekly > thresh
    now its you responsibility to pair this buy signal with a sell sig 
    or several....
    '''
    #FUNCTION
    df['5ma']          = df['close'].rolling(5).mean().shift()
    df['closed_ab_ma'] = df['close'] > df['5ma']
    df['buy']          = (df['closed_ab_ma']==True)&(df[condition]==True)
    
    
def mention_total(df,col):
    '''
    creates a column in your df. that counts total mentions...
    
    
    '''
    df['mention'] = 0
    for i in range(1,len(df)):
        df['mention'][i] = df[col][i] + df['mention'][i-1]

results = []

#df          = pd.read_csv('output_data/first_date.csv').dropna(axis=0)



mention_thresh = 10



# THE LOOP 

daily = 'data/'
CHANGE_STARTS_HERE = ''

for col in all_data:#daily_data:
    #data = daily_data[1]

    #CHEACKPOINT FUNCTION
    # just check if grid name is in grid_path:


    print(col)
    df       = pd.read_csv(path + col,index_col='time')
    df.index = pd.to_datetime(df.index,unit='s')
    [df.rename(columns={col:col.lower()},inplace=True) for col in df.columns]
    df       = df[['open','high','low','close']]#,'volume']]
    max_num  = df['high'].max()+1
    
    # to short or not to short
    if SHORT_STRATS == True:
        df       = max_num - df
    df
    




    #CANDLES START HERE
    canli = the_twelve(df,True)
    print(canli)
    results = []
    for candle in canli:

        grid_name = candle+':'+col+'.csv'

        #grid loop starts here
        up_parms =UP_PCT_TARGETS
        dn_parms =DN_PCT_TARGETS

        #make a placeholder
        place_hold = np.zeros((len(up_parms),len(dn_parms)))
        print('shape:',place_hold.shape)

        #label the dimentions
        phdf = pd.DataFrame(place_hold,columns=dn_parms)
        phdf.index = up_parms
        phdf
        for colu in dn_parms:
            for ind in up_parms:
                #result = validation_buy_pct_targets(df,up_pct=ind,dn_pct=col)
                
                #result  = harami_pct(df,up_pct=ind,dn_pct=col,plot=False,stoch=True,stoch_thresh=10)
                result  = candle_pct(df,candle,up_pct=ind,dn_pct=colu,plot=False,stoch=True,stoch_thresh=STOCH_THRESH)
                #append
                results.append(result)
                #isolate spot on phdf
                #if phdf[col][ind] != None:
                try:
                    phdf[colu][ind] = result['final_pnl']
                except:
                    phdf[colu][ind] = 0
        grid_path = OUTPUT_PATH + 'grid_output/'
        if not os.path.exists(grid_path):
            os.mkdir(grid_path)
        
        phdf.to_csv(grid_path+grid_name)

        















        print(candle)
        print(col)
        print(len(df))
        result = candle_pct(df,candle,20,5,plot=False,stoch=True,stoch_thresh=30,return_list=True)
        results.append(result)
    
#
    '''
    -SAVE  RESULTS ZONE-
    '''
    rdf = pd.concat(results)
    rdf['sec'] = col
    # i should prolly save the scaled acnt plots to add em all together at the end
    # LAST ADDITIONS TO THE DATASET
    print('made it!')
    rdf['index'] = rdf['sec'] + ':' + rdf['strat_name']
    rdf = rdf.set_index('index')
    rdf['backtest_time'] = str(datetime.now())
    rdf['mention_criteria'] = 'NONE'#condition
    rdf['short'] = SHORT_STRATS
    #rdf['strat_name'] = rdf['mention_criteria'] +':'+ rdf['strat_name']

    
    rdf
    print('\n.\n.\n. save \n .\n.\n.')
    apath     = OUTPUT_PATH+'agg_ouput_data/'
    save_name = apath+'collection.csv'
    if not os.path.exists(apath):
        os.mkdir(apath)
        rdf.to_csv(save_name)
    else:
        ordf = pd.read_csv(save_name,index_col='index')
        rdf  = ordf.append(rdf)
        rdf.to_csv(save_name)
    #except KeyException as b:
    #print(b)
    #pass
    
    ## going to need to add the mention criteria as well ... shift

    # OK NOW PUT THEM INTO FUNCTIONS AND YOU ARE IN BUISNESS

time_diff = datetime.now() - start_time
print('backtest_runtime:',time_diff)