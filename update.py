import sys
import os
import ctypes
import urllib.request
from imports.settings import getSetting, setSetting
from imports.utils import alert
import threading
import json
import shutil
import tempfile
import tkinter as tk
from tkinter import ttk
import subprocess
import time

# --------------------
# Admin rights check
# --------------------
def runAsAdmin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    else:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit()

runAsAdmin()


# --------------------
# Update UI
# --------------------
class UpdateUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TaskFlow - Update")
        self.root.geometry("400x250")
        self.root.resizable(False, False)

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (250 // 2)
        self.root.geometry(f"400x250+{x}+{y}")

        self.setupUI()

    def setupUI(self):
        mainFrame = ttk.Frame(self.root, padding="20")
        mainFrame.pack(fill=tk.BOTH, expand=True)

        titleLabel = ttk.Label(mainFrame, text="TaskFlow Update", font=("Arial", 14, "bold"))
        titleLabel.pack(pady=(0, 20))

        self.statusLabel = ttk.Label(mainFrame, text="Preparing update...", font=("Arial", 10))
        self.statusLabel.pack(pady=(0, 10))

        self.progressBar = ttk.Progressbar(mainFrame, mode='determinate', length=300)
        self.progressBar.pack(pady=(0, 20))

        self.detailsText = tk.Text(mainFrame, height=6, width=45, wrap=tk.WORD, state=tk.DISABLED)
        self.detailsText.pack(pady=(0, 10))

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
# Download helper
# --------------------
def downloadWithProgress(url, filename, ui):
    def progressHook(blockNum, blockSize, totalSize):
        if totalSize > 0:
            downloaded = blockNum * blockSize
            percent = min(100, (downloaded * 100) // totalSize)
            ui.updateStatus(f"Downloading... {percent}%", 20 + (percent * 0.4))
    try:
        urllib.request.urlretrieve(url, filename, progressHook)
        return True
    except Exception as e:
        ui.addDetail(f"Download error: {str(e)}")
        return False


# --------------------
# Actual update process
# --------------------
def runUpdateProcess(ui, exePath, repoVersion, downloadUrl):
    try:
        ui.addDetail("Starting update process...")
        ui.updateStatus("Initializing...", 0)

        # Backup
        backupPath = exePath + ".backup"
        try:
            shutil.copy2(exePath, backupPath)
            ui.addDetail(f"Backup created: {backupPath}")
        except Exception as e:
            ui.addDetail(f"Warning: Could not create backup: {str(e)}")

        # Download
        ui.updateStatus("Downloading new version...", 20)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as tempFile:
            tempPath = tempFile.name

        downloadSuccess = downloadWithProgress(downloadUrl, tempPath, ui)
        if not downloadSuccess:
            try:
                os.unlink(tempPath)
            except:
                pass
            ui.addDetail("Update failed: Download error")
            return

        # Replace exe
        ui.updateStatus("Installing update...", 80)
        tempOldPath = exePath + ".old"
        if os.path.exists(tempOldPath):
            os.unlink(tempOldPath)
        os.rename(exePath, tempOldPath)
        shutil.move(tempPath, exePath)
        try:
            os.unlink(tempOldPath)
        except:
            pass

        setSetting("version", repoVersion)
        ui.addDetail(f"Version updated to: {repoVersion}")

        ui.updateStatus("Update completed! Launching...", 100)
        ui.root.after(1000, lambda: launchTaskFlow(ui, exePath))

    except Exception as e:
        ui.addDetail(f"Update failed: {str(e)}")
        ui.updateStatus("Update failed", 0)


# --------------------
# Launch TaskFlow
# --------------------
def launchTaskFlow(ui, exePath):
    try:
        subprocess.Popen([exePath], shell=False, cwd=os.path.dirname(exePath))
        ui.addDetail("TaskFlow launched successfully")
    except Exception as e:
        ui.addDetail(f"Error launching TaskFlow: {str(e)}")
    finally:
        ui.root.destroy()


# --------------------
# Main updater logic
# --------------------
def updateWindows():
    try:
        localVersion = getSetting("version")
        repoUrl = "https://raw.githubusercontent.com/Vic-Nas/TaskFlow/main/data/settings.json"
        with urllib.request.urlopen(repoUrl, timeout=10) as response:
            repoSettings = json.loads(response.read().decode('utf-8'))
        repoVersion = int(repoSettings.get("version"))
        newDetails = repoSettings.get("new", {})

        if localVersion == repoVersion:
            subprocess.Popen([os.path.abspath("TaskFlow.exe")], shell=False)
            return

        fixes = "\n".join(newDetails.get("fix", []))
        added = "\n".join(newDetails.get("add", []))
        alert([fixes, added], title="Confirm update:", headings=["Fixes", "Added"])

        # Corrected download path
        downloadUrl = "https://github.com/Vic-Nas/TaskFlow/raw/main/build/dist/TaskFlow/TaskFlow.exe"

        # Pre-check: make sure file exists
        try:
            with urllib.request.urlopen(downloadUrl) as checkResp:
                if checkResp.status != 200:
                    raise Exception(f"Server returned {checkResp.status}")
        except Exception as e:
            print(f"Update file check failed: {e}")
            return

        exePath = os.path.abspath("TaskFlow.exe")
        ui = UpdateUI()
        threading.Thread(target=runUpdateProcess, args=(ui, exePath, repoVersion, downloadUrl), daemon=True).start()
        ui.root.mainloop()

    except Exception as e:
        print(f"Update check failed: {e}")
        subprocess.Popen([os.path.abspath("TaskFlow.exe")], shell=False)


try:
    updateWindows()
except:
    alert("Update failed. Consider adding installation\nfolder to antivirus exclusion path.")