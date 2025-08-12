
import tkinter, os, sys, subprocess, threading
from tkinter import font as tkfont
from json import load, dump
from pathlib import Path
import requests
from imports.keys import IMGBB_API_KEY, FORM_DATA, FORM_URL



def setSetting(key, val):
    with open(Path("data")/"settings.json") as file:
        setting = load(file)
    setting[key] = val
    with open(Path("data")/"settings.json", "w") as file:
        dump(setting, file, indent = 4)

def getSetting(key):
    with open(Path("data")/"settings.json") as file:
        return load(file)[key]

def updateWindows():
    import urllib.request
    import json
    
    newDetails = {}
    try:
        # Get local version
        localVersion = getSetting("version")
        
        # Get repository version
        repoUrl = "https://raw.githubusercontent.com/Vic-Nas/TaskFlow/main/data/settings.json"
        
        with urllib.request.urlopen(repoUrl, timeout=10) as response:
            repoSettings = json.loads(response.read().decode('utf-8'))
        
        repoVersion = repoSettings.get("version")
        newDetails = repoSettings.get("new")
        
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
    
    fixes = "\n".join(newDetails["fix"])
    added = "\n".join(newDetails["add"])
    
    # Show update confirmation - keeping your original alert function
    confirmUpdate = alert([f"{fixes}", f"{added}"], title="Confirm update:", headings=["Fixes", "Added"])
    
    # If user doesn't confirm, return (adjust this based on what your alert function returns)
    if not confirmUpdate:
        return
    
    # NOW show loading window during the actual update process
    import tkinter as tk
    from tkinter import ttk
    import threading
    import time
    
    # Create loading window
    loadingWindow = tk.Tk()
    loadingWindow.title("TaskFlow Update")
    loadingWindow.geometry("350x120")
    loadingWindow.resizable(False, False)
    
    # Center the window
    loadingWindow.update_idletasks()
    x = (loadingWindow.winfo_screenwidth() // 2) - (350 // 2)
    y = (loadingWindow.winfo_screenheight() // 2) - (120 // 2)
    loadingWindow.geometry(f"350x120+{x}+{y}")
    
    # Disable close button
    loadingWindow.protocol("WM_DELETE_WINDOW", lambda: None)
    
    tk.Label(loadingWindow, text="Updating TaskFlow...", font=("Arial", 12, "bold")).pack(pady=15)
    
    statusLabel = tk.Label(loadingWindow, text="Preparing update...", font=("Arial", 9))
    statusLabel.pack(pady=5)
    
    progressBar = ttk.Progressbar(loadingWindow, mode='indeterminate', length=250)
    progressBar.pack(pady=10)
    progressBar.start()
    
    def updateInBackground():
        """Run the original update logic in background thread"""
        try:
            # Update status
            loadingWindow.after(0, lambda: statusLabel.config(text="Creating directories..."))
            time.sleep(0.5)
            
            tempDir = os.path.abspath("tempUpdate")
            backupDir = os.path.abspath("backup")
            
            # Get the actual executable path (works for both .py and .exe)
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                currentExePath = sys.executable
                appDir = os.path.dirname(currentExePath)
            else:
                # Running as python script
                currentExePath = os.path.abspath(sys.argv[0])
                appDir = os.path.dirname(currentExePath)
            
            exeName = os.path.basename(currentExePath)
            
            # Create temp and backup dirs
            os.makedirs(tempDir, exist_ok=True)
            os.makedirs(backupDir, exist_ok=True)
            
            loadingWindow.after(0, lambda: statusLabel.config(text="Creating update script..."))
            time.sleep(0.5)
            
            # Create batch script FIRST, then update version after successful download
            batScript = f"""@echo off
echo Update started - Local version: {localVersion}, Repository version: {repoVersion} > update.log

echo Creating backup... >> update.log
copy "{currentExePath}" "{backupDir}\\{exeName}.bak" >> update.log 2>&1
if errorlevel 1 (
    echo Backup failed, aborting update >> update.log
    goto :cleanup
)

echo Downloading TaskFlow.exe... >> update.log
powershell -WindowStyle Hidden -Command "try {{ Invoke-WebRequest -Uri 'https://github.com/Vic-Nas/TaskFlow/raw/main/build/dist/TaskFlow/TaskFlow.exe' -OutFile '{tempDir}\\TaskFlow.exe' -TimeoutSec 30 }} catch {{ exit 1 }}" >> update.log 2>&1
if errorlevel 1 (
    echo Download failed >> update.log
    goto :cleanup
)

echo Waiting for app to close... >> update.log
timeout /t 3 /nobreak > nul

echo Installing update... >> update.log
copy /y "{tempDir}\\TaskFlow.exe" "{currentExePath}" >> update.log 2>&1
if errorlevel 1 (
    echo Installation failed, restoring backup >> update.log
    copy /y "{backupDir}\\{exeName}.bak" "{currentExePath}" >> update.log 2>&1
    goto :cleanup
)

echo Update successful, starting application... >> update.log
start "" "{currentExePath}"

:cleanup
echo Cleaning up... >> update.log
if exist "{tempDir}" rmdir /s /q "{tempDir}" >> update.log 2>&1
echo Update finished >> update.log
del "%~0"
"""
            
            batPath = os.path.join(os.path.dirname(currentExePath), "update.bat")
            
            with open(batPath, "w") as batFile:
                batFile.write(batScript)
            
            loadingWindow.after(0, lambda: statusLabel.config(text="Updating version..."))
            time.sleep(0.5)
            
            # Update version only AFTER successful batch creation
            try:
                setSetting("version", repoVersion)
            except:
                pass
            
            loadingWindow.after(0, lambda: statusLabel.config(text="Starting update process..."))
            time.sleep(1)
            
            # Launch batch silently and exit current process
            subprocess.Popen([batPath], cwd=os.path.dirname(currentExePath), creationflags=subprocess.CREATE_NO_WINDOW)
            
            loadingWindow.after(0, lambda: statusLabel.config(text="Restarting TaskFlow..."))
            time.sleep(1)
            
            # Close loading window and exit
            loadingWindow.after(0, loadingWindow.destroy)
            
            # Exit current process to avoid relaunch loop
            sys.exit(0)
            
        except Exception as e:
            loadingWindow.after(0, lambda: statusLabel.config(text=f"Update failed: {str(e)}"))
            time.sleep(2)
            loadingWindow.after(0, loadingWindow.destroy)
    
    # Start update in background thread
    updateThread = threading.Thread(target=updateInBackground, daemon=True)
    updateThread.start()
    
    # Show loading window (this will block until window is destroyed)
    loadingWindow.mainloop()
    

def centerWin(window):
    window.update_idletasks()
    windowWidth = window.winfo_width()
    windowHeight = window.winfo_height()

    if windowWidth <= 1 or windowHeight <= 1:
        geometry = window.geometry()
        if 'x' in geometry and '+' in geometry:
            sizePart = geometry.split('+')[0]
            windowWidth, windowHeight = map(int, sizePart.split('x'))
        else:
            windowWidth, windowHeight = 300, 200

    screenWidth = window.winfo_screenwidth()
    screenHeight = window.winfo_screenheight()

    x = (screenWidth - windowWidth) // 2
    y = (screenHeight - windowHeight) // 2

    window.geometry(f"{windowWidth}x{windowHeight}+{x}+{y}")

def alert(content, headings = None, bg = "#222", fg = "#fff", title = "Info", sectionBg = "#333", sectionFg = "#0ff"):
    # Create root but keep it hidden
    root = tkinter.Tk()
    root.withdraw()
    
    win = tkinter.Toplevel(root)
    win.title(title)
    win.configure(bg = bg)
    win.resizable(False, False)
    
    sectionFont = tkfont.Font(family = "Helvetica", size = 12, weight = "bold")
    textFont = tkfont.Font(family = "Helvetica", size = 10)

    if isinstance(content, str):
        tkinter.Label(win, text = content, bg = bg, fg = fg, font = textFont, justify = "left", wraplength = 400).pack(padx = 20, pady = 20)
    elif isinstance(content, list):
        for i, txt in enumerate(content):
            if headings and i < len(headings):
                secTitle = headings[i]
            else:
                secTitle = f"Section {i + 1}:"
            
            tkinter.Label(win, text = secTitle, bg = sectionBg, fg = sectionFg, font = sectionFont, anchor = "w").pack(fill = "x", padx = 10, pady = (10, 0))
            tkinter.Label(win, text = txt, bg = bg, fg = fg, font = textFont, justify = "left", wraplength = 400).pack(padx = 20, pady = 5)
    else:
        raise TypeError("content must be a string or a list of strings")
    
    def closeWin(event = None):
        win.destroy()
        root.quit()  # ⬅ force sortie de mainloop
    
    okButton = tkinter.Button(win, text = "OK", command = closeWin, bg = "#555", fg = "#fff", activebackground = "#777", relief = "flat")
    okButton.pack(pady = 10)

    win.bind("<Return>", closeWin)  # ⬅ Enter valide aussi
    
    centerWin(win)
    win.grab_set()
    root.mainloop() 
    root.destroy() 
    
    

def uploadImageToImgbb(imagePath):
    with open(imagePath, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        response = requests.post(url, files={"image": file}, data={"key": IMGBB_API_KEY})
        if response.status_code == 200:
            jsonResp = response.json()
            if jsonResp['success']:
                return jsonResp['data']['url']  # direct image link
            else:
                raise Exception("Upload failed: " + str(jsonResp))
        else:
            raise Exception(f"HTTP Error: {response.status_code}")

def submitForm(description: str, xCoord: float, yCoord: float, imagePaths: tuple[str]) -> bool:
    links = []
    for imagePath in imagePaths:
        imageLink = uploadImageToImgbb(imagePath)
        links.append(imageLink)
    data = FORM_DATA.copy()
    data["entry.705277571"] = description
    data["entry.383106297"] = str(xCoord)
    data["entry.1253928474"] = str(yCoord)
    data["entry.114537537"] = ",".join(links)

    response = requests.post(FORM_URL, data=data)
    return response.status_code == 200

def submitFormAsync(description: str, xCoord: float, yCoord: float, imagePaths: tuple[str]):
    """Non-blocking version of submitForm"""
    def backgroundSubmit():
        try:
            submitForm(description, xCoord, yCoord, imagePaths)
        except Exception as e:
            print(f"Submit error: {e}")  # or however you want to handle errors
    
    threading.Thread(target=backgroundSubmit, daemon=True).start()
