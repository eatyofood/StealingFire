


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


