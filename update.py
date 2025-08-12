
from imports.settings import getSetting, setSetting
from imports.utils import alert

import sys
import subprocess, os


# Detect if running as script or executable
fileName = os.path.basename(sys.argv[0])


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
    alert([f"{fixes}", f"{added}"], title="Confirm update:", headings=["Fixes", "Added"])
    
    # Get the actual executable path
    if getattr(sys, 'frozen', False):
        currentExePath = sys.executable
    else:
        currentExePath = os.path.abspath(sys.argv[0])
    
    # Update version setting
    try:
        setSetting("version", repoVersion)
    except:
        pass
    
    # Create update.py script if it doesn't exist
    updateScriptPath = os.path.join(os.path.dirname(currentExePath), "update.py")
    
    # Launch the separate update script with parameters
    subprocess.Popen([
        sys.executable, 
        updateScriptPath,
        str(localVersion),
        str(repoVersion), 
        currentExePath
    ], cwd=os.path.dirname(currentExePath))
    
    # Exit current process immediately
    sys.exit(0)