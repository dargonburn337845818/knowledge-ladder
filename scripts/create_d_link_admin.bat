@echo off
rem 以管理员身份运行：创建 D:\algorithm-coaching -> WSL 真实记忆目录 的目录符号链接
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请右键“以管理员身份运行”本脚本。
    pause
    exit /b 1
)
if exist "D:\algorithm-coaching" (
    echo [提示] D:\algorithm-coaching 已存在，未重复创建。
    pause
    exit /b 0
)
mklink /D "D:\algorithm-coaching" "\\wsl.localhost\Ubuntu\home\ru\work\algorithm-coaching"
if %errorlevel% == 0 (
    echo [完成] 已创建 D:\algorithm-coaching 链接。
) else (
    echo [失败] 创建失败，请确认 Windows“开发者模式”已开启，或联系管理员。
)
pause
