#from time import say 
import os
import pandas as pd
import pretty_errors
from shutil import copyfile
from stealing.time import say
lib_path = '/home/brand/anaconda3/lib/python3.7/site-packages/stealing/'
repo_path= '/home/brand/hyperDrive/Templates/StealingFire/stealing/'

import pyttsx3 
import os

eng = pyttsx3.Engine()
eng.setProperty('rate',150)
from datetime import datetime
import os 

def update_version(title=None,version_path=None):
    if version_path == None:
        version_path = 'version.py'
    else:
        version_path = version_path + '/version.py' 

    
    if not os.path.exists(version_path):
        with open(version_path,'w') as f :
            print('CREATING VERSION>>>1.0.0')
            f.write('version = 1.0')
            v = 1.0


    else:
        from version import version
        v  = version
        print('PACKAGE VERSION:',v)
        v = v+0.1
        print('CURRENT VERSION',v)
        with open(version_path,'w') as f:
            f.write('version = '+str(v))

    now    = str(datetime.now()).split('.')[0]
    version=  ' Version=' + str(v) + now  
    print(version)

    if title == None:
        heading= '# ' + input('ENTER A TITLE:')
    else:
        heading= '# ' + title 
        
    header = heading #+ version
    print('HEADER: ',header)

    body   = '- '+input('NOTES ABOUT UPDATE   : -')

    payload = header + '\n'  + '## ' + version + '\n' + body + '\n'

    print(payload)

    with open('log.md','a') as f:
        f.write(payload) 

    os.system('xdg-open log.md')
    #with open('log.md','a') as f:
        
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
        old = lib_path + file
        new = repo_path+ file
        print('MOVE:',old,'\nTO:',new)
        try: 
            copyfile(old,new)
        except:
            try:
                os.remove(old)
                os.replace(old,new)
            except BaseException as b:
                print(b)

say('global library files moved')
# UPDATE THE ODDBALL NOTEBOOKS AS WELL

#path = '/home/brando/algos/Research/ProjectReports/'
#
#say('files moved to template')
#
#say('cloud backup directory')
#print('GIT DIRECTORY')
#print('/home/brando/algos/Templates/StealingFire') 
#import config
#print('git access token:\n',config.git_access_token)
#say('update the log:')
#os.system('libreoffice /home/brando/algos/project_diary.ods')


# UPDATE STEALING FIRE
say('stealing fire')
say('git message')
message  = input('GIT MESSAGE:')

#UPDATE VERSION 
update_version(title=message)


repo_path= '/home/brand/hyperDrive/Templates/StealingFire'
comands = [
    f'(cd {repo_path}; git add .)',
    f'(cd {repo_path}; git status)',
    f"(cd {repo_path}; git commit -m '{message}')",

]
for c in comands:
    print(c)
    os.system(c)

#say('good morning brandon ')

say("cloud backup?") 

print('Update the Repo?')
yn = input("TYPE [update|UPDATE]:").lower()
if yn == 'update':

    GITKEY = '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'
    print('git access token:\n',GITKEY)

    os.system(f'(cd {repo_path}; git push origin main)')




# UPDATE ROUTINE & SCHEDULE APPS 
say('do you want to update the routine apps?')
yn = input('update routine app? type [y/n]:').lower()
if yn == 'y':
    say('git message')
    message  = input('GIT MESSAGE:')
    repo_path= '/home/brand/hyperDrive/RoutineApp'
    comands = [
        f'(cd {repo_path}; git add .)',
        f'(cd {repo_path}; git status)',
        f"(cd {repo_path}; git commit -m '{message}')",

    ]

    #run commands
    for c in comands:
        print(c)
        os.system(c)


    say("cloud backup?") 

    print('Update the Repo?')
    yn = input('type [update|UPDATE]:').lower()
    if yn == 'update':

        GITKEY = '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'
        print('git access token:\n',GITKEY)
        print('')
        os.system(f'(cd {repo_path}; git push origin main)')

