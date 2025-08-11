#!/usr/bin/env python3

import os
import sys
import platform
from imports.utils import alert

import traceback, subprocess

class ConsoleWindowManager:
    """Cross-platform console window manager for minimize/restore operations"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.isWindows = self.platform == 'windows'
        self.isLinux = self.platform == 'linux'
        self.isMacOS = self.platform == 'darwin'
    
    def minimizeWindow(self):
        """Minimize the console window to taskbar/dock"""
        try:
            if self.isWindows:
                self._minimizeWindowsConsole()
            elif self.isLinux:
                self._minimizeLinuxTerminal()
            elif self.isMacOS:
                self._minimizeMacOSTerminal()
            else:
                print(f"Platform {self.platform} not supported for window minimization")
                return False
            return True
        except Exception as e:
            print(f"Error minimizing window: {e}")
            return False
    

    
    def _minimizeWindowsConsole(self):
        """Windows-specific console minimization"""
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            # SW_MINIMIZE = 6
            ctypes.windll.user32.ShowWindow(hwnd, 6)
    

    
    def _minimizeLinuxTerminal(self):
        """Linux-specific terminal minimization using wmctrl"""
        try:
            # Try to minimize using wmctrl (needs to be installed)
            subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,hidden'], 
                         check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: try with xdotool
            try:
                subprocess.run(['xdotool', 'getactivewindow', 'windowminimize'], 
                             check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Neither wmctrl nor xdotool found. Please install one of them:")
                print("Ubuntu/Debian: sudo apt-get install wmctrl")
                print("Or: sudo apt-get install xdotool")
                raise Exception("Required tools not available")
    

    
    def _minimizeMacOSTerminal(self):
        """macOS-specific terminal minimization using AppleScript"""
        script = '''
        tell application "System Events"
            tell process "Terminal"
                set frontmost to true
                click button 2 of window 1
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
    

    
    def hideFromTaskbar(self):
        """Hide application from taskbar (Windows only)"""
        if self.isWindows:
            try:
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd != 0:
                    # Hide from taskbar by removing WS_EX_APPWINDOW style
                    ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00000080)
            except Exception as e:
                print(f"Error hiding from taskbar: {e}")
    
    def showInTaskbar(self):
        """Show application in taskbar (Windows only)"""
        if self.isWindows:
            try:
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd != 0:
                    # Show in taskbar by adding WS_EX_APPWINDOW style
                    ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x00040000)
            except Exception as e:
                print(f"Error showing in taskbar: {e}")




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
    manager = ConsoleWindowManager()
    manager.minimizeWindow()

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

except SystemExit:
    print("System exited in module main.")

except:
    traceback.print_exc()
    alert("Critical problem in the app.\nLog will be sent.")
    sendFeedBackMail(getSetting("email"), "Critical problem", "logs.txt")