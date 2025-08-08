#!/usr/bin/env python3

import os
import sys
import platform
from pymsgbox import alert

# Check / elevate privileges
def ensure_admin():
    system = platform.system()
    if system == "Windows":
        import ctypes
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False
        if not is_admin:
            # Relaunch with UAC elevation
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    else:  # Linux or macOS
        if os.geteuid() != 0:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

# Apply the check before running anything
ensure_admin()

from src.main import main

filename = os.path.basename(sys.argv[0])

if not filename.lower().endswith('.py'):
    try:
        name = "update" + platform.system()
        exec(f"from src.main import {name};{name}()")
    except Exception as e:
        alert(f"Update unavailable:\n{e}")
else:
    message = "Auto update disabled when running with Python.\n"
    message += "You'll have to manually redownload the src folder."
    alert(message)

main()