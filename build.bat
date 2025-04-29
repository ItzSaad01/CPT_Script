@echo off
setlocal

:: ---------- CONFIG ----------
set SCRIPT_NAME=cpt_script_extract.py
set EXE_NAME=cpt_script.exe
set DIST_DIR=dist
set BUILD_DIR=build
set SPEC_FILE=%SCRIPT_NAME:.py=.spec%

:: Poppler and Tesseract directories relative to this folder
set POPPLER=poppler
set TESSERACT=tesseract

echo.
echo [INFO] Installing required Python packages...
pip install --quiet pyinstaller pdf2image pytesseract pillow tqdm

echo.
echo [INFO] Cleaning old build files...
rmdir /s /q %DIST_DIR%
rmdir /s /q %BUILD_DIR%
del /q %SPEC_FILE%

echo.
echo [INFO] Building %EXE_NAME% using PyInstaller...
pyinstaller --onefile ^
 --add-data "%POPPLER%;%POPPLER%" ^
 --add-data "%TESSERACT%;%TESSERACT%" ^
 --name "%EXE_NAME:.exe=%" ^
 "%SCRIPT_NAME%"

IF EXIST "%DIST_DIR%\%EXE_NAME%" (
    echo.
    echo [SUCCESS] Build complete! Output located at %DIST_DIR%\%EXE_NAME%
) ELSE (
    echo.
    echo [ERROR] Build failed. Check for errors above.
)

echo.
pause

