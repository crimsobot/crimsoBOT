import os
from config import TOKEN

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

print(TOKEN)
print(PROJECT_DIR)
os.execl("C:/Windows/System32/cmd.exe", "/k",'"D:/Python36/python.exe "'+PROJECT_DIR+'/bot.py"')