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
