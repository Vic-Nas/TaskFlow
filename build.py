#!/usr/bin/env python3
"""
Build script for TaskFlow project using PyInstaller
Creates a standalone executable with data folders copied alongside the executable
Preserves original relative path structure (data/settings.json works as-is)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
PROJECT_NAME = "TaskFlow"
MAIN_SCRIPT = "TaskFlow.py"
BUILD_DIR = "build"
DIST_DIR = os.path.join(BUILD_DIR, "dist")
WORK_DIR = os.path.join(BUILD_DIR, "build")

# Folders to copy alongside the executable (NOT included in PyInstaller bundle)
DATA_FOLDERS = [
    "data",
    "src", 
    "tasks",
    "imports"
]

# Additional files to copy
ADDITIONAL_FILES = [
    "index.html",
    "requirements.txt"
]

def clean_build_directories():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build directories...")
    
    directories_to_clean = [BUILD_DIR, "dist", "build", "__pycache__"]
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"   ✓ Removed {directory}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not remove {directory}: {e}")
    
    # Remove .spec files
    for spec_file in Path(".").glob("*.spec"):
        try:
            spec_file.unlink()
            print(f"   ✓ Removed {spec_file}")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not remove {spec_file}: {e}")

def check_dependencies():
    """Check if required tools are available"""
    print("🔍 Checking dependencies...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"   ✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("   ❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("   ✓ PyInstaller installed")
    
    # Check if main script exists
    if not os.path.exists(MAIN_SCRIPT):
        print(f"   ❌ Main script '{MAIN_SCRIPT}' not found!")
        sys.exit(1)
    else:
        print(f"   ✓ Main script '{MAIN_SCRIPT}' found")

def get_hidden_imports():
    """Get list of hidden imports that PyInstaller might miss"""
    hidden_imports = [
        # Tkinter and GUI libraries
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.filedialog",
        "tkinter.simpledialog",
        
        # Common Python libraries that might be missed
        "json",
        "csv",
        "sqlite3",
        "datetime",
        "pathlib",
        "threading",
        "queue",
        "functools",
        "itertools",
        "collections",
        "os",
        "sys",
        "shutil",
        "subprocess",
        
        # Potential project-specific imports
        "importlib",
        "importlib.util",
        "types",
    ]
    
    return hidden_imports

def build_pyinstaller_command():
    """Build the PyInstaller command - NO data folders included, just the executable"""
    print("🔧 Building PyInstaller command...")
    
    # Create build directory
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    command = [
        "pyinstaller",
        "--onedir",  # Create a directory instead of a single file
        "--windowed",  # No console window (GUI app)
        "--clean",  # Clean cache before building
        f"--distpath={DIST_DIR}",
        f"--workpath={WORK_DIR}",
        f"--specpath={BUILD_DIR}",
        f"--name={PROJECT_NAME}",
    ]
    
    # Add hidden imports
    hidden_imports = get_hidden_imports()
    for import_name in hidden_imports:
        command.extend(["--hidden-import", import_name])
    
    # Add main script (use absolute path)
    current_dir = os.path.abspath(".")
    main_script_path = os.path.join(current_dir, MAIN_SCRIPT)
    command.append(main_script_path)
    
    print("   ✓ PyInstaller will create executable only (no data folders bundled)")
    
    return command

def run_pyinstaller():
    """Execute PyInstaller with the built command"""
    print("🚀 Running PyInstaller...")
    
    command = build_pyinstaller_command()
    
    print(f"   Command: {' '.join(command)}")
    print()
    
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        print("   ✓ PyInstaller completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ PyInstaller failed with error code {e.returncode}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def copy_data_folders():
    """Copy data folders alongside the executable to preserve relative paths"""
    print("📁 Copying data folders alongside executable...")
    
    exe_dir = os.path.join(DIST_DIR, PROJECT_NAME)
    
    if not os.path.exists(exe_dir):
        print(f"   ❌ Executable directory not found: {exe_dir}")
        return False
    
    success = True
    
    # Copy data folders
    for folder in DATA_FOLDERS:
        if os.path.exists(folder):
            dest_folder = os.path.join(exe_dir, folder)
            try:
                if os.path.exists(dest_folder):
                    shutil.rmtree(dest_folder)
                shutil.copytree(folder, dest_folder)
                print(f"   ✓ Copied folder: {folder} -> {dest_folder}")
            except Exception as e:
                print(f"   ❌ Failed to copy {folder}: {e}")
                success = False
        else:
            print(f"   ⚠️  Warning: Folder '{folder}' not found, skipping")
    
    # Copy additional files
    for file_path in ADDITIONAL_FILES:
        if os.path.exists(file_path):
            dest_file = os.path.join(exe_dir, file_path)
            try:
                # Create directory if needed
                dest_dir = os.path.dirname(dest_file)
                if dest_dir:
                    os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(file_path, dest_file)
                print(f"   ✓ Copied file: {file_path} -> {dest_file}")
            except Exception as e:
                print(f"   ❌ Failed to copy {file_path}: {e}")
                success = False
        else:
            print(f"   ⚠️  Warning: File '{file_path}' not found, skipping")
    
    return success

def post_build_cleanup():
    """Perform post-build cleanup and organization"""
    print("🎨 Performing post-build cleanup...")
    
    exe_dir = os.path.join(DIST_DIR, PROJECT_NAME)
    
    if not os.path.exists(exe_dir):
        print(f"   ❌ Expected executable directory not found: {exe_dir}")
        return False
    
    print(f"   ✓ Executable created in: {exe_dir}")
    
    # List contents of the executable directory
    print("   📁 Contents of executable directory:")
    try:
        items = []
        for item in os.listdir(exe_dir):
            item_path = os.path.join(exe_dir, item)
            if os.path.isdir(item_path):
                items.append(f"📂 {item}/")
            else:
                items.append(f"📄 {item}")
        
        # Sort and display
        for item in sorted(items):
            print(f"      {item}")
            
    except Exception as e:
        print(f"   ⚠️  Could not list directory contents: {e}")
    
    return True

def create_run_script():
    """Create a simple batch file to run the executable"""
    print("📝 Creating run script...")
    
    batch_file = os.path.join(DIST_DIR, "run_taskflow.bat")
    
    batch_content = f"""@echo off
echo Starting {PROJECT_NAME}...
cd /d "%~dp0{PROJECT_NAME}"
{PROJECT_NAME}.exe
pause
"""
    
    try:
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        print(f"   ✓ Created run script: {batch_file}")
    except Exception as e:
        print(f"   ⚠️  Could not create run script: {e}")

def print_summary():
    """Print build summary and instructions"""
    print("\n" + "="*60)
    print("🎉 BUILD COMPLETED!")
    print("="*60)
    
    exe_dir = os.path.join(DIST_DIR, PROJECT_NAME)
    exe_file = os.path.join(exe_dir, f"{PROJECT_NAME}.exe")
    
    print(f"\n📦 Your executable is ready:")
    print(f"   Location: {os.path.abspath(exe_dir)}")
    print(f"   Executable: {PROJECT_NAME}.exe")
    
    print(f"\n🚀 To run your application:")
    print(f"   1. Navigate to: {os.path.abspath(exe_dir)}")
    print(f"   2. Double-click: {PROJECT_NAME}.exe")
    print(f"   3. Or use the batch file: run_taskflow.bat")
    
    print(f"\n📋 Structure created:")
    print(f"   {PROJECT_NAME}/")
    print(f"   ├── {PROJECT_NAME}.exe")
    print(f"   ├── data/          (your original data folder)")
    print(f"   ├── src/           (your original src folder)")  
    print(f"   ├── tasks/         (your original tasks folder)")
    print(f"   ├── imports/       (your original imports folder)")
    print(f"   └── [PyInstaller files...]")
    
    print(f"\n✅ Benefits:")
    print(f"   • Your code works unchanged (data/settings.json paths work)")
    print(f"   • Executable runs from its own directory like your original setup")
    print(f"   • No Python installation required on target machine")
    print(f"   • All dependencies included")
    
    print(f"\n🧹 After testing:")
    print(f"   You can safely delete the original folders: {', '.join(DATA_FOLDERS)}")
    print(f"   Distribute the entire '{PROJECT_NAME}' folder")

def main():
    """Main build process"""
    print("🔨 TaskFlow Build Script")
    print("="*40)
    
    try:
        # Step 1: Clean previous builds
        clean_build_directories()
        
        # Step 2: Check dependencies
        check_dependencies()
        
        # Step 3: Run PyInstaller (executable only)
        success = run_pyinstaller()
        
        if not success:
            print("\n❌ Build failed!")
            sys.exit(1)
        
        # Step 4: Copy data folders alongside executable
        copy_success = copy_data_folders()
        
        if not copy_success:
            print("\n❌ Failed to copy data folders!")
            sys.exit(1)
        
        # Step 5: Post-build cleanup
        post_build_cleanup()
        
        # Step 6: Create run script
        create_run_script()
        
        # Step 7: Print summary
        print_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()