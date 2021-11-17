from datetime import datetime
import os 
version_path = 'version.py'
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
heading= '# ' + input('ENTER A TITLE:')
header = heading #+ version
print('HEADER: ',header)

body   = '- '+input('NOTES ABOUT UPDATE   : -')

payload = header + '\n'  + '## ' + version + '\n' + body + '\n'

print(payload)

with open('log.md','a') as f:
    f.write(payload) 

os.system('xdg-open log.md')
#with open('log.md','a') as f:
    