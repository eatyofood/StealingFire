
from datetime import datetime
start_time = datetime.now()

results = []
'''
Inputs
'''


STUDY  = 'Shortline'




import pretty_errors
import pandas as pd
import numpy as np
import cufflinks as cf
import os
cf.go_offline(connected=False)

from finding_fire import bipolar
from stealing_fire import hl
from finding_fire import pct_targets,one_stop,vally_stop,jenay

import talib
from finding_fire import count_this,vally_stop,one_stop


tdf = pd.read_csv('output_data/tweet_matrix.csv').set_index('Datetime').drop(['Unnamed: 10','ticker','hash','Text'],axis=1)
tdf.index = pd.to_datetime(tdf.index)
tdf.head()

tdf['Date'] = tdf.index.date

# Sum Agrigated by date


tdf = tdf.groupby('Date').agg('sum')

tdf.head()

# Suplimenting loop with col 

col = 'PW'
tdf[col]

from finding_fire import save_function








# loop 
for col in tdf.columns:
    

    price_path = 'daily_price/'
    price_dir  = os.listdir(price_path)
    
    # if the data is not in the directory skip it...
    try:
        data = [s for s in price_dir if col == s.split('_')[0]][0]
        data
        
        # HERE IS A GOOD PLACE TO ADD THE STATMENT: IF COL MENTION.SUM > MENTION THRESH 
        # CONTINUE OTHERWISE SKIP TO SAVE TIME ON THE LOOPO RUNNING
        
        # Load Corasponding Data

        df = pd.read_csv(price_path+data).set_index('Date')
        df.index = pd.to_datetime(df.index)
        [df.rename(columns={colu:colu.lower()},inplace=True) for colu in df.columns]
        df

        pd.set_option('display.max_rows',None)

        tdf

        tdf[col].index[0]

        df = df.join(tdf[col]).fillna(0)
        df

        # Now Mix this with what eever time frame you want to mix it with... DUH!!!!!

        #####  if you are going to use smaller time framdes split them up into daily where you have the read_csv() part...


        df

        # adding a total mention column
        
        col_name = col + '_total_mentions'
        df[col_name] = 0
        for i in range(1,len(df)):
            df[col_name][i] = df[col][i]+df[col_name][i-1]

        df[col_name]#.iplot(theme='solar')

        # IDEA: 
        ### mesure the delta of a stock mentions...
        ### usde the mention delta as a buy signal....

        df
        
        # mix a switch column that 

        # MENTION THRESH FOR INPLAY MODE

        #MENTION_THESHES = [1,3,5,10,15,20,25,30,35,40]
        ment_threshes = [5,20]
        for MENTION_THRESH in ment_threshes:
            #MENTION_THRESH = 10

            #only prefor backtest if the first condition is met.
            if tdf[col].sum() >= MENTION_THRESH:
                df['thresh_hit'] = df[col_name] >= MENTION_THRESH
                bipolar(df,'thresh_hit','close','mention_thresh_met')
                hl(df)

                # ALGO HERE



                print('[[[[[[[[[[[[[[[[[[[[[[[[',col,']]]]]]]]]]]]]]]]]]]]]]]]')

                #P_PCT = 50
                #DN_PCT = 30

                up_targets = [30,50,100]
                dn_targets = [10,30,50]
                for UP_PCT in up_targets:
                    for DN_PCT in dn_targets:
                
                        plot   = False

                        #
                        #
                        #
                        #        ALGOS 
                        #
                        #
                        
                        # how many buy signals are you still interested in?
                        BUY_LIMIT = 1
                        plot      = False
                        #for BUY_LIMIT in buy_limits:
                        #buy_limits = [1,15]
                        
                        '''
                        Short Line Candel Algo --- 
                        '''

                        pct_targets(df,up_pct=UP_PCT,dn_pct=DN_PCT)
                        df['SHORTLINE'] = talib.CDLSHORTLINE(df.open,df.high,df.low,df.close).replace(100,True)

                        #buy when the candle triggers and the mention thresh is met
                        df['buy_sig'] = (df['SHORTLINE']==True) & (df['mention_thresh_met']==True)

                        #count how many buy signals you have
                        count_this(df,'buy_sig','close','buy_cnt')


                        # if the buy signal is below the thresh its in play
                        df['buy']     = (df['buy_sig']==True) & (df['buy_cnt'].shift()<BUY_LIMIT)

                        #jenay(df,scale_one='buy')


                        # dont even run the backtest if theres no signals

                        if len(df[df['buy']==True])>0:
                            strat_name = 'Candel_'+'Mention:'+str(MENTION_THRESH)+'-one_stop'+'_UP:'+str(UP_PCT) + '_DN:' + str(DN_PCT) + '_buy_limit:' + str(BUY_LIMIT)
                            result = one_stop(df,plot=plot,strat_name=strat_name)
                            result['ticker'] = col
                            result['buy_cap']= BUY_LIMIT
                            results.append(result)



                            strat_name ='Candel_'+ 'Mention:'+str(MENTION_THRESH)+'-vally_stop'+'_UP:'+str(UP_PCT) + '_DN:' + str(DN_PCT) + '_buy_limit:' + str(BUY_LIMIT)
                            result = vally_stop(df,plot=plot,strat_name=strat_name)
                            result['ticker'] = col
                            result['buy_cap']= BUY_LIMIT
                            results.append(result)

                #
                #
                # THIS WILL BECOME A FUNCTION
                #
                #
                #
                save_function(results,STUDY)


        

    # DONT MOVE THIS ONE!!!
    except BaseException as b:
    	print(b)
        print('no data found for :',col)
        print('//////////////////////////////////////////////////////////')
        print('moving on')
    #hl(df)


time_diff = datetime.now() - start_time
print('backtest_runtime:',time_diff)
