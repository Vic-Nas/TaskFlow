#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaskFlow Installer
Downloads and installs TaskFlow application from GitHub
Requires administrator rights
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
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restart the script with administrator privileges"""
    if is_admin():
        return True
    else:
        print("Administrator rights required. Restarting as administrator...")
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            " ".join(sys.argv), 
            None, 
            1
        )
        return False

def download_file(url, destination):
    """Download a file from URL"""
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, destination)
        print(f"Download completed: {destination}")
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract ZIP file"""
    print(f"Extracting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extraction completed to: {extract_to}")
        return True
    except Exception as e:
        print(f"Extraction error: {e}")
        return False

def create_desktop_shortcut(target_path, shortcut_name):
    """Create desktop shortcut"""
    try:
        import win32com.client
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / f"{shortcut_name}.lnk"
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(target_path)
        shortcut.WorkingDirectory = str(target_path.parent)
        shortcut.IconLocation = str(target_path)
        shortcut.save()
        
        print(f"Desktop shortcut created: {shortcut_path}")
        return True
    except ImportError:
        print("win32com module not available. Creating shortcut manually...")
        return create_shortcut_alternative(target_path, shortcut_name)
    except Exception as e:
        print(f"Shortcut creation error: {e}")
        return False

def create_shortcut_alternative(target_path, shortcut_name):
    """Create shortcut without win32com using PowerShell"""
    try:
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / f"{shortcut_name}.lnk"
        
        ps_script = f'''
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{target_path}"
        $Shortcut.WorkingDirectory = "{target_path.parent}"
        $Shortcut.Save()
        '''
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Desktop shortcut created: {shortcut_path}")
            return True
        else:
            print(f"PowerShell shortcut creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Alternative shortcut creation error: {e}")
        return False

def create_uninstaller(install_path):
    """Create uninstaller executable"""
    uninstaller_code = f'''#!/usr/bin/env python3
"""
TaskFlow Uninstaller
Removes TaskFlow application
"""
import shutil
import sys
from pathlib import Path
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    if not is_admin():
        print("Administrator rights required for uninstallation.")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return
    
    install_dir = Path(r"{install_path}")
    
    if install_dir.exists():
        try:
            print("Removing TaskFlow...")
            shutil.rmtree(install_dir)
            print("TaskFlow has been successfully uninstalled.")
            
            # Try to remove desktop shortcut
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "TaskFlow.lnk"
            if shortcut_path.exists():
                shortcut_path.unlink()
                print("Desktop shortcut removed.")
                
        except Exception as e:
            print(f"Uninstallation error: {{e}}")
    else:
        print("TaskFlow installation not found.")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    uninstaller_path = install_path / "uninstall.py"
    try:
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_code)
        print(f"Uninstaller created: {uninstaller_path}")
        
        # Create batch file to run uninstaller
        batch_path = install_path / "uninstall.bat"
        batch_content = f'''@echo off
cd /d "{install_path}"
python uninstall.py
pause
'''
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        print(f"Uninstaller batch file created: {batch_path}")
        
        return True
    except Exception as e:
        print(f"Uninstaller creation error: {e}")
        return False

def main():
    """Main installation function"""
    print("=" * 50)
    print("TaskFlow Installer")
    print("=" * 50)
    
    # Check admin rights
    if not run_as_admin():
        return
    
    # Configuration
    github_url = "https://github.com/Vic-Nas/TaskFlow/archive/refs/heads/main.zip"
    app_name = "TaskFlow"
    program_files = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files'))
    install_dir = program_files / app_name
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_file = temp_path / "TaskFlow.zip"
        extract_dir = temp_path / "extracted"
        
        # Download ZIP file
        if not download_file(github_url, zip_file):
            print("Failed to download TaskFlow. Installation aborted.")
            input("Press Enter to exit...")
            return
        
        # Extract ZIP file
        if not extract_zip(zip_file, extract_dir):
            print("Failed to extract TaskFlow. Installation aborted.")
            input("Press Enter to exit...")
            return
        
        # Find the compiled/win folder in extracted content
        extracted_content = list(extract_dir.iterdir())
        if not extracted_content:
            print("No content found in downloaded archive.")
            input("Press Enter to exit...")
            return
            
        # Look for TaskFlow folder or compiled/win folder
        source_dir = None
        for item in extracted_content:
            if item.is_dir():
                compiled_win = item / "compiled" / "win"
                if compiled_win.exists():
                    source_dir = compiled_win
                    break
        
        if not source_dir:
            print("Could not find compiled/win folder in the archive.")
            print("Please check if the repository structure is correct.")
            input("Press Enter to exit...")
            return
        
        # Create installation directory
        try:
            if install_dir.exists():
                print(f"Removing existing installation at {install_dir}...")
                shutil.rmtree(install_dir)
            
            print(f"Installing TaskFlow to {install_dir}...")
            shutil.copytree(source_dir, install_dir)
            print("Installation completed successfully!")
            
        except Exception as e:
            print(f"Installation error: {e}")
            input("Press Enter to exit...")
            return
    
    # Find main executable
    exe_files = list(install_dir.glob("*.exe"))
    main_exe = None
    
    if exe_files:
        # Look for TaskFlow.exe or use first exe found
        for exe in exe_files:
            if "TaskFlow" in exe.name:
                main_exe = exe
                break
        if not main_exe:
            main_exe = exe_files[0]
    
    # Create desktop shortcut
    if main_exe:
        create_desktop_shortcut(main_exe, "TaskFlow")
    else:
        print("No executable found. Skipping desktop shortcut creation.")
    
    # Create uninstaller
    create_uninstaller(install_dir)
    
    print("\n" + "=" * 50)
    print("Installation Summary:")
    print(f"- TaskFlow installed to: {install_dir}")
    if main_exe:
        print(f"- Main executable: {main_exe}")
        print("- Desktop shortcut created")
    print(f"- Uninstaller created: {install_dir / 'uninstall.bat'}")
    print("=" * 50)
    print("TaskFlow installation completed successfully!")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()