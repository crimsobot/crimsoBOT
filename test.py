import os
from config import TOKEN

# root directory for bot
root_dir = os.path.dirname(__file__) #<-- absolute dir the script is in

print(TOKEN)
print(root_dir)
os.execl("C:/Windows/System32/cmd.exe", "/k",'"D:/Python36/python.exe "'+root_dir+'/bot.py"')