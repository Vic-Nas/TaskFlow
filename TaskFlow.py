#!/usr/bin/env python3

import os
import sys
import platform
from imports.utils import alert

def minimizeConsole():
    """Minimize only the console window on Windows, detach on Linux/macOS"""
    system = platform.system()
    if system == "Windows":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd != 0:
            # 6 = SW_MINIMIZE, affects only the console window
            user32.ShowWindow(hwnd, 6)
    else:
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
        exec(f"from imports.utils import {updateName};{updateName}()")
    except Exception as e:
        alert(f"Update unavailable:\n{e}")
else:
    ensureAdminScript()
    message = "Auto update disabled when running with Python.\n"
    message += "You'll have to manually redownload the src folder."
    alert(message)

import traceback

logFilePath = "logs.txt"
maxRows = 1000

class LogRedirector:
    def __init__(self, filePath, maxLines):
        self.filePath = filePath
        self.maxLines = maxLines

    def write(self, message):
        if message.strip() == "":
            return
        lines = self.readLogLines()
        lines.append(message)
        if len(lines) > self.maxLines:
            lines = lines[-self.maxLines:]
        self.writeLogLines(lines)

    def flush(self):
        pass  # Needed for compatibility

    def readLogLines(self):
        try:
            with open(self.filePath, mode = "r", encoding='utf-8') as f:
                return f.readlines()
        except FileNotFoundError:
            return []

    def writeLogLines(self, lines):
        with open(self.filePath, mode = "w", encoding='utf-8') as f:
            f.writelines(lines)

def globalExceptionHandler(excType, excValue, excTraceback):
    error = "".join(traceback.format_exception(excType, excValue, excTraceback))
    with open(logFilePath, mode = "a", encoding='utf-8') as f:
        f.write("\nException captured:\n")
        f.write(error)
    print("Exception logged, check logs.txt")

sys.stdout = LogRedirector(logFilePath, maxRows)
sys.stderr = LogRedirector(logFilePath, maxRows)
sys.excepthook = globalExceptionHandler

from imports.mail import sendFeedBackMail
from imports.settings import getSetting

try:
    import src.main
except:
    traceback.print_exc()
    alert("Critical problem in the app.\nLog will be sent.")
    sendFeedBackMail(getSetting("email"), "Critical problem", "logs.txt")
