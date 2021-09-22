import pandas as pd
import time
import os
import tweepy
from config import consumer_key
from config import consumer_secret
from config import access_token
from config import access_token_secret
from stealing.time import to_db

#prep for using twitter API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)

def username_tweets_to_db(username,count):
    try:      
        # Creation of query method using parameters
        tweets = tweepy.Cursor(api.user_timeline,id=username).items(count)

        # Pulling information from tweets iterable object
        tweets_list = [[tweet.created_at, tweet.id, tweet.text] for tweet in tweets]

        # Creation of dataframe from tweets list
        # Add or remove columns as you remove tweet information
        tweets_df = pd.DataFrame(tweets_list,columns=['Datetime', 'Tweet Id', 'Text'])

        
        #ARCHIVE HERE!
        tweets_df = tweets_df.set_index('Datetime')
        # subtract 4 hours from GMT to be EST: best time ever!
        tweets_df.index = tweets_df.index - pd.Timedelta(hours=4)
        
        table_name = username.replace('@','') 
        to_db(tweets_df,table_name,'twitter')
        return tweets_df
    except BaseException as e:#except BaseException as e:
          print('failed on_status,',str(e))
          time.sleep(3)
    

def show_tweets(TICKER,rm_rt=False):
    indi = []
    for i in range(len(tdf)):
        for t in tdf['hash'][i]:
            if t == TICKER.upper():
                
                indi.append(tdf.index[i])
    # Define Isolated Data Frame
    stdf = tdf.T[indi].T
    
    if (rm_rt == True) & ( len(stdf) > 0 ):
        badli = []
        for i in trange(len(stdf)):
            
            if "RT" in stdf['Text'][i].upper() :
                print(f'retweet in: {stdf.index[i]}')
                badli.append(stdf.index[i])
        stdf = stdf.drop(badli,axis=0)
    
    return stdf
