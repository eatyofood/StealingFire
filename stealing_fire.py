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


def load_data(path):
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
    df = df[col_list]
    return df


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




#ATR TARG - STOP GENERATOR - EXITS
def atr_exits(df,dn_mul=1,up_mul=2,buy_trigger='buy'):
    '''
    
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



#[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[ SCRAPER  ]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
api = '26815f601e2c459e55a4510a897ea5dd'
from urllib.request import urlopen
import json
import os
import pandas as pd

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

def save_dat_data(dtype,ticker,df):
    sheet_name = (ticker+'_'+dtype.replace('/','_'))
    p = 'downloaded_data/'
    if not os.path.exists(p):
        os.mkdir(p)
    df.to_csv(p+sheet_name+'.csv')
    
def get_some(dtype,ticker):
    url = ("https://financialmodelingprep.com/api/v3/{}/{}?apikey=26815f601e2c459e55a4510a897ea5dd").format(dtype,ticker)
    data = get_jsonparsed_data(url)
    df = pd.DataFrame(data)
    save_dat_data(dtype,ticker,df)
    return df 




def get_price_data(ticker,time_frame='15min'):
    dtype      = 'historical-chart/'+time_frame
    df         = get_some(dtype,ticker)
    print('got data!')
    time.sleep(3)
    df = df[::-1]
    #df = df.set_index('data')

    df.set_index('date')
    save_name = 'data/'+ticker +'_' +time_frame + '.csv'
    print(save_name)
    if not os.path.exists('data/'):
        os.mkdir('data/')
    df.to_csv(save_name)
    print('saved:',time_frame)
    
    


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
