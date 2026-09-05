@echo off
rem Create D:\algorithm-coaching -> WSL real memory dir symlink (run as Administrator)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Please run this script as Administrator.
    pause
    exit /b 1
)
if exist "D:\algorithm-coaching" (
    echo [INFO] D:\algorithm-coaching already exists.
    pause
    exit /b 0
)
mklink /D "D:\algorithm-coaching" "\\wsl.localhost\Ubuntu\home\ru\work\algorithm-coaching"
if %errorlevel% == 0 (
    echo [OK] Created D:\algorithm-coaching link.
) else (
    echo [FAIL] Creation failed. Enable Windows Developer Mode or contact admin.
)
pause
