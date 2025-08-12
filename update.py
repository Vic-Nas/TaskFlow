from imports.settings import getSetting, setSetting
from imports.utils import alert

import sys
import subprocess, os
import tkinter as tk
from tkinter import ttk
import time


class UpdateUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TaskFlow - Update")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (250 // 2)
        self.root.geometry(f"400x250+{x}+{y}")
        
        self.setupUI()
        
    def setupUI(self):
        # Main frame
        mainFrame = ttk.Frame(self.root, padding="20")
        mainFrame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        titleLabel = ttk.Label(mainFrame, text="TaskFlow Update", 
                               font=("Arial", 14, "bold"))
        titleLabel.pack(pady=(0, 20))
        
        # Status label
        self.statusLabel = ttk.Label(mainFrame, text="Preparing update...", 
                                     font=("Arial", 10))
        self.statusLabel.pack(pady=(0, 10))
        
        # Progress bar
        self.progressBar = ttk.Progressbar(mainFrame, mode='determinate', length=300)
        self.progressBar.pack(pady=(0, 20))
        
        # Details text area
        self.detailsText = tk.Text(mainFrame, height=6, width=45, 
                                   wrap=tk.WORD, state=tk.DISABLED)
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


def downloadWithProgress(url, filename, ui):
    """Downloads a file with progress bar"""
    import urllib.request
    
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


def updateWindows():
    import urllib.request
    import json
    import shutil
    import tempfile
    
    newDetails = {}
        
    try:
        # Get local version
        localVersion = getSetting("version")
        
        # Get repository version
        repoUrl = "https://raw.githubusercontent.com/Vic-Nas/TaskFlow/main/data/settings.json"
        
        with urllib.request.urlopen(repoUrl, timeout=10) as response:
            repoSettings = json.loads(response.read().decode('utf-8'))
        
        repoVersion = repoSettings.get("version")
        newDetails = repoSettings.get("new", {})
        
        # Ensure repoVersion is an integer
        if repoVersion is None:
            return
        
        try:
            repoVersion = int(repoVersion)
        except (ValueError, TypeError):
            return
        
        # Check if update is needed
        if localVersion == repoVersion:
            return
        
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception):
        return
    
    # Show update details and confirm
    fixes = "\n".join(newDetails.get("fix", []))
    added = "\n".join(newDetails.get("add", []))
    
    # Use your existing alert function for confirmation
    alert([f"{fixes}", f"{added}"], title="Confirm update:", headings=["Fixes", "Added"])
    
    
    # Create and show update UI
    ui = UpdateUI()
    
    try:
        ui.addDetail("Starting update process...")
        ui.updateStatus("Initializing...", 0)
        
        # Get the actual executable path
        if getattr(sys, 'frozen', False):
            currentExePath = sys.executable
        else:
            currentExePath = os.path.abspath(sys.argv[0])
        
        ui.addDetail(f"Current file: {currentExePath}")
        
        # Create backup
        ui.updateStatus("Creating backup...", 10)
        backupPath = currentExePath + ".backup"
        try:
            shutil.copy2(currentExePath, backupPath)
            ui.addDetail(f"Backup created: {backupPath}")
        except Exception as e:
            ui.addDetail(f"Warning: Could not create backup: {str(e)}")
        
        # Download new version
        ui.updateStatus("Downloading new version...", 20)
        downloadUrl = "https://github.com/Vic-Nas/TaskFlow/raw/main/build/dist/TaskFlow.exe"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as tempFile:
            tempPath = tempFile.name
        
        ui.addDetail(f"Downloading to: {tempPath}")
        
        # Download with progress
        downloadSuccess = downloadWithProgress(downloadUrl, tempPath, ui)
        
        if not downloadSuccess:
            try:
                os.unlink(tempPath)
            except:
                pass
            ui.addDetail("Update failed: Download error")
            return
        
        ui.updateStatus("Download completed", 60)
        ui.addDetail("Download completed successfully")
        
        # Verify download
        ui.updateStatus("Verifying download...", 70)
        if not os.path.exists(tempPath) or os.path.getsize(tempPath) < 1024:
            ui.addDetail("Error: Downloaded file is invalid")
            return
        
        ui.addDetail(f"Downloaded file size: {os.path.getsize(tempPath)} bytes")
        
        # Replace current executable
        ui.updateStatus("Installing update...", 80)
        ui.addDetail("Replacing executable...")
        
        try:
            # Windows specific replacement
            ui.updateStatus("Preparing file replacement...", 82)
            tempCurrentPath = currentExePath + ".old"
            if os.path.exists(tempCurrentPath):
                os.unlink(tempCurrentPath)
            
            ui.updateStatus("Renaming current executable...", 85)
            os.rename(currentExePath, tempCurrentPath)
            ui.addDetail("Current executable renamed")
            
            ui.updateStatus("Installing new executable...", 87)
            shutil.move(tempPath, currentExePath)
            ui.addDetail("New executable installed")
            
            # Clean up old file
            ui.updateStatus("Cleaning up...", 89)
            try:
                os.unlink(tempCurrentPath)
                ui.addDetail("Old file cleaned up")
            except:
                pass
                
            ui.addDetail("Executable replaced successfully")
            
        except Exception as e:
            ui.addDetail(f"Error replacing executable: {str(e)}")
            # Try to restore backup
            if os.path.exists(backupPath):
                try:
                    shutil.copy2(backupPath, currentExePath)
                    ui.addDetail("Backup restored")
                except:
                    ui.addDetail("Failed to restore backup")
            return
        
        # Update version setting
        ui.updateStatus("Finalizing...", 90)
        try:
            setSetting("version", repoVersion)
            ui.addDetail(f"Version updated to: {repoVersion}")
        except Exception as e:
            ui.addDetail(f"Warning: Could not update version setting: {str(e)}")
        
        ui.updateStatus("Update completed! Launching...", 100)
        ui.addDetail("Update completed successfully!")
        ui.addDetail("Launching TaskFlow...")
        
        time.sleep(1)
        
        # Launch TaskFlow and exit
        try:
            subprocess.Popen([currentExePath], shell=False, cwd=os.path.dirname(currentExePath))
            ui.addDetail("TaskFlow launched successfully")
            time.sleep(0.5)
            ui.root.quit()
            sys.exit(0)
            
        except Exception as e:
            ui.addDetail(f"Error launching TaskFlow: {str(e)}")
            time.sleep(2)
            ui.root.quit()
        
    except Exception as e:
        ui.addDetail(f"Update failed: {str(e)}")
        ui.updateStatus("Update failed", 0)
        time.sleep(2)
        ui.root.quit()
    
    # Show UI during process
    ui.root.mainloop()
    
    
updateWindows()