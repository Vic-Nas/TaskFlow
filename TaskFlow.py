#!/usr/bin/env python3

import os
import sys
import platform
from imports.utils import alert

def minimizeConsole():
    """Minimize or hide console window depending on OS"""
    system = platform.system()
    if system == "Windows":
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            # 6 = minimize, 0 = hide completely
            ctypes.windll.user32.ShowWindow(hwnd, 6)  
    else:
        # On Linux/macOS, cannot programmatically minimize most terminals
        # Best option: detach from terminal
        try:
            if sys.stdin and sys.stdin.isatty():
                sys.stdin.close()
            if sys.stdout and sys.stdout.isatty():
                sys.stdout.close()
            if sys.stderr and sys.stderr.isatty():
                sys.stderr.close()
        except Exception:
            pass

def ensureAdminScript():
    """Elevation when running as .py script"""
    system = platform.system()
    if system == "Windows":
        import ctypes
        try:
            isAdmin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            isAdmin = False
        if not isAdmin:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    else:  # Linux / macOS
        if os.geteuid() != 0:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

def ensureAdminExecutable():
    """Elevation when running as compiled executable"""
    system = platform.system()
    if system == "Windows":
        import ctypes
        try:
            isAdmin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            isAdmin = False
        if not isAdmin:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1
            )
            sys.exit()
    else:  # Linux / macOS
        if os.geteuid() != 0:
            exePath = os.path.abspath(sys.executable)
            try:
                os.execvp("pkexec", ["pkexec", exePath] + sys.argv[1:])
            except FileNotFoundError:
                os.execvp("sudo", ["sudo", exePath] + sys.argv[1:])

# Minimize/hide console early
minimizeConsole()

# Detect if running as script or executable
fileName = os.path.basename(sys.argv[0])

if not fileName.lower().endswith('.py'):
    ensureAdminExecutable()
    try:
        updateName = "update" + platform.system()
        exec(f"from src.main import {updateName};{updateName}()")
    except Exception as e:
        alert(f"Update unavailable:\n{e}")
else:
    ensureAdminScript()
    message = "Auto update disabled when running with Python.\n"
    message += "You'll have to manually redownload the src folder."
    alert(message)

from src.main import main
main()
