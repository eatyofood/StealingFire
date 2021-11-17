from webull import webull
import pandas as pd
import sqlalchemy as sql
import os
from datetime import datetime
wb = webull()

def to_db(df ,table_name,database='postgresql://postgres:password@localhost'):
    '''
    uses your dataframe to append or create a database table
    '''
    #create engine
    eng = sql.create_engine(f'{database}/{table_name}')
    # List tables 
    con = eng.connect()
    #print(eng.table_names())

    # Add Columns If Not In Database
    #left_overs = set(df.columns) - set(a.columns)
    #print('columns not in database:',len(left_overs),'columns left over:',left_overs)
    #if len(left_overs) > 0:
    #    for col in left_overs:
    #        con.execute("ALTER TABLE '{}' ADD COLUMN '{}' TEXT NULL;".format(table_name,col))

    # Save Data To Base
    df.to_sql(table_name,con,if_exists = 'append', index = True)
    # close connection
    con.close()
                    
                    

def positions(show_orders=False):
    '''
    get current positions or orders. 
    '''
    import config
    
    data         = wb.login(config.wb_em, config.wb_p,config.wb_de)
    orders       = wb.get_current_orders()
    # ORDERS
    odf = pd.DataFrame(orders)

    # POSITIONS
    data = wb.get_positions()
    podf = pd.DataFrame(data)

    podf['tic'] = ""

    #extracting the ticker from the dictionary_index
    for i in range(len(podf)):
        podf['tic'][i] = podf['ticker'][i]['symbol']
    
    # set the indexx
    podf['datetime'] = str(datetime.now()).split('.')[0]
    podf             = podf.set_index('datetime')
    
    #columns for positions
    cols = ['tic','positionProportion',
            'unrealizedProfitLoss',
            'marketValue','lastPrice','costPrice','cost','position']


    #print(len(cols))
    cols = [ col for col in cols if col in podf]
    #print(len(cols))

    # extracting ticker from orders dictionary index
    odf['tic'] = ""
    for i in range(len(odf)):
        odf['tic'][i] = odf['ticker'][i]['symbol']
    # SAVE TO CSV HERE AND THEN DATABASE
    spath = 'data_logg/'
    if not os.path.exists(spath):
        os.mkdir(spath)
    #save if path not exists else append. 
    save_path = spath + 'position_log.csv'
    if not os.path.exists(save_path):
        podf.to_csv(save_path)
    else:
        odf = pd.read_csv(save_path)
        ndf = odf.append(podf) 
        ndf.to_csv(save_path)
    # TODO: insert datebase logic here!
    try:
        to_db(podf,table_name='positions_archive')
    except Exception as e:
        print(e)
    podf = podf[cols] 

   
    if show_orders == False:
        output = podf.copy()
    else:
        output = odf.copy()
    return output

def buy_stonk(ticker,buy_the='ask',cash=200,price=None):
    '''
    purchace stock from webull
    TAKES:
        ticker  : str 
        buy_the : str [ask,bid,price] 
                do you want tto buy at the bid,ask, or last price?
        cash    : float 
                the amount you want to spend
        qnty    : int - if you specify a qnty it will supercced cash amount 
    '''
    import config
    from webull import webull
    wb = webull()
    # log in stuff
    data             = wb.login(config.wb_em, config.wb_p,config.wb_de)
    rep              = wb.get_trade_token(config.wb_pi)
    
    print(rep)
    
    # show current positions
    print(positions())


    # get quote
    quote = wb.get_quote(ticker)
    print('+++')
    print(quote)
    
    ticker_id = quote['tickerId']
    with open('quote.txt','a') as f:
        f.write(str(quote) + '\n ')

    if price != None:
        print('price was given +++')
    else:
        #BLOCK HERE]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
        qdf   = pd.DataFrame([quote]) # TODO: save to database before triming
        qdf   = qdf[['name','bid','ask','symbol','disExchangeCode','tradeTime','pPrice']]
        print(qdf)

        # get prices 
        ask =  float(qdf['askList'][0][0]['price'])
        bid =  float(qdf['bidList'][0][0]['price'])
        ppc =  float(qdf['pPrice'][0])
        qdf['ask'] = ask
        qdf['bid'] = bid
        print(bid,ask,ppc)

        #TODO: IF PRICE != nONE DONT DO ALL THIS!
        # choose price
        if buy_the == 'bid':
            price = bid + 0.1
        elif buy_the == 'ask':
            price = ask + 0.1
        else: 
            price = ppc
        print('price:',price)
        
    #DATABASE LOGIC HERE - build dictionary 
    save_path = 'data_log/'
    time      = str(datetime.now()).split('.')[0]
    ddi       = {
        'time'   : time,
        'ticker' : ticker,
        'buy_the': buy_the,
        'cash'   : cash,
    }
    #TO HERE\\\]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]
    # Get Quantity

    qnty = int(round(cash/price))
    print('cash:',cash,'qnty:',qnty)
    ddi['qnty'] = qnty
    with open('data/request_log.txt','a') as f :
        f.write(str(ddi)+'\n')
    
    
    # show current positions again 
    #rep = wb.place_order(ticker,tId=ticker_id,price=price,quant=qnty)
    rep = wb.place_order(ticker,tId=ticker_id,price=price,quant=qnty)
    print(rep)
    # save the response 
    #TODO: make this update csv file, use csv to update a database. 
    
    with open('data/buy_log.txt','a') as f:
        f.write(str(rep)+'\n')
    ddi['response'] = str(rep)
    
    log_df = pd.DataFrame([ddi])
    try:
        to_db(log_df,'order_archive')
    except Exception as e:
        print(e)
    #show current positions again

    #print(positions)
    return rep
podf = positions()
podf 
