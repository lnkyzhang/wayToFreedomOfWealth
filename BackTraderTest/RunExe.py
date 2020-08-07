import subprocess
import sys
import os

import win32event
import win32process

'''

def OpenProcess0(procPath, param = ""):
    commandline = "\"" + procPath + "\" " + param
    handle = win32process.CreateProcess(None,
	       commandline, None, None, 0,
	       win32process.CREATE_NO_WINDOW,
	        None ,
	        None,
	        win32process.STARTUPINFO(wShowWindow = SW_HIDE))
    rc = win32event.WaitForSingleObject(handle[0], 10000)
    print(rc)
'''

def OpenAndHide():


    IS_WIN32 = 'win32' in str(sys.platform).lower()

    if IS_WIN32:
        startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags = subprocess.CREATE_NEW_CONSOLE | subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        p = subprocess.Popen(r"cmd C:\Users\DuoWei\Desktop\vnc\jsmpeg-vnc.exe desktop", startupinfo=startupinfo)


if __name__ == '__main__':


    os.chdir(r"C:\Users\DuoWei\Desktop\vnc")

    os.system(r"C:\Users\DuoWei\Desktop\vnc\jsmpeg-vnc.exe desktop")

    # OpenAndHide()
