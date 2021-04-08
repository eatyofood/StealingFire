


# THIS IS A REPO FOR ALL ALGOS - functions and non i dont judge..





'''
PHENIX ALGO - give it an up band and a stop and when price comes down SHE WILL BURN YOUR CITY TO ASH::   
'''

only_buy = 3#None
risk_multiple     = 1

condition = 'last_trend' #.........................................................................................................
target_buy = 'plot.3'

df['buy'] = (df[condition] == True) & (df['low'].shift()>df[target_buy]) & ( df['low']< df[target_buy] )

#count buys
df = count_this(df,'buy','dn_trend','buy_cnt')

if only_buy != None:
    #only  take this many trades until you get a trend change and reset
    df['buy'] = (df['buy'] == True) & (df['buy_cnt']<=only_buy)
#hl(df)

jenay(df,line_one='plot.3',line_two='vma',scale_one='last_trend',scale_two='buy')

from finding_fire import vally_stop

# this is the target minus distance from buy to target 
### need to add the option to use the pct difference trailing...
df['stop_risk'] = df[target_buy] - (df['vma'] - df[target_buy] * risk_multiple)

DN_TARG='stop_risk'

#result = vally_stop(df,UP_TARG='vma',DN_TARG=DN_TARG,plot=True,plot_capital=True,strat_name='VMA- BAND BUY')

pct_targets(df,up_pct=20,dn_pct=5)
result = one_stop(df)#,UP_TARG='vma',DN_TARG=DN_TARG,plot=True,plot_capital=True,strat_name='VMA- BAND BUY')
result = vally_stop(df),UP_TARG='vma',DN_TARG=DN_TARG,plot=True,plot_capital=True,strat_name='VMA- BAND BUY')
result['targ'] = 'pct'



result['only_buy'] = only_buy

results.append(result)






import pandas_ta as pta 
'''
Short Line Candel Algo --- 
'''
plot = False

# +++ RSI +++ 
RSI_THRESH = 30
rsis       = [10,20,30]

# +++ CONDITION +++ 
CONDITION = 'rsi_below_thresh'
#CONDITION = None

# === XXX RSI_THRESH XXX
# === 
# === 
# === 
#for RSI_THRESH in rsis:


pct_targets(df,up_pct=UP_PCT,dn_pct=DN_PCT)
df['SHORTLINE'] = talib.CDLSHORTLINE(df.open,df.high,df.low,df.close).replace(100,True)
df['rsi']       = pta.rsi(df.close)


#buy when the candle triggers and the mention thresh is met
df['buy_sig'] = (df['SHORTLINE']==True) & (df['mention_thresh_met']==True)

#count how many buy signals you have
count_this(df,'buy_sig','close','buy_cnt')


# if the buy signal is below the thresh its in play
df['buy']     = (df['buy_sig']==True) & (df['buy_cnt'].shift()<BUY_LIMIT)
if CONDITION != None:
    df['buy'] = (df['buy'] == True ) & ( df[CONDITION] == True)

if plot == True:
    jenay(df,scale_one='buy')


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



'''
Momentum Strat --->
'''
plot = False

from finding_fire import add_weekly
add_weekly(df,True,plot=plot)

# +++ RSI_THRESH +++ 
#RSI_THRESH  = 70
rsis        = [60,70,80]

# +++ TARGETS +++
ups = [10,15,20]
dns = [5,10,15]
UP  = 9
DN  = 5

# +++ CONDITION +++  
condition  = 'wk_rsi_ab'

# === XXX RSI_THRESH XXX
# === 
# === 
for RSI_THRESH in rsis:
    # === XXX UP XXX
    # === 
    # === 
    for UP in ups:
        # === XXX DN  XXX
        # === 
        # === 
        for DN  in dns:


            df['wk_rsi_ab'] = df['week_rsi']> RSI_THRESH
            if plot == True:
                jenay(df,scale_one='wk_rsi_ab')

            # This might be an operutun condition  to play a momentum strategy - 
            ### - build a confirmation validation strat with a trailing stop loss

            #results = []

            df['ma5'] = df['close'].rolling(5).mean().shift()


            df['buy'] = (df['close'] > df['ma5']) & (df[condition] == True ) & (df['close'].shift() < df['ma5'])

            # initial plot to get an idea of what it looks like
            if plot == True:
                jenay(df,scale_one=condition,scale_two='buy',line_one='ma5')

            if len(df[df['buy']==True]) > 0 :

                strat_name = 'up:'+str(UP)+'dn:'+str(DN) + 'func:'+'vally_stop'
                pct_targets(df,UP,DN)
                result = vally_stop(df,strat_name=strat_name,plot=plot,plot_capital=plot)
                result['up'] = UP
                result['dn'] = DN
                result['funct']  ='vally_stop'
                result['condition'] = condition
                result['sheet']     = col
                results.append(result)
                result


                strat_name = 'up:'+str(UP)+'dn:'+str(DN) + 'func:'+'one_stop'
                result = one_stop(df,strat_name=strat_name,plot=plot,plot_capital=plot)
                result['up'] = UP
                result['dn'] = DN
                result['funct']  ='one_stop'
                result['condition'] = condition
                result['sheet']     = col
                results.append(result)
                result
            




'''

===DELTA_MA===                                  --- the best DAYMN delta you ever smelled...

'''
plot_cap     = False
plot         = False

# +++ CONDITION +++ 
#CONDITION = 'mentioned' #thow - CONDITION on there too. 
CONDITION = None

# +++ MOVING AVGS +++
FAST         = 12
SLOW         = 20

# +++ DELTA THRESH +++ 
DELTA_THRESH = 7  
thresh_deltas = [4, 7 ,11]


# +++ TARGETS +++ 
UP_PCT       = 70 #ups = [10,20 ,30 ,50,100]
DN_PCT       = 30 #dns = [10,20,30]
ups = [10,20 ,30 ,50]
dns = [10,20,30]


# XXX DELTA_THRESH XXX
#
#
#
for DELTA_THRESH in thresh_deltas:


    # XXX UP TARGETS XXX
    #
    #
    #
    for UP_PCT in ups:

        # XXX DN TARGETS XXX 
        #
        #
        #
        for DN_PCT in dns:
            strat_parms = {
                'algo'         : 'DELTA_MA',
                'FAST'         :FAST,
                'SLOW'         :SLOW,
                'DELTA_THRESH' :DELTA_THRESH,  
                'UP_PCT'        :UP_PCT, 
                'DN_PCT'        :DN_PCT,
                'ticker'        :col


            }


            #DELTA_MA uses three avg's
            df['200ma'] = df['close'].rolling(200).mean().shift()
            df['FAST']  = df['close'].rolling(FAST).mean().shift()
            df['SLOW']  = df['close'].rolling(SLOW).mean().shift()
            
            #PRICE MUST SLAM DOWN - after a sufficiant beat down is the time to snipe bulls interest
            #    in this case looking for the slow_MA to go below the 200ma(WHILE: it was pointing up)
            df['slam_down'] = (df['200ma']>df['200ma'].shift()) & (df['SLOW']<df['200ma']) & (df['SLOW'].shift()>df['200ma'].shift())
            if CONDITION != None:
                df['slam_down']= df['slam_down'] & (df[CONDITION]==True) 
            df['fast_ab_slow'] = df['FAST']>df['SLOW']

            #DELTA - is the pct difference from its previouse period XXX TIMES XXX 1000 
            df['delta'] = df['FAST'].pct_change()*1000
            df['delta_rising'] = (df['delta'] > DELTA_THRESH) #& (df['slain']==True) #& (df['FAST']>df['SLOW'])
            
            # OFFLIMITS - after a signal , SLOW_MA has to climb above 200ma and slam down again in order to get a new signal
            bipolar(df,'slam_down','delta_rising','slain')

            df['buy'] = (df['delta'] > DELTA_THRESH) & (df['slain'].shift()==True)
            ##jenay(df,line_one='SLOW',scale_one='slain',scale_two='buy')

            ##jenay(df,scale_one='slam_down',scale_two='delta_rising',line_two='SLOW')
            if len(df[df['buy']==True]) > 0:
                pct_targets(df,up_pct=UP_PCT,dn_pct=DN_PCT,plot=plot)

                strat_name = 'Delta: '+str(strat_parms).replace(' ','') + '_ONE_STOP:'
                result     = one_stop(df,strat_name = strat_name,plot=plot,plot_capital=plot_cap)
                for d in strat_parms:
                    result[d] = strat_parms[d]

                results.append(result)


                strat_name = 'Delta: '+str(strat_parms).replace(' ','') + '_VALLY_STOP:'
                result     = vally_stop(df,strat_name = strat_name,plot=plot,plot_capital=plot_cap)
                for d in strat_parms:
                    result[d] = strat_parms[d]

                results.append(result)

#def fire_torpedos(df,col):

from finding_fire import the_twelve
import talib
'''
Candle Algo --- 
'''

the_twelve(df)#,#return_candlelist=False):

#[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[CONTROLS]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]

#  +++ PLOT +++ 
plot     = False  

# +++  CANDLE   +++
#CANDLE  = 'BELTHOLD'
#CANDLE  = 'HARAMI'
#CANDLE   = 'MORNINGSTAR'
candle_list = ['DOJI','EVENINGSTAR','MORNINGSTAR','SHOOTINGSTAR','HAMMER','INVERTEDHAMMER','HARAMI','ENGULFING','HANGINGMAN','PIERCING','BELTHOLD','KICKING','DARKCLOUDCOVER']

# +++  TARGETS   +++
#up_targets = [30,50,100]
#dn_targets = [10,30,50]
UP_PCT     = 20
DN_PCT     = 10

# +++  STOCHASTICS +++
#stos          = [10,20,30]
#STOCH_THRESH = 30
STOCH         =False


# +++ CONDITIONS +++
#CONDITION  = None
#CONDITION  = 'low_riz'
CONDITION  = 'low_rsi'
#CONDITION  = 'riz_corn'
#CONDITION  = 'riz_and_upslug'
#CONDITION   = 'slug_is_up'
#conditions = ['low_riz','low_rsi','riz_corn','riz_and_upslug','slug_is_up']

# +++ RSI_THRESH +++
rsis        = [11,19,31]
#RSI_THRESH =  30
#RSI_THRESH  = None



# RIZ+THRESH
RIZ_THRESH  =  11




# === XXX STOCH_THRESH XXX
# ===
# ===
#for STOCH_THRESH in stos:

# === XXX RSI_THRESH XXX
# ===
# ===
for RSI_THRESH in rsis:

# === XXX TARGETS XXX  
# === 
# ===  
#for UP_PCT in up_targets:
    # ===  
    # === 
    # === 
    #for DN_PCT in dn_targets:



# ==  XXX CONDITIONS  XXX 
# == 
# == 
#for CONDITION in conditions: 

    #== XXX CANDLE XXX 
    #==
    #==
    for CANDLE in candle_list:


        #rsi --
        df['rsi'] = pta.rsi(df.close)
        df['low_rsi'] = df['rsi'] < RSI_THRESH


        #riz -- 
        df['riz'] = pta.rsi(df.close,length=2)
        df['low_riz'] = df['riz'] < RIZ_THRESH
        df['riz_corn']= (df['low_riz']==False) & (df['low_riz'].shift()==True)

        #ma -- 
        df['ma_200'] = df.close.rolling(200).mean()
        df['slug_is_up'] = df['ma_200'] > df['ma_200'].shift()
        

        
        #riz and forward facing ma
        df['riz_and_upslug'] = (df['slug_is_up'] == True) & (df['low_riz'] == True)

        if plot == True:
            jenay(df,scale_one=CONDITION,title = 'Condition: ' + CONDITION )

        #results = []
        print('[[[[[[[[[[[[[[[[[[[[[[[[',col,']]]]]]]]]]]]]]]]]]]]]]]]')

    
        

        
        #buy
        df['buy'] = df[CANDLE].replace(100,True).replace(-100,False).replace(0,False)


        if STOCH == True:
            df[['fast_sto','slow_sto']]  = pta.stoch(df.high,df.low,df.close)
            df['buy']                    = (df['buy']==True) & ( df['fast_sto']<STOCH_THRESH)
        #if plot==True:
            #df['buy_scale'] = df['buy'].replace(True,1).replace(1,df.close)
            #df[['buy_scale','close']].iplot(theme='solar',fill=True)
            
        #def candle_pct(df,CANDLE,UP_PCT=10,DN_PCT=5,plot=False,STOCH=False,STOCH_THRESH=30,#return_list=False,CONDITION=None):


        #candle_buy(df,CANDLE,STOCH=STOCH,STOCH_THRESH=STOCH_THRESH,plot=False,#return_list=#return_list)#,CONDITION=CONDITION)
        if CONDITION != None:
            df['buy'] = (df['buy'] == True) & (df[CONDITION]==True)
        if plot == True:    
            jenay(df,scale_one='buy')


        if len(df[df['buy']==True]) > 0:
            pct_targets(df,UP_PCT,DN_PCT)
            print(col)

            # name the strat
            strat_name = CANDLE +'_up:'+str(UP_PCT)+'_dn:'+str(DN_PCT) 
            if RSI_THRESH != None:
                strat_name = strat_name + '_rsi:'+str(RSI_THRESH)
            if STOCH == True:
                strat_name = strat_name + str(STOCH_THRESH)
            if CONDITION != None:
                strat_name = strat_name +'_' +CONDITION
            

            #one_stop
            strat_name = strat_name  + '_' +'One_Stop'
            result =one_stop(df,strat_name=strat_name,plot=plot,plot_capital=plot)
            result['UP_PCT'] = UP_PCT
            result['DN_PCT'] = DN_PCT
            result['CANDLE'] = CANDLE
            result['sheet']  = col
            if RSI_THRESH != None:
                result['RSI_THRESH'] = RSI_THRESH
            if STOCH == True:
                result['STOCH'] = STOCH_THRESH
            if CONDITION != None:
                result['CONDITION'] ='_' +CONDITION
            results.append(result)

            #vally_stop
            strat_name = strat_name +'_' +'Vally_Stop'
            result =vally_stop(df,strat_name=strat_name,plot=plot,plot_capital=plot)
            result['UP_PCT'] = UP_PCT
            result['DN_PCT'] = DN_PCT
            result['CANDLE'] = CANDLE
            result['sheet']  = col
            if RSI_THRESH != None:
                result['RSI_THRESH'] = RSI_THRESH
            if STOCH == True:
                result['STOCH'] = STOCH_THRESH
            if CONDITION != None:
                result['CONDITION'] = CONDITION
            
            results.append(result)

        else:
            result = None
    

def First_Rsi_Telescope_Algo(df,plot=True):
    '''
    FRIST RSI TELESCOPE =---->
    '''
    # Pull Weekly Time Frame Out
    #pull weekly out of daily
    wdf = weekly_pull(df)

    if plot == True:
        jenay(wdf)

    ### Now We Can Add Some Weekly Indicators

    wdf['rsi'] = pta.rsi(wdf.close)

    ### Mix It Back With The Daily Data Frame

    df = weekly_push(df,wdf)
    if plot == True:
        jenay(df,line_one='week_high',line_two='week_low')

    # Now Let's Add The Monthly Time Frame

    mdf = monthly_pull(df)
    if plot == True:
        jenay(mdf)

    pd.set_option('display.max_columns',None)

    mdf['rsi'] = pta.rsi(mdf.close)

    ### And Mix It Back With The Daily Time Frame

    df = monthly_push(df,mdf)


    sola(scale(df[['high','low','week_low','week_high','month_low','month_high']]))
    sola(df[['high','low','week_low','week_high','month_low','month_high']])

    # Structuring An Algo With Time Frames

    ### Telescope - algo first time daily-RSI is above weekly-RSI which is above monthly-RSI

    df['rsi'] = pta.rsi(df.close)
    df['rsi_telescope'] = (df['rsi'] > df['week_rsi']) & (df['week_rsi']> df['month_rsi'])
    df['buy'] = (df['rsi_telescope'].shift()== False) & (df['rsi_telescope']== True)
    if plot == True:
        jenay(df,scale_one='buy')

    sola(df[['rsi','week_rsi','month_rsi']])

    results = []

    # copy and paste this to send it to the refrence database
    strat = 'First-RSI-Telescop'
    target_type = 'percent'
    UP,DN = 50,25
    #ups = [5,15,25,50,75,100]
    #dns = [5,10,20,30,40]
    #for UP in ups:
    #   for DN in dns:
    if len(df[df['buy']==True]) > 0:
        strat_name = 'one_stop'+strat + 'UP_PCT:' + str(UP)+'DN_PCT:' + str(DN)
        pct_targets(df,up_pct = UP,dn_pct=DN)
        result = one_stop(df,strat_name=strat_name,plot=plot)
        result['up_target'] = UP
        result['dn_target'] = DN
        result['target_type'] = target_type
        #result['data']        = table_name
        results.append(result)

        strat_name = 'vally_stop' + strat + 'UP_PCT:' + str(UP)+'DN_PCT:' + str(DN)
        pct_targets(df,up_pct = UP,dn_pct=DN)
        result = vally_stop(df,strat_name=strat_name,plot=plot)
        result['up_target'] = UP
        result['dn_target'] = DN
        result['target_type'] = target_type
        #result['data']        = table_name
        results.append(result)