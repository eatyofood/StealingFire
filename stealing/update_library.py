#from time import say 
import os
import pandas as pd
import pretty_errors
from shutil import copyfile

lib_path = '/home/brando/anaconda3/lib/python3.7/site-packages/stealing'
repo_path= '/home/brando/algos/Templates/StealingFire/stealing'

import pyttsx3 
import os

eng = pyttsx3.Engine()
eng.setProperty('rate',150)

def say(thing):
    os.system(f'figlet {thing}')
    print('---------------------------------------------')
    eng.say(thing)
    eng.runAndWait()

def move_file(old,new):
    '''
    tries to copy a file, and if it exists then it will delete the old one 
    '''
    try: 
        copyfile(old,new)
    except:
        try:
            os.remove(old)
            os.replace(old,new)
        except BaseException as b:
            print(b)

say('good morning brandon ')

say("let me know if you would like to update the repo")
print('Update the Repo?')
yn = input("TYPE 'update':")
if yn == 'update':
    
    # i cant figure out how to update the repository 
    #say('enter commit flag')
    #com_mes = input('Log Message:')
    #command = os.system('git add .')
    #import subprocess
    #p = subprocess.Popen(command, cwd=repo_path)
    #p.wait()
    #os.system(f'git commit -m "{com_mes}"')

    libdir = os.listdir(lib_path)
    repodir= os.listdir(repo_path)
    print(pd.DataFrame(libdir,columns=['Library Directory']))
    #print(pd.DataFrame(repodir,columns=['Template Directory']))
    
    for file in libdir: 
        old = lib_path + '/' + file
        new = repo_path + '/' + file
        print('MOVE:\n',old,'TO:\n',new)
        try: 
            copyfile(old,new)
        except:
            try:
                os.remove(old)
                os.replace(old,new)
            except BaseException as b:
                print(b)
# UPDATE THE ODDBALL NOTEBOOKS AS WELL
# dropzone
file = 'Daily_Diggs.ipynb'
old = '/home/brando/algos/Develop/DataBase/' + file
new = repo_path + '/' + file 
move_file(old,new)
# backtest
file = 'Back_Test_Engine.ipynb'
old = '/home/brando/algos/Research/ProjectReports/' + file
new = repo_path + '/' + file 
move_file(old,new)

path = '/home/brando/algos/Research/ProjectReports/'

say('files moved to template')

say('cloud backup directory')
print('GIT DIRECTORY')
print('/home/brando/algos/Templates/StealingFire') 
import config
print('git access token:\n',config.git_access_token)
say('update the log:')
os.system('libreoffice /home/brando/algos/project_diary.ods')
