import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
import urllib.request
import ctypes
import tkinter as tk
from tkinter import ttk
import threading


# --------------------
# Admin rights check
# --------------------
def runAsAdmin():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
    except:
        pass
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()


# --------------------
# UI Class
# --------------------
class InstallUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TaskFlow Installer")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"500x300+{x}+{y}")

        self.setupUI()

    def setupUI(self):
        mainFrame = ttk.Frame(self.root, padding="20")
        mainFrame.pack(fill=tk.BOTH, expand=True)

        titleLabel = ttk.Label(mainFrame, text="Installing TaskFlow", font=("Arial", 14, "bold"))
        titleLabel.pack(pady=(0, 20))

        self.statusLabel = ttk.Label(mainFrame, text="Preparing installation...", font=("Arial", 10))
        self.statusLabel.pack(pady=(0, 10))

        self.progressBar = ttk.Progressbar(mainFrame, mode='determinate', length=400)
        self.progressBar.pack(pady=(0, 20))

        self.detailsText = tk.Text(mainFrame, height=8, width=60, wrap=tk.WORD, state=tk.DISABLED)
        self.detailsText.pack()

    def updateStatus(self, text, progressValue=None):
        self.statusLabel.config(text=text)
        if progressValue is not None:
            self.progressBar['value'] = progressValue
        self.root.update()

    def addDetail(self, text):
        self.detailsText.config(state=tk.NORMAL)
        self.detailsText.insert(tk.END, text + "\n")
        self.detailsText.see(tk.END)
        self.detailsText.config(state=tk.DISABLED)
        self.root.update()


# --------------------
# Installer helpers
# --------------------
def createDesktopShortcut(exePath, ui):
    try:
        desktop = Path.home() / "Desktop"
        shortcutPath = desktop / "TaskFlow.lnk"
        psCommand = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcutPath}")
$Shortcut.TargetPath = "{exePath}"
$Shortcut.WorkingDirectory = "{exePath.parent}"
$Shortcut.Save()
'''
        subprocess.run(["powershell", "-Command", psCommand], capture_output=True, text=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        ui.addDetail("Desktop shortcut created.")
    except Exception as e:
        ui.addDetail(f"Shortcut creation error: {e}")


def createUninstaller(installPath, ui):
    try:
        batchContent = f'''@echo off
echo TaskFlow Uninstaller
net session >nul 2>&1
if not %errorLevel% == 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)
if exist "{installPath}" (
    rmdir /s /q "{installPath}"
)
if exist "%USERPROFILE%\\Desktop\\TaskFlow.lnk" (
    del "%USERPROFILE%\\Desktop\\TaskFlow.lnk"
)
pause
'''
        batchPath = installPath / "uninstall.bat"
        with open(batchPath, 'w') as f:
            f.write(batchContent)
        ui.addDetail("Uninstaller created.")
    except Exception as e:
        ui.addDetail(f"Uninstaller creation error: {e}")


def downloadWithProgress(url, destination, ui):
    try:
        response = urllib.request.urlopen(url)
        totalSize = int(response.headers.get('Content-Length', 0))
        downloaded = 0
        chunkSize = 8192
        with open(destination, 'wb') as f:
            while True:
                chunk = response.read(chunkSize)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if totalSize > 0:
                    percent = (downloaded / totalSize) * 100
                    ui.updateStatus(f"Downloading... {percent:.1f}%", percent * 0.5)
        ui.addDetail("Download completed.")
        return True
    except Exception as e:
        ui.addDetail(f"Download error: {e}")
        return False


# --------------------
# Installation process
# --------------------
def runInstallation(ui):
    tempDir = tempfile.mkdtemp()
    try:
        zipUrl = "https://github.com/Vic-Nas/TaskFlow/raw/main/compiled/win/TaskFlow.zip"
        zipPath = Path(tempDir) / "TaskFlow.zip"
        extractPath = Path(tempDir) / "extracted"

        ui.updateStatus("Downloading package...", 0)
        if not downloadWithProgress(zipUrl, zipPath, ui):
            return

        ui.updateStatus("Extracting files...", 60)
        extractPath.mkdir()
        with zipfile.ZipFile(zipPath, 'r') as zipRef:
            zipRef.extractall(extractPath)
        ui.addDetail(f"Extracted {len(list(extractPath.rglob('*')))} items.")

        ui.updateStatus("Installing...", 80)
        programFiles = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files'))
        installDir = programFiles / "TaskFlow"
        if installDir.exists():
            shutil.rmtree(installDir)
        shutil.copytree(extractPath, installDir)
        ui.addDetail(f"Installed to: {installDir}")

        exeFile = None
        for candidate in [installDir / "update.exe", installDir / "TaskFlow.exe"]:
            if candidate.exists():
                exeFile = candidate
                break
        if not exeFile:
            exes = list(installDir.glob("*.exe"))
            if exes:
                exeFile = exes[0]

        if exeFile:
            createDesktopShortcut(exeFile, ui)
            createUninstaller(installDir, ui)
            ui.addDetail("Installation completed successfully!")
        else:
            ui.addDetail("No executable found after installation.")

        ui.updateStatus("Done!", 100)

    finally:
        shutil.rmtree(tempDir, ignore_errors=True)


# --------------------
# Main
# --------------------
def main():
    runAsAdmin()
    ui = InstallUI()
    threading.Thread(target=runInstallation, args=(ui,), daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
