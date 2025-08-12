#!/usr/bin/env python3
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
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if is_admin():
        return True
    else:
        print("Administrator rights required. Restarting as administrator...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return False

def create_desktop_shortcut(exe_path):
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
        
        result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if result.returncode == 0:
            print("Desktop shortcut created.")
        else:
            print("Failed to create desktop shortcut.")
            
    except Exception as e:
        print(f"Shortcut creation error: {e}")

def create_uninstaller(install_path):
    try:
        # Create simple batch uninstaller
        batch_content = f'''@echo off
echo TaskFlow Uninstaller
echo ====================
echo.
echo This will completely remove TaskFlow from your system.
pause
echo.
echo Removing TaskFlow...

:: Request admin rights
net session >nul 2>&1
if not %errorLevel% == 0 (
    echo Administrator rights required.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

:: Remove installation directory
if exist "{install_path}" (
    rmdir /s /q "{install_path}"
    echo TaskFlow removed successfully.
) else (
    echo TaskFlow installation not found.
)

:: Remove desktop shortcut
if exist "%USERPROFILE%\\Desktop\\TaskFlow.lnk" (
    del "%USERPROFILE%\\Desktop\\TaskFlow.lnk"
    echo Desktop shortcut removed.
)

echo.
echo Uninstallation completed.
pause
'''
        
        batch_path = install_path / "uninstall.bat"
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        print("Uninstaller created.")
        
    except Exception as e:
        print(f"Uninstaller creation error: {e}")

def main():
    print("=" * 50)
    print("TaskFlow Installer")
    print("=" * 50)
    
    if not run_as_admin():
        return
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        zip_url = "https://github.com/Vic-Nas/TaskFlow/raw/main/compiled/win/TaskFlow.zip"
        zip_path = Path(temp_dir) / "TaskFlow.zip"
        extract_path = Path(temp_dir) / "extracted"
        
        # Download
        print("Downloading TaskFlow.zip...")
        
        def download_with_progress(url, destination):
            try:
                response = urllib.request.urlopen(url)
                total_size = int(response.headers.get('Content-Length', 0))
                
                if total_size > 0:
                    print(f"File size: {total_size / (1024*1024):.1f} MB")
                
                downloaded = 0
                chunk_size = 8192
                
                with open(destination, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='', flush=True)
                        else:
                            print(f"\rDownloaded: {downloaded / (1024*1024):.1f} MB", end='', flush=True)
                
                print()  # New line after progress
                return True
                
            except Exception as e:
                print(f"Download error: {e}")
                return False
        
        if not download_with_progress(zip_url, zip_path):
            print("Download failed!")
            return
        
        # Extract
        print("Extracting...")
        extract_path.mkdir()
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Check extraction
        files = list(extract_path.rglob("*"))
        print(f"Extracted {len(files)} items")
        
        # Installation
        program_files = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files'))
        install_dir = program_files / "TaskFlow"
        
        if install_dir.exists():
            shutil.rmtree(install_dir)
        
        install_dir.mkdir(parents=True)
        
        # Copy files
        print("Installing files...")
        for item in extract_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(extract_path)
                dest = install_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
        
        # Find exe
        taskflow_exe = install_dir / "TaskFlow.exe"
        if not taskflow_exe.exists():
            exe_files = list(install_dir.glob("*.exe"))
            if exe_files:
                taskflow_exe = exe_files[0]
        
        if taskflow_exe.exists():
            print(f"Found executable: {taskflow_exe}")
            create_desktop_shortcut(taskflow_exe)
            create_uninstaller(install_dir)
            print("Installation completed successfully!")
        else:
            print("ERROR: No executable found!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()