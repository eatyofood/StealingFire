
'''
RIZ
'''

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


        '''

        ===DELTA_MA===                                  --- the best DAYMN delta you ever smelled...
        
        '''

        fast         = 12
        slow         = 20       
        delta_thresh = 7  #thresh_deltas = [4, 11] 
        up_pct       = 70 #ups = [10,20 ,30 ,50,100]
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





