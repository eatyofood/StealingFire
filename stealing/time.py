import pyttsx3 
import os

eng = pyttsx3.Engine()
eng.setProperty('rate',150)

def say(thing):
    os.system(f'figlet {thing}')
    print('---------------------------------------------')
    eng.say(thing)
    eng.runAndWait()
say('good morning brandon ')


import sqlalchemy as sql
import pandas as pd


#database_function - V3.1
def to_db(df,table_name,db='log',addr= 'postgresql://postgres:password@localhost/'):
    eng = sql.create_engine(addr+db)
    con = eng.connect()
    print(df)
    tables = eng.table_names()
    if table_name in tables:
        print('yeap table already exists...')
        
        
        a=pd.read_sql_query(f'select * from "{table_name}"',con=eng)
        try:
            a = a.set_index(df.index.name)
        except Exception as e:
            print('could not set index for some reason:',e)
        print(a)
        
        #if you have issues here add an if statment to the set index thing. 
        missing_columns = [col for col in df.columns if col not in a.columns]
        print(f'missing columns :',missing_columns)
        
        if len(missing_columns) > 0:
            for col in missing_columns:
                print('attempting to add:',col)
                con.execute(f'ALTER TABLE {table_name} ADD COLUMN {col} TEXT NULL;')#.format(table_name,col))
                
    df.to_sql(table_name,con,if_exists='append')
    con.close()
    
    print(f'databaselog:{table_name}\n UPDATED!')


def from_db(table_name,db_name,index_name=None):
    try:
        eng = sql.create_engine(db_name)

        # List tables 
        con = eng.connect()
        tables = eng.table_names()
        print('CONNECTED: TO CLOUD')
    except:
        eng = sql.create_engine(f'postgresql://postgres:password@localhost/{db_name}')

        # List tables 
        con = eng.connect()
        tables = eng.table_names()
        print('connected to local database')
        
    print(tables)
    if table_name in tables:
        #Load Data From The Base
        a=pd.read_sql_query(f'select * from {table_name}',con=eng)#.set_index('date')
        if index_name != None:
            if index_name in a.columns:
                a = a.set_index(index_name)
    return a
