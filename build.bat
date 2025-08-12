@echo off
setlocal enabledelayedexpansion
echo ====================================
echo TaskFlow Build Script (No ZIP)
echo ====================================

:: Step 1: Run python build.py
echo.
echo [1/3] Running python build.py...
python build.py
if !errorlevel! neq 0 (
    echo ERROR: Failed to run python build.py
    pause
    exit /b 1
)
echo Python build completed successfully.

:: Step 2: Clean the build/dist/TaskFlow folder
echo.
echo [2/3] Cleaning build/dist/TaskFlow folder...
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

:: Step 3: Prepare release folder structure
echo.
echo [3/3] Preparing release structure...

:: Check if compiled/win folder exists, create if not
if not exist "compiled\win" (
    echo Creating compiled\win folder...
    mkdir "compiled\win"
)

:: Clean old compiled files
if exist "compiled\win\TaskFlow" (
    echo Removing old compiled folder...
    rmdir /s /q "compiled\win\TaskFlow"
)

:: Copy build to compiled (without creating ZIP)
echo Copying build to compiled/win/TaskFlow...
xcopy "build\dist\TaskFlow\*" "compiled\win\TaskFlow\" /E /I /H /Y
if !errorlevel! neq 0 (
    echo ERROR: Failed to copy files
    pause
    exit /b 1
)

echo Files copied successfully.

:: Step 4: Final summary
echo.
echo ====================================
echo Build completed successfully!
echo ====================================
echo Summary:
echo - Python build executed
echo - build/dist/TaskFlow folder cleaned
echo - Files ready in: compiled/win/TaskFlow/
echo - No ZIP file created (files ready for Git commit)
echo ====================================
echo.
echo You can now commit the individual files to Git.
echo The installer will download them directly from GitHub.
echo.
pause