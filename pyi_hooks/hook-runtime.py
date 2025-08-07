"""
Runtime hook to set working directory correctly for PyInstaller
This ensures that relative paths like 'data/settings.json' work correctly
"""

import os
import sys

def set_working_directory():
    """Set the working directory to the executable directory"""
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller executable
        # Set working directory to where data files are extracted
        os.chdir(sys._MEIPASS)
    elif hasattr(sys, 'frozen'):
        # Running as other type of executable
        exe_dir = os.path.dirname(sys.executable)
        os.chdir(exe_dir)

# Execute the function when the hook is imported
set_working_directory()
