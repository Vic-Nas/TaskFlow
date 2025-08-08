#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaskFlow Installer - Fixed Version
Downloads, extracts and installs TaskFlow application
"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
import urllib.request
import ctypes

def is_admin():
    """Check if running with admin rights"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restart with admin rights"""
    if is_admin():
        return True
    else:
        print("Administrator rights required. Restarting as administrator...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return False

def download_and_extract():
    """Download and extract TaskFlow ZIP"""
    zip_url = "https://github.com/Vic-Nas/TaskFlow/raw/main/compiled/win/TaskFlow.zip"
    
    print("Downloading TaskFlow.zip...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "TaskFlow.zip"
        
        try:
            # Download ZIP file directly
            urllib.request.urlretrieve(zip_url, zip_path)
            print("Download completed.")
            
            # Extract ZIP to temp folder
            extract_path = Path(temp_dir) / "extracted"
            extract_path.mkdir()
            
            print("Extracting files...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Return the extracted folder
            return extract_path
            
        except Exception as e:
            print(f"ERROR: Failed to download/extract: {e}")
            return None

def install_taskflow():
    """Main installation function"""
    print("=" * 50)
    print("TaskFlow Installer")
    print("=" * 50)
    
    # Check admin rights
    if not run_as_admin():
        return
    
    # Download and extract
    temp_extract = download_and_extract()
    if not temp_extract:
        input("Installation failed. Press Enter to exit...")
        return
    
    # Installation directory
    program_files = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files'))
    install_dir = program_files / "TaskFlow"
    
    try:
        # Remove existing installation
        if install_dir.exists():
            print("Removing existing installation...")
            shutil.rmtree(install_dir)
        
        # Create install directory
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy extracted files to installation directory
        print(f"Installing to {install_dir}...")
        
        # Debug: List what was extracted
        extracted_files = list(temp_extract.rglob("*"))
        print(f"DEBUG: Found {len(extracted_files)} items in extracted folder")
        for item in extracted_files[:10]:  # Show first 10 items
            print(f"  - {item}")
        
        if not extracted_files:
            print("ERROR: No files were extracted!")
            input("Press Enter to exit...")
            return
        
        # Copy all files from extracted folder
        copied_count = 0
        for item in temp_extract.rglob("*"):
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(temp_extract)
                dest_path = install_dir / rel_path
                
                # Create parent directories if needed
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, dest_path)
                copied_count += 1
        
        print(f"Files copied successfully. ({copied_count} files)")
        
        # Find TaskFlow.exe
        taskflow_exe = install_dir / "TaskFlow.exe"
        
        if not taskflow_exe.exists():
            # Search for any .exe file
            exe_files = list(install_dir.rglob("*.exe"))
            if exe_files:
                taskflow_exe = exe_files[0]
                print(f"Found executable: {taskflow_exe}")
            else:
                print("ERROR: No executable found!")
                input("Press Enter to exit...")
                return
        
        # Create desktop shortcut
        create_desktop_shortcut(taskflow_exe)
        
        # Create uninstaller
        create_uninstaller(install_dir)
        
        print("\n" + "=" * 50)
        print("INSTALLATION COMPLETED SUCCESSFULLY!")
        print(f"TaskFlow installed to: {install_dir}")
        print(f"Executable: {taskflow_exe}")
        print("Desktop shortcut created.")
        print("=" * 50)
        
    except Exception as e:
        print(f"Installation error: {e}")
    
    input("Press Enter to exit...")

def create_desktop_shortcut(exe_path):
    """Create desktop shortcut using PowerShell"""
    try:
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "TaskFlow.lnk"
        
        ps_command = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{exe_path.parent}"
$Shortcut.Save()
'''
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            print("Desktop shortcut created successfully.")
        else:
            print("Failed to create desktop shortcut.")
            
    except Exception as e:
        print(f"Shortcut creation error: {e}")

def create_uninstaller(install_path):
    """Create simple uninstaller"""
    try:
        uninstaller_code = f'''import shutil
import sys
from pathlib import Path
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

install_dir = Path(r"{install_path}")
desktop = Path.home() / "Desktop" / "TaskFlow.lnk"

print("Uninstalling TaskFlow...")

if install_dir.exists():
    shutil.rmtree(install_dir)
    print("TaskFlow removed.")

if desktop.exists():
    desktop.unlink()
    print("Desktop shortcut removed.")

print("Uninstallation completed.")
input("Press Enter to exit...")
'''
        
        uninstaller_path = install_path / "uninstall.py"
        with open(uninstaller_path, 'w') as f:
            f.write(uninstaller_code)
        
        # Create batch file
        batch_content = f'@echo off\ncd /d "{install_path}"\npython uninstall.py\n'
        batch_path = install_path / "uninstall.bat"
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        print("Uninstaller created.")
        
    except Exception as e:
        print(f"Uninstaller creation error: {e}")

if __name__ == "__main__":
    install_taskflow()