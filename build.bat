@echo off
setlocal enabledelayedexpansion

echo ====================================
echo TaskFlow Build and Deployment Script
echo ====================================

:: Step 1: Run python build.py
echo.
echo [1/5] Running python build.py...
python build.py
if !errorlevel! neq 0 (
    echo ERROR: Failed to run python build.py
    pause
    exit /b 1
)
echo Python build completed successfully.

:: Step 2: Clean the build/dist/TaskFlow folder
echo.
echo [2/5] Cleaning build/dist/TaskFlow folder...
cd build\dist\TaskFlow
if !errorlevel! neq 0 (
    echo ERROR: Cannot access build/dist/TaskFlow folder
    pause
    exit /b 1
)

:: Delete all files and folders except data, tasks, _internal and TaskFlow.exe
for /d %%D in (*) do (
    if /i not "%%D"=="data" if /i not "%%D"=="tasks" if /i not "%%D"=="_internal" (
        echo Deleting folder: %%D
        rmdir /s /q "%%D"
    )
)

for %%F in (*) do (
    if /i not "%%F"=="TaskFlow.exe" (
        echo Deleting file: %%F
        del /q "%%F"
    )
)

echo Cleanup completed.

:: Return to root directory
cd ..\..\..

:: Step 3: Create ZIP file
echo.
echo [3/5] Creating ZIP file...

:: Check if compiled/win folder exists, create if not
if not exist "compiled\win" (
    echo Creating compiled\win folder...
    mkdir "compiled\win"
)

:: Delete old ZIP if it exists
if exist "compiled\win\TaskFlow.zip" (
    echo Removing old ZIP file...
    del /q "compiled\win\TaskFlow.zip"
)

:: Create new ZIP (using PowerShell)
echo Creating new ZIP file...
powershell -command "Compress-Archive -Path 'build\dist\TaskFlow\*' -DestinationPath 'compiled\win\TaskFlow.zip' -Force"
if !errorlevel! neq 0 (
    echo ERROR: Failed to create ZIP file
    pause
    exit /b 1
)
echo ZIP file created successfully.

:: Step 4: Copy TaskFlow.exe to desktop
echo.
echo [4/5] Copying TaskFlow.exe to desktop...
set "destination=C:\Users\nasci\Desktop\TaskFlow"

:: Create destination folder if it doesn't exist
if not exist "!destination!" (
    echo Creating destination folder...
    mkdir "!destination!"
)

:: Copy TaskFlow.exe
copy "build\dist\TaskFlow\TaskFlow.exe" "!destination!\TaskFlow.exe" /Y
if !errorlevel! neq 0 (
    echo ERROR: Failed to copy to desktop
    pause
    exit /b 1
)
echo TaskFlow.exe copied successfully to !destination!

:: Step 5: Final summary
echo.
echo [5/5] All operations completed successfully!
echo ====================================
echo Summary:
echo - Python build executed
echo - build/dist/TaskFlow folder cleaned
echo - ZIP file created: compiled/win/TaskFlow.zip
echo - TaskFlow.exe copied to: !destination!
echo ====================================
echo.
pause