from track_sectors import plot_n_scrape
import pandas as pd
import os
from finding_fire import jenay
import sqlalchemy as sql
import time
import cufflinks as cf 
cf.go_offline(connected=False)
# Established Database Connection


eng = sql.create_engine('postgresql://postgres:password@localhost/stock_market')
con = eng.connect()
print(eng.table_names())


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


        url = ("https://financialmodelingprep.com/api/v3/{}/{}?apikey=26815f601e2c459e55a4510a897ea5dd").format(dtype,ticker)
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

## Query by Username
#Creation of queries using Tweepy API

#Function is focused on completing the query then providing a CSV file of that query using pandas

tweets = []



#HOLYSHIT - if i archive INSIDE THE FUNCTION i dont have to worry about all that ticker bullshit!


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

# Input username to scrape tweets and name csv file
'''
make this into an input if you want something other that super
'''
import re
import pandas as pd
import pretty_errors
import shutil 
from tqdm import trange
import time
import os
from datetime import datetime
import sqlalchemy as sql

username = 'super_trades'
count = 300#int(input('how many you want?'))
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
        
        
        if len(w) == len(result):
            #print('====GOOD====',w)
            
            goodli.append(re.sub(r'\d+', '', w.replace('$','')))
        else:
            #print('====NAH====',w)
            pass



    #print(goodli)
    return goodli
        
def twit_grid(df,username):
    '''
    turns "hash" column ( list of tickers ) into a grid
    '''


    for i in trange(len(df)):
        ticli = df['hash'][i]

        for tic in ticli:
            tic = tic.upper()
            if tic not in df.columns:
                df[tic] = 0
            else:
                df[tic][i] = 1


    from finding_fire import hl,sola
    # eliminate rows that dont contain ticker symbols
    df = df[df['hash'].apply(len)>0]

    boring = ['Tweet Id','Text','hash','tic_count']
    #hl(df)

    sola(df.drop(boring,axis=1).rolling(12).sum(),title='Rolling Twelve')

    ## I Want To See This Cross Reference With Price Data

    ### 

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
        a=pd.read_sql_query('select * from {}'.format(table_name),con=eng).set_index('Datetime')

        # Add Columns If Not In Database
        left_overs = set(df.columns) - set(a.columns)
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

    df

    

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
    try:
        grid = twit_grid(df,username)
    except:
        grid = None
        
    return df,grid
