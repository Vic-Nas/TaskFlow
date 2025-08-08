#!/usr/bin/env python3

from src.main import main
import platform
from pymsgbox import alert
import os, sys


filename = os.path.basename(sys.argv[0])

if not filename.lower().endswith('.py'):
    try:
        name = "update" + platform.system()
        exec(f"from src.main import {name};{name}()")
    except Exception as e:
        alert(f"Update unavailabale:\n{e}")
else:
    message = "Auto update disabled when using python.\n"
    message += "You'll have to do redownload the src folder."
    alert(message)

main()