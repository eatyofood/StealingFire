from datetime import datetime
start_time = datetime.now()
from stealing_fire import make_sma_targets,buy_delta
from stealing_fire import my_backtest,compile_signals,after_burner
import pandas as pd
import numpy as np
#import cufflinks as cf
#cf.go_offline(connected=False)
import os
from tqdm import trange


import sys
from IPython.core import ultratb
sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=False)
#import pretty_errors

SAVE_STUDY_PATH= 'RIZ_EXPERIMENTS'
PATH           = 'SUPERTRADES_over_20/'
MENTION_THRESH = 20
DAYS_BACK      = 300
TIMEFRAME      = '60'



study_traits = {
    'SAVE_STUDY_PATH': 'RIZ_EXPERIMENTS',
    'PATH'           : 'SUPERTRADES_over_20/',
    'MENTION_THRESH' :MENTION_THRESH,
    'DAYS_BACK'      :DAYS_BACK,
    'TIMEFRAME'      :TIMEFRAME
    
}



pd.set_option('display.max_columns',None)
tdf = pd.read_csv('output_data/tweet_matrix.csv',index_col='Datetime')
tdf.index = pd.to_datetime(tdf.index)#,unit='s')
tdf


from stealing_fire import sola
from stealing_fire import hl


LIMITDAYS = True
TOTAL_MENTION = True

# LIST DIRECTORY 
pathli = os.listdir(PATH)
#PREFORM AN OPERTAION TO DETERMAIN WHAT DATA IS IN THE PATH
data_list = [i.split(' ')[1].replace(',','') for i in pathli]
# ISOLATE THOSE COLUMNS
data_list = set(data_list)
len(data_list)
tdf = tdf[data_list]
too_short = [col for col in tdf.columns if len(col)<2]
if len(too_short)>0:
    tdf = tdf.drop(too_short,axis=1)
    print('droped:',too_short)

print(len(tdf.columns))

# add every cell to the one under it
print('total mentions:')
for col in tdf.columns:
    for i in range(1,len(tdf)):
        tdf[col][i] = tdf[col][i] + tdf[col][i-1]
    print(col,':',tdf[col][-1])

#IF YOU WANT TO PUT A MENTION THRESH HOLD ON YOUR BACKTEST ELSE 1
tdf = (tdf>=MENTION_THRESH)
if LIMITDAYS == True:
    for col in tdf.columns:
        # this works becuase the first mention is 1 which is the same as true...
        first_mention = tdf[tdf[col]==True].index[0]
        #here we get the date of out cut off limit....variable

        date_limit = pd.Timedelta(days=DAYS_BACK) + first_mention
        #and overwrite the true conditions if they are past the date set...
        for index in tdf[col].index:
            if index < date_limit:
                pass
            else:
                tdf[col][index]=False

hl(tdf)

from stealing_fire import load_data

from finding_fire import bipolar
from finding_fire import trendmap,add_weekly,indicator_adder
from finding_fire import count_this
from finding_fire import pct_targets,one_stop,vally_stop
from finding_fire import jenay

# you have to specify time frame since they are all mixed togher


#Preloop test col 
#col = "PW"

results = []
# isolate the date range
for col in tdf.columns:

    # going to have to add the criteria ...
    # if len(tdf[tdf[col]==True]) > 0:
    range_df = tdf[tdf[col]==True]
    hl(range_df)
    # isolate the dates where it was in play ocording to that criteria
    start_date = range_df.index[0]
    end_date   = range_df.index[-1]
    print('tweet_criteria, start_date:',start_date)
    print('tweet_criteria, end_date:',end_date)
    # isolate the relevent data.
    sheets    = [s for s in pathli if TIMEFRAME in s]
    sheet     = [s for s in sheets if col in s ][0]
    print(sheet)
    df = load_data(PATH+sheet)
    df
    # Now we create the tweet criteria column in the corrasponding price sheet
    # use start date and end date as criteria
    df[col] = (df.index >= start_date) & (df.index <= end_date)
    #hl(df)
    #jenay(df,scale_one=col)

    # so here is where i would apply an alogo and and see if it has wings

    #im giving this a condition that will never satify so its always true once in play
    bipolar(df,first=col,last='close',col = 'mentioned')



    #jenay(df,scale_one='mentioned')


    #trendmap(df)
    #add_weekly(df,True)
    indicator_adder(df)
    hl(df)

    # So what if we are above the 200 ma and we get a riz: ex







    riz_thresh = 10
    riz_sell   = 89 #
    riz_count  = 3
    up_pct     = 15
    dn_pct     = 15
    plot       = False



    strat_parms = { 
        
        'riz_thresh' :riz_thresh,
        'riz_sell'   :riz_sell, #
        'riz_count'  :riz_count,
        'up_pct'     :up_pct,
        'dn_pct'     :dn_pct,
        'ticker'     : col
    }


    df['200ma'] = df['close'].rolling(200).mean().shift()
    df['rex_when_uptrend'] = (df['close'] > df['200ma']) & (df['riz']<riz_thresh)&(df['riz'].shift()>riz_thresh) & (df['mentioned']==True)
    df['riz_to_high'] = (df['riz'] > riz_sell) & (df['mentioned']== True)

    count_this(df,'rex_when_uptrend','riz_to_high','riz_count')

    df['buy'] = (df['riz_count'] == riz_count)
    
    if len(df[df['buy']==True])> 0:
        #jenay(df,scale_one='rex_when_uptrend',scale_two='riz_to_high')
        if plot:
            jenay(df,scale_two='buy')

        pct_targets(df,up_pct=up_pct,dn_pct=dn_pct,plot=plot)

        strat_name = 'ONE_STOP:'+str(strat_parms).replace(' ','')
        result     = one_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)



        strat_name = 'VALLY_STOP:'+str(strat_parms).replace(' ','')
        result     = vally_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)



    riz_thresh = 11
    riz_sell   = 89 #
    riz_count  = 3
    up_pct     = 10
    dn_pct     = 10
    plot       = False



    strat_parms = { 
        
        'riz_thresh' :riz_thresh,
        'riz_sell'   :riz_sell, #
        'riz_count'  :riz_count,
        'up_pct'     :up_pct,
        'dn_pct'     :dn_pct,
        'ticker'     : col
    }


    df['200ma'] = df['close'].rolling(200).mean().shift()
    df['rex_when_uptrend'] = (df['close'] > df['200ma']) & (df['riz']<riz_thresh)&(df['riz'].shift()>riz_thresh) & (df['mentioned']==True)
    df['riz_to_high'] = (df['riz'] > riz_sell) & (df['mentioned']== True)

    count_this(df,'rex_when_uptrend','riz_to_high','riz_count')

    df['buy'] = (df['riz_count'] == riz_count)
    
    if len(df[df['buy']==True])> 0:
        #jenay(df,scale_one='rex_when_uptrend',scale_two='riz_to_high')
        if plot:
            jenay(df,scale_two='buy')

        pct_targets(df,up_pct=up_pct,dn_pct=dn_pct,plot=plot)

        strat_name = 'ONE_STOP:'+str(strat_parms).replace(' ','')
        result     = one_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)



        strat_name = 'VALLY_STOP:'+str(strat_parms).replace(' ','')
        result     = vally_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)


    riz_thresh = 11
    riz_sell   = 89 #
    riz_count  = 3
    up_pct     = 15
    dn_pct     = 15
    plot       = False



    strat_parms = { 
        
        'riz_thresh' :riz_thresh,
        'riz_sell'   :riz_sell, #
        'riz_count'  :riz_count,
        'up_pct'     :up_pct,
        'dn_pct'     :dn_pct,
        'ticker'     : col
    }


    df['200ma'] = df['close'].rolling(200).mean().shift()
    df['rex_when_uptrend'] = (df['close'] > df['200ma']) & (df['riz']<riz_thresh)&(df['riz'].shift()>riz_thresh) & (df['mentioned']==True)
    df['riz_to_high'] = (df['riz'] > riz_sell) & (df['mentioned']== True)

    count_this(df,'rex_when_uptrend','riz_to_high','riz_count')

    df['buy'] = (df['riz_count'] == riz_count)
    
    if len(df[df['buy']==True])> 0:
        #jenay(df,scale_one='rex_when_uptrend',scale_two='riz_to_high')
        if plot:
            jenay(df,scale_two='buy')

        pct_targets(df,up_pct=up_pct,dn_pct=dn_pct,plot=plot)

        strat_name = 'ONE_STOP:'+str(strat_parms).replace(' ','')
        result     = one_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)



        strat_name = 'VALLY_STOP:'+str(strat_parms).replace(' ','')
        result     = vally_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)


    riz_thresh = 11
    riz_sell   = 89 #
    riz_count  = 4
    up_pct     = 10
    dn_pct     = 10
    plot       = False



    strat_parms = { 
        
        'riz_thresh' :riz_thresh,
        'riz_sell'   :riz_sell, #
        'riz_count'  :riz_count,
        'up_pct'     :up_pct,
        'dn_pct'     :dn_pct,
        'ticker'     : col
    }


    df['200ma'] = df['close'].rolling(200).mean().shift()
    df['rex_when_uptrend'] = (df['close'] > df['200ma']) & (df['riz']<riz_thresh)&(df['riz'].shift()>riz_thresh) & (df['mentioned']==True)
    df['riz_to_high'] = (df['riz'] > riz_sell) & (df['mentioned']== True)

    count_this(df,'rex_when_uptrend','riz_to_high','riz_count')

    df['buy'] = (df['riz_count'] == riz_count)
    
    if len(df[df['buy']==True])> 0:
        #jenay(df,scale_one='rex_when_uptrend',scale_two='riz_to_high')
        if plot:
            jenay(df,scale_two='buy')

        pct_targets(df,up_pct=up_pct,dn_pct=dn_pct,plot=plot)

        strat_name = 'ONE_STOP:'+str(strat_parms).replace(' ','')
        result     = one_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)



        strat_name = 'VALLY_STOP:'+str(strat_parms).replace(' ','')
        result     = vally_stop(df,strat_name = strat_name)
        for d in strat_parms:
            result[d] = strat_parms[d]

        results.append(result)




'''
-SAVE  RESULTS ZONE-
'''
rdf = pd.concat(results)


# i should prolly save the scaled acnt plots to add em all together at the end
# LAST ADDITIONS TO THE DATASET
print('made it!')
#rdf['index'] = rdf['sec'] + ':' + rdf['strat_name']
##rdf = rdf.set_index('index')
rdf['backtest_time'] = str(datetime.now())
rdf['mention_criteria'] = 'NONE'#condition
#rdf['short'] = SHORT_STRATS
#rdf['strat_name'] = rdf['mention_criteria'] +':'+ rdf['strat_name']


'''
ADD GLOBAL STUDY VARIABLES TO THE RESULTS
'''

for key in study_traits:
    rdf[key] = study_traits[key]



print('\n.\n.\n. savef! \n .\n.\n.')
apath     = 'agg_ouput_data/'
#save_name = apath+OUTPUT_PATH+':'+'collection.csv'
save_name =apath+   'collection.csv'

#create directory if its not there
if not os.path.exists(apath):
    os.mkdir(apath)
#save results data if it not there
if not os.path.exists(apath+save_name):
    rdf.to_csv(save_name)
#otherwise append it
else:
    ordf = pd.read_csv(save_name)#,index_col='index')
    rdf  = ordf.append(rdf)
    rdf.to_csv(save_name,index=False)
#except KeyException as b:
#print(b)
#pass

## going to need to add the mention criteria as well ... shift

# OK NOW PUT THEM INTO FUNCTIONS AND YOU ARE IN BUISNESS

time_diff = datetime.now() - start_time
print('backtest_runtime:',time_diff)


