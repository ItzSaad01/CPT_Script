@echo off
setlocal

:: -------- SETTINGS --------
set SCRIPT_NAME=cpt_code_extract.py
set EXE_NAME=Cpt_Extractor

:: -------- CHECK PYTHON INSTALL --------
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Python not found. Installing via winget...
    winget install --id=Python.Python.3 -e --source winget
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python. Please install it manually.
        pause
        exit /b
    )
)

:: -------- INSTALL REQUIRED PACKAGES --------
echo [INFO] Installing required packages...
pip install --upgrade pip >nul
pip install PyInstaller pdf2image pytesseract pillow tqdm >nul

:: -------- BUILD EXECUTABLE --------
echo [INFO] Building standalone EXE using PyInstaller...

python3 -m PyInstaller --onefile --console --name "%EXE_NAME%" ^
--add-data "poppler;poppler" ^
--add-data "tesseract;tesseract" ^
"%SCRIPT_NAME%"

if exist "dist\%EXE_NAME%.exe" (
    echo [✓] Build complete: dist\%EXE_NAME%.exe
) else (
    echo [ERROR] Build failed.
)

pause
