


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




