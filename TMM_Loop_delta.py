import pretty_errors
import sys
from IPython.core import ultratb
sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=False)

from datetime import datetime
start_time = datetime.now()
import pandas as pd
import numpy as np
#import cufflinks as cf
#cf.go_offline(connected=False)
import os
from tqdm import trange
from stealing_fire import load_data
from finding_fire import pct_targets,one_stop,vally_stop,count_this,trendmap,add_weekly,indicator_adder,bipolar



SAVE_STUDY_PATH= 'DELTA_MA'
PATH           = 'SUPERTRADES_over_20/'
MENTION_THRESH = 20
DAYS_BACK      = 300
TIMEFRAME      = '60' # you have to specify time frame since they are all mixed togher
LIMITDAYS      = True
TOTAL_MENTION  = True


ask_to_change_path = str(input('------\n------\nAre you cool with the STUDY_NAME:{}? \nPress: [ENTER] or [ENTER_NEW_NAME]'.format(SAVE_STUDY_PATH)))
if len(ask_to_change_path) > 0:
    SAVE_STUDY_PATH = ask_to_change_path

print('=======STUDY========')
print(SAVE_STUDY_PATH)
print('====================')

study_traits = {
    'SAVE_STUDY_PATH': SAVE_STUDY_PATH,
    'PATH'           : PATH,
    'MENTION_THRESH' :MENTION_THRESH,
    'DAYS_BACK'      :DAYS_BACK,
    'TIMEFRAME'      :TIMEFRAME,
    'LIMITDAYS'      : LIMITDAYS,
    'TOTAL_MENTION'  : TOTAL_MENTION,
    
}

tdf = pd.read_csv('output_data/tweet_matrix.csv',index_col='Datetime')
tdf.index = pd.to_datetime(tdf.index)#,unit='s')
tdf

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

#Preloop test col 
#col = "PW"

results = []
# isolate the date range
for col in tdf.columns:

    # going to have to add the criteria ...
    if len(tdf[tdf[col]==True]) > 0:
        range_df = tdf[tdf[col]==True]
        ###hl(range_df)
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
        ###hl(df)
        ##jenay(df,scale_one=col)
        #im giving this a condition that will never satify so its always true once in play
        if LIMITDAYS == False:
            bipolar(df,first=col,last='close',col = 'mentioned')
            df[col] = df['mentioned']
        #
        # 
        # 
        # 
        #  
        '''
        |||||||||||||||||||||||||||||||||--- {ALGOS} --- |||||||||||||||||||||||||||||||||||
        '''
        #
        #
        #
        #
        #

        bipolar(df,first=col,last='close',col = 'mentioned')

        '''

        ===DELTA_MA===                                  --- the best DAYMN delta you ever smelled...
        
        '''

        fast         = 12
        slow         = 20       
        delta_thresh = 7  # delta_threshes = [4 ,7, 11] 
        up_pct       = 70 #ups = [10,20 ,30 ,50,70,100]
        dn_pct       = 30 #dns = [10,20,30]

        strat_parms = {
            'algo'         : 'DELTA_MA',
            'fast'         :fast,
            'slow'         :slow,
            'delta_thresh' :delta_thresh,  
            'up_pct'        :up_pct, 
            'dn_pct'        :dn_pct,
            'ticker'        :col


        }

        plot_cap     = False
        plot         = False

        #DELTA_MA uses three avg's
        df['200ma'] = df['close'].rolling(200).mean().shift()
        df['fast']  = df['close'].rolling(fast).mean().shift()
        df['slow']  = df['close'].rolling(slow).mean().shift()
        
        #PRICE MUST SLAM DOWN - after a sufficiant beat down is the time to snipe bulls interest
        #    in this case looking for the slow_MA to go below the 200ma(WHILE: it was pointing up)
        condition = 'mentioned' #thow - condition on there too. 
        df['slam_down'] = (df['200ma']>df['200ma'].shift()) & (df['slow']<df['200ma']) & (df[condition]==True) & (df['slow'].shift()>df['200ma'].shift())
        df['fast_ab_slow'] = df['fast']>df['slow']

        #DELTA - is the pct difference from its previouse period XXX TIMES XXX 1000 
        df['delta'] = df['fast'].pct_change()*1000
        df['delta_rising'] = (df['delta'] > delta_thresh) #& (df['slain']==True) #& (df['fast']>df['slow'])
        
        # OFFLIMITS - after a signal , SLOW_MA has to climb above 200ma and slam down again in order to get a new signal
        bipolar(df,'slam_down','delta_rising','slain')

        df['buy'] = (df['delta'] > delta_thresh) & (df['slain'].shift()==True)
        ##jenay(df,line_one='slow',scale_one='slain',scale_two='buy')

        ##jenay(df,scale_one='slam_down',scale_two='delta_rising',line_two='slow')
        if len(df[df['buy']==True]) > 0:
            pct_targets(df,up_pct=up_pct,dn_pct=dn_pct,plot=plot)

            strat_name = 'ONE_STOP:'+str(strat_parms).replace(' ','')
            result     = one_stop(df,strat_name = strat_name,plot=plot,plot_capital=plot_cap)
            for d in strat_parms:
                result[d] = strat_parms[d]

            results.append(result)


            strat_name = 'VALLY_STOP:'+str(strat_parms).replace(' ','')
            result     = vally_stop(df,strat_name = strat_name,plot=plot,plot_capital=plot_cap)
            for d in strat_parms:
                result[d] = strat_parms[d]

            results.append(result)







    '''
-SAVE  RESULTS ZONE-|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
'''
rdf = pd.concat(results)


# LAST ADDITIONS TO THE DATASET
print('made it!')
rdf['backtest_time'   ] = str(datetime.now())
rdf['backtest_runtime'] = datetime.now() - start_time
rdf['mention_criteria'] = 'NONE'#condition

'''
ADD GLOBAL STUDY VARIABLES TO THE RESULTS
'''
for key in study_traits:
    rdf[key] = study_traits[key]



print('\n.\n.\n. savef! \n .\n.\n.')
apath     = 'agg_ouput_data/'
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
    ordf.to_csv(save_name,index=False)

'''SAVE THE STUDY'''
study_path = apath+SAVE_STUDY_PATH+'_study.csv'

if not os.path.exists(study_path):
    rdf.to_csv(study_path,index=False)
else:
    rsdf = pd.read_csv(study_path)
    rsdf = rsdf.append(rdf)
    rsdf.to_csv(study_path,index=False)


#except KeyException as b:
#print(b)
#pass

time_diff = datetime.now() - start_time
print('backtest_runtime:',time_diff)


