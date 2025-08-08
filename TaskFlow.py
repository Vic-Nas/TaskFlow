#!/usr/bin/env python3

from src.main import main
import platform
from pymsgbox import alert

try:
    name = "update" + platform.system()
    exec(f"from src.main import {name};{name}()")
except Exception as e:
    alert(f"Update unavailabale:\n{e}")

main()