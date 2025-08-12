#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
import urllib.request
import urllib.error
import json
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

def get_github_file_list(repo_owner, repo_name, path):
    """Get list of files from GitHub repository using API"""
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
    
    try:
        response = urllib.request.urlopen(api_url)
        data = json.loads(response.read().decode())
        return data
    except Exception as e:
        print(f"Error getting file list: {e}")
        return []

def download_file_with_progress(url, destination):
    """Download file with progress indicator"""
    try:
        response = urllib.request.urlopen(url)
        total_size = int(response.headers.get('Content-Length', 0))
        
        if total_size > 0:
            print(f"  Size: {total_size / (1024*1024):.1f} MB")
        
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
                    print(f"\r  Progress: {progress:.1f}%", end='', flush=True)
                else:
                    print(f"\r  Downloaded: {downloaded / (1024*1024):.1f} MB", end='', flush=True)
        
        print()  # New line after progress
        return True
        
    except Exception as e:
        print(f"  Download error: {e}")
        return False

def download_directory_recursive(repo_owner, repo_name, github_path, local_path):
    """Recursively download directory from GitHub"""
    items = get_github_file_list(repo_owner, repo_name, github_path)
    
    if not items:
        print(f"No items found in {github_path}")
        return False
    
    success = True
    for item in items:
        if item['type'] == 'file':
            # Download file
            file_url = item['download_url']
            local_file = local_path / item['name']
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Downloading {item['name']}...")
            if not download_file_with_progress(file_url, local_file):
                success = False
                
        elif item['type'] == 'dir':
            # Recursively download subdirectory
            subdir_path = local_path / item['name']
            subdir_path.mkdir(parents=True, exist_ok=True)
            
            print(f"Entering directory {item['name']}/...")
            if not download_directory_recursive(repo_owner, repo_name, item['path'], subdir_path):
                success = False
    
    return success

def main():
    print("=" * 50)
    print("TaskFlow Installer (Direct GitHub Download)")
    print("=" * 50)
    
    if not run_as_admin():
        return
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        repo_owner = "Vic-Nas"
        repo_name = "TaskFlow"
        github_path = "compiled/win/TaskFlow"
        
        extract_path = Path(temp_dir) / "taskflow"
        extract_path.mkdir()
        
        # Download files directly from GitHub
        print("Downloading TaskFlow files from GitHub...")
        print(f"Repository: {repo_owner}/{repo_name}")
        print(f"Path: {github_path}")
        print()
        
        if not download_directory_recursive(repo_owner, repo_name, github_path, extract_path):
            print("Download failed!")
            return
        
        # Check download
        files = list(extract_path.rglob("*"))
        print(f"\nDownloaded {len(files)} items")
        
        # Installation
        program_files = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files'))
        install_dir = program_files / "TaskFlow"
        
        if install_dir.exists():
            print("Removing existing installation...")
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
            print("\n" + "=" * 50)
            print("Installation completed successfully!")
            print("=" * 50)
            print(f"TaskFlow installed to: {install_dir}")
            print("Desktop shortcut created.")
            print("Uninstaller available in installation folder.")
        else:
            print("ERROR: No executable found!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()