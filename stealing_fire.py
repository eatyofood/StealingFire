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
from finding_fire import jenay, weekly_pull,weekly_push, monthly_pull,monthly_push,one_stop,vally_stop,bipolar,pct_targets,sobar,hl,sola,short_frame,the_twelve


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
    
    #Convert the "buy" Column into FastQuant Format 
    df['buy'] = df['buy'].replace(True,1).replace(False,0)
    # Createing Sell Signal
    for i in range(1,len(df)-1):
        if (df['trac'][i] == False) & (df['trac'][i-1] == True):
            df['buy'][i] = -1

    #hl(df[['TRAC','trac','buy']])
    fq_result = backtest(
                    strategy      = 'ternary',
                    data          = df,
                    custom_column = 'buy',
                    init_cash     = 1000,
                    plot          = False,
                    )

    result = result.join(fq_result)
    return result
      

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


def falcon_backtest(df,mydic,sheet,results=None,research_project=None,plot=True):
    '''
    TAKES: 
        1) price dataframe with buy signals 
        2) paramater_dictionary
        3) sheet : for spreadsheet but really just a refrence to what_data for saving results...
        4) results : is a list for combing results
        5) research_project : name (optional) will save a database table for that specific project.
            todo: thats unnessisarty , just make a column for it!!! and a function to extract it!
        6) plot : 
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
        for i in mydic.keys():
            if mydic[i] != None:
                result[i] = mydic[i]
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
        else:
            result['security'] = sheet.split('_')[0]
        
        if results !=None:
            results.append(result)
        
        '''
        DATABASE ZONE:
            1. save to repo-dump
            2. if project_name is not none. also save everything in that project table
            
            SIDENOTE: IF THIS SLOWS BACKTEST'S DOWN TO MUCH 
                GOBACK, to doing them in bundles...
        
        if research_project != None:

            result['research_project'] = research_project
            push_database(result,research_project,'research',save_index=True,drop_duplicates=True,time_series=False)#,index_name='strat_name')

        push_database(result,'ResearchDump','research',save_index=True,drop_duplicates=True,time_series=False)#,index_name='strat_name')
        '''
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
import config
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
    cryptos = ['EGLD','BTC','ORN','ETH','CEL']
    if ticker in cryptos:
        print('[[[[[[[[[[[[[[[[[[[[[[[[CRYPTO {}]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]'.format(ticker))
        df = get_crypto(ticker,time_frame,start_date = '2020-03-01-00-00')
    elif time_frame == '1d':
        df = dnld_daily(ticker)
        # standardize
        df.index.name = 'date'
    else:
        if time_frame == '1hr':
            dtype = 'historical-chart/1hour'

        if time_frame == '15min':
            dtype = 'historical-chart/15min'

        url = (f"https://financialmodelingprep.com/api/v3/{dtype}/{ticker}?apikey={config.fin_mod_api}")
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

def show_tweets(TICKER):
    indi = []
    for i in range(len(tdf)):
        for t in tdf['hash'][i]:
            if t == TICKER.upper():
                indi.append(tdf.index[i])
    return tdf.T[indi].T

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
from config import consumer_key
from config import consumer_secret
from config import access_token
from config import access_token_secret


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
    #print(tables)
    #print(table_name)

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
        from finding_fire import sola,sobar

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
            
    