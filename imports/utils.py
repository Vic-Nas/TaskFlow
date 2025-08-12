
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
    import tkinter as tk
    from tkinter import ttk
    import time
    import threading
    
    # Main function logic - check for updates first
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
    
    # Show update confirmation dialog (this needs to work without main UI)
    fixes = "\n".join(newDetails["fix"])
    added = "\n".join(newDetails["add"])
    
    # Create temporary root for confirmation dialog
    tempRoot = tk.Tk()
    tempRoot.withdraw()  # Hide the root window
    
    try:
        # Show confirmation using messagebox
        import tkinter.messagebox as msgbox
        
        updateText = f"Update Available!\n\nFixes:\n{fixes}\n\nAdded:\n{added}\n\nDo you want to update now?"
        userConfirmed = msgbox.askyesno("TaskFlow Update", updateText, parent=tempRoot)
        
        if not userConfirmed:
            tempRoot.destroy()
            return
        
    except Exception:
        tempRoot.destroy()
        return
    
    # User confirmed - now show loading dialog during update
    def createLoadingWindow():
        """Create standalone loading window"""
        loadingRoot = tk.Tk()
        loadingRoot.title("TaskFlow Update")
        loadingRoot.geometry("400x180")
        loadingRoot.resizable(False, False)
        
        # Center the window
        loadingRoot.update_idletasks()
        x = (loadingRoot.winfo_screenwidth() // 2) - (400 // 2)
        y = (loadingRoot.winfo_screenheight() // 2) - (180 // 2)
        loadingRoot.geometry(f"400x180+{x}+{y}")
        
        # Disable window close button
        loadingRoot.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Icon and styling
        try:
            loadingRoot.iconbitmap("icon.ico")  # Adjust path as needed
        except:
            pass
        
        # Add content
        titleLabel = tk.Label(loadingRoot, text="Updating TaskFlow", 
                              font=("Arial", 16, "bold"), fg="#2c3e50")
        titleLabel.pack(pady=20)
        
        statusLabel = tk.Label(loadingRoot, text="Initializing update...", 
                               font=("Arial", 11), fg="#34495e")
        statusLabel.pack(pady=10)
        
        progressBar = ttk.Progressbar(loadingRoot, mode='indeterminate', length=300)
        progressBar.pack(pady=15)
        progressBar.start()
        
        infoLabel = tk.Label(loadingRoot, text="Please wait - TaskFlow will restart automatically", 
                             font=("Arial", 9), fg="#7f8c8d")
        infoLabel.pack(pady=5)
        
        return loadingRoot, statusLabel
    
    def performUpdateWithUi():
        """Perform update with UI feedback"""
        # Create loading window
        loadingRoot, statusLabel = createLoadingWindow()
        
        def updateStatus(message):
            """Update status message"""
            statusLabel.config(text=message)
            loadingRoot.update()
            time.sleep(0.8)  # Give user time to read the message
        
        def doUpdate():
            """Actual update process"""
            try:
                updateStatus("Preparing update environment...")
                
                tempDir = os.path.abspath("tempUpdate")
                backupDir = os.path.abspath("backup")
                
                # Get the actual executable path
                if getattr(sys, 'frozen', False):
                    currentExePath = sys.executable
                else:
                    currentExePath = os.path.abspath(sys.argv[0])
                
                exeName = os.path.basename(currentExePath)
                
                # Create directories
                os.makedirs(tempDir, exist_ok=True)
                os.makedirs(backupDir, exist_ok=True)
                
                updateStatus("Creating installation script...")
                
                # Create batch script
                batScript = f"""@echo off
echo TaskFlow Update Process Started > update.log
echo ====================================== >> update.log
echo Local version: {localVersion} >> update.log
echo Repository version: {repoVersion} >> update.log
echo Update time: %date% %time% >> update.log
echo. >> update.log

echo [%time%] Step 1: Creating backup... >> update.log
copy "{currentExePath}" "{backupDir}\\{exeName}.bak" >> update.log 2>&1
if errorlevel 1 (
    echo [%time%] ERROR: Backup failed, aborting update >> update.log
    pause
    goto :cleanup
)
echo [%time%] Backup created successfully >> update.log

echo [%time%] Step 2: Downloading new version... >> update.log
powershell -WindowStyle Hidden -Command "try {{ Write-Host 'Downloading...'; Invoke-WebRequest -Uri 'https://github.com/Vic-Nas/TaskFlow/raw/main/build/dist/TaskFlow/TaskFlow.exe' -OutFile '{tempDir}\\TaskFlow.exe' -TimeoutSec 30; Write-Host 'Download complete' }} catch {{ Write-Host 'Download failed'; exit 1 }}" >> update.log 2>&1
if errorlevel 1 (
    echo [%time%] ERROR: Download failed >> update.log
    goto :cleanup
)
echo [%time%] Download completed successfully >> update.log

echo [%time%] Step 3: Waiting for application to close... >> update.log
timeout /t 3 /nobreak > nul

echo [%time%] Step 4: Installing update... >> update.log
copy /y "{tempDir}\\TaskFlow.exe" "{currentExePath}" >> update.log 2>&1
if errorlevel 1 (
    echo [%time%] ERROR: Installation failed, restoring backup >> update.log
    copy /y "{backupDir}\\{exeName}.bak" "{currentExePath}" >> update.log 2>&1
    if errorlevel 1 (
        echo [%time%] CRITICAL ERROR: Backup restoration failed! >> update.log
    )
    goto :cleanup
)
echo [%time%] Update installed successfully >> update.log

echo [%time%] Step 5: Starting updated application... >> update.log
start "" "{currentExePath}"
echo [%time%] Application restarted >> update.log

:cleanup
echo [%time%] Cleaning up temporary files... >> update.log
if exist "{tempDir}" (
    rmdir /s /q "{tempDir}" >> update.log 2>&1
    echo [%time%] Temporary directory cleaned >> update.log
)
echo [%time%] Update process completed >> update.log
echo ====================================== >> update.log

timeout /t 2 /nobreak > nul
del "%~0"
"""
                
                batPath = os.path.join(os.path.dirname(currentExePath), "update.bat")
                
                updateStatus("Writing installation script...")
                with open(batPath, "w") as batFile:
                    batFile.write(batScript)
                
                updateStatus("Updating version information...")
                try:
                    setSetting("version", repoVersion)
                except:
                    pass
                
                updateStatus("Launching update process...")
                
                # Launch batch file
                subprocess.Popen([batPath], cwd=os.path.dirname(currentExePath), 
                               creationflags=subprocess.CREATE_NO_WINDOW)
                
                updateStatus("TaskFlow will restart in 3 seconds...")
                time.sleep(3)
                
                # Close loading window and exit
                loadingRoot.destroy()
                tempRoot.destroy()
                sys.exit(0)
                
            except Exception as e:
                updateStatus(f"Update failed: {str(e)}")
                time.sleep(3)
                loadingRoot.destroy()
                tempRoot.destroy()
        
        # Start update in thread to keep UI responsive
        updateThread = threading.Thread(target=doUpdate, daemon=True)
        updateThread.start()
        
        # Run loading window
        loadingRoot.mainloop()
    
    # Start the update process
    performUpdateWithUi()
    

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
