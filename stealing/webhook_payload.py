from datetime import datetime
from stealing.time import to_db
import pandas as pd
import pretty_errors
from stealing.time import say 
import os
import shutil

#/home/brando/anaconda3/lib/python3.7/site-packages/stealing/data
#print(os.listdir())


algo_list_path = '/home/brando/anaconda3/lib/python3.7/site-packages/stealing/data//ALGO_LIST.csv' 
adf            = pd.read_csv(algo_list_path)
say('which algo would you like to deploy?')




confirm = False
while confirm == False:
    print(adf)
    a_input = input('ENTER ALGO:').upper()
    for i in range(len(adf)) :
        algo = adf['ALGO_NAME'][i]
        if a_input in algo:
            say(algo.replace('_','')+' algo')
            di = {}
            
            print('SELECTION:',algo)
            say('what ticker symbol?')
            di['tick']     = input('ENTER THE SYMBOL:').upper()
            di['algo']     = '"'+algo+'"'
            say('what time frame?:')
            di['time_frame'] = input('ENTER TIMEFRAME:').upper()
            aldf             = pd.DataFrame([di])
            say('is this selection correct?:')
            print(aldf.set_index('algo'))
            print('============================================================')
            aldf = aldf.T
            print(aldf)
            print('============================================================')
            li = []
            for r in range(len(aldf)):
                li.append(aldf[0][r])
            algo_id = '"'+str(li).join("''").replace("'",'').replace(',','|').upper()
            di['strategy_id'] = '"'+algo_id.replace('"','')+'"'
            print(algo_id)
            


            
            yn = input('cancel selection by typing n or no:').lower()


            if 'n' not in yn:
                confirm = True

say('enter position size:')
di['market_position_size'] = int(input('position size:'))
say('is this a PDT?')
yn = input('enter y or n:').lower()
if 'y' in yn:   
    di['daytrade'] = '"True"'
else:
    di['daytrade'] = '"False"'
payload_path = '/home/brando/anaconda3/lib/python3.7/site-packages/stealing/data/sell_payload.txt'
li = []

to_db(pd.DataFrame([di]).set_index('algo'),'active_algos_checkpoint')
say('saved to local database')
with open(payload_path,'r') as f:
    for l in f.readlines():
        line = l.split(':')[0].replace('"','').replace(' ','')
        for key in di.keys():
            print(key)
            print(line)
            if key == line:
                l = '        "'+key +'":'+ str(di[key]) + ',\n'


        print(l)
        li.append(l)
print('change the list')
# TAKE THE COMMA OFF THE LAST LINE OR IT WILL FUCK THE JSON UP !
print(li[-2])

li[-2] = li[-2].replace(',','')
print(li[-2])

with open('payload.txt','w') as f:
    for line in li:
        f.writelines(line)


shutil.move("payload.txt",'payload.json')
os.system('gedit payload.json')
say('generating alert ID')
with open('alert_name.txt','w') as f:
    f.write(algo_id.replace('"','').replace(' ',''))
os.system('gedit alert_name.txt')

say('generating webhook payload')

os.system('')
say('yey')

#gedit tradingview_webhook_payload_format.json

# MAKE A DATAFRAME TO LOG ALGO
df              = pd.DataFrame([di])
df['datetime']  = str(datetime.now()).split('.')[0]
df['status'  ]  = 'ACTIVATED'
df['experation']= str(datetime.now() + pd.Timedelta(days=30)).split('.')[0]
df              = df.set_index('datetime')
print(df) 
say('put risk_reward Metrics into slot')

pd.set_option('display.max_columns',None)
metrics = ['net_profit','total_closed','percent_profitable','profit_factor','max_drawdown','avg_trade','avg_bars']
cnt = 1
for m in metrics:
    print(m.upper(),'(',cnt ,'of 7 )')
    cnt   += 1
    df[m]  = input(f'enter {m}')
    print('=================================================')
    print(df.T)

    
df['variables']   = input('ADD TRADINGVIEW variables HERE:')
DB_ADDRESS        = 'postgresql://postgres:password1234@database-3-instance-1.ckkftjkepe2f.us-east-2.rds.amazonaws.com'


print(df)
# save to local database for redundancy
try:
    to_db(df,'activated_algos')#,DB_ADDRESS)
except Exception as e:
    print('could not save to local dtabase')
    print(e)

to_db(df,'activated_algos',DB_ADDRESS)
