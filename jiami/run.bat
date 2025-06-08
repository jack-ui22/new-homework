@echo off
chcp 65001 >nul
title 加解密项目控制台 v1.4
color 0A
setlocal enabledelayedexpansion

REM ================ 基础配置 ================
set "PROJECT_ROOT=%~dp0"
set "CONDA_ENV=key"
set "CONDA_BASE=E:\anaconda"
set "REQUIREMENTS=%PROJECT_ROOT%requirements.txt"

REM ================ 用户界面 ================
:MAIN_MENU
cls
echo ==============================
echo    加解密项目控制台 v1.4
echo ==============================
echo.
echo  1. 执行加密流程
echo  2. 执行解密流程
echo  3. 随机性测试
echo  4. EXIT
echo.
choice /c 1234 /n /m "请选择操作 (1-4): "
set "MENU_CHOICE=%errorlevel%"

if "%MENU_CHOICE%"=="1" (
    set "PROJECT_TYPE=encrypt"
    set "EN_DIR=%PROJECT_ROOT%en"
    set "C_SRC=jiami.c"
    set "EXE_NAME=jiami.exe"
    set "PY_SCRIPTS=massage.py key.py sort.py"
    goto INIT_PROJECT
)
if "%MENU_CHOICE%"=="2" (
    set "PROJECT_TYPE=decrypt"
    set "EN_DIR=%PROJECT_ROOT%de"
    set "C_SRC=jiemi.c"
    set "EXE_NAME=jiemi.exe"
    set "PY_SCRIPTS=ma.py key.py sort.py readkey.py"
    goto INIT_PROJECT
)
if "%MENU_CHOICE%"=="3" goto ALL_TESTS
if "%MENU_CHOICE%"=="4" exit /b 0

REM ================ 项目初始化 ================
:INIT_PROJECT
set "LOG_DIR=%EN_DIR%\logs"
set "BUILD_DIR=%EN_DIR%\build"
set "DATA_DIR=%EN_DIR%\data"
set "SRC_DIR=%EN_DIR%\src"

REM 创建必要目录
for %%d in ("%EN_DIR%" "%LOG_DIR%" "%BUILD_DIR%" "%DATA_DIR%") do (
    if not exist "%%~d" (
        echo [信息] 创建目录: %%~d
        mkdir "%%~d" || (
            echo [错误] 无法创建目录: %%~d
            pause
            goto MAIN_MENU
        )
    )
)

REM ================ 环境检测 ================
REM 检测GCC编译器
where gcc >nul 2>&1 || (
    echo [错误] 未找到GCC编译器
    echo 请安装MinGW-w64并添加至PATH
    pause
    goto MAIN_MENU
)

REM 检测Python环境
set "PYTHON_ENV=0"
set "ENV_PATH=%CONDA_BASE%\envs\%CONDA_ENV%"

REM 检查Conda是否可用
where conda >nul 2>&1
if !errorlevel! equ 0 (
    echo [信息] 检测到Conda已安装
    set "CONDA_AVAILABLE=1"
) else (
    echo [信息] 未检测到Conda，将使用系统Python
    set "CONDA_AVAILABLE=0"
)

if !CONDA_AVAILABLE! equ 1 (
    REM 检查Conda环境是否存在
    if exist "%ENV_PATH%" (
        echo [信息] 发现已存在的Conda环境: %CONDA_ENV%
        set "CONDA_MISSING=0"
    ) else (
        conda info --envs | findstr /b /c:"%CONDA_ENV%" >nul 2>&1 || set "CONDA_MISSING=1"
    )

    if !CONDA_MISSING! equ 1 (
        echo [信息] Conda环境 "%CONDA_ENV%" 不存在，正在创建...
        call conda create --name %CONDA_ENV% --yes python=3.8 || (
            echo [错误] 环境创建失败
            echo [信息] 将尝试使用系统Python
            set "CONDA_AVAILABLE=0"
        )
    )
)

REM 激活环境或使用系统Python
if !CONDA_AVAILABLE! equ 1 (
    REM 激活Conda环境
    call "%CONDA_BASE%\Scripts\activate.bat" %CONDA_ENV% || (
        echo [错误] Conda环境激活失败: %CONDA_ENV%
        echo [信息] 将尝试使用系统Python
        set "CONDA_AVAILABLE=0"
    )
)

if !CONDA_AVAILABLE! equ 0 (
    REM 检测系统Python
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%p in ('where python') do set "PYTHON_PATH=%%p"
        echo [信息] 使用系统Python: !PYTHON_PATH!
        set "PYTHON_ENV=1"
    ) else (
        echo [错误] 未找到Python环境
        echo 请安装Python并添加到PATH
        pause
        goto MAIN_MENU
    )
)

REM 验证Python环境
echo [信息] 验证Python环境...
python --version || (
    echo [错误] Python环境验证失败
    pause
    goto MAIN_MENU
)

REM 安装Python依赖
if exist "%REQUIREMENTS%" (
    echo [信息] 安装Python依赖...
    pip install -r "%REQUIREMENTS%" || (
        echo [警告] 部分依赖安装失败，继续执行...
    )
) else (
    echo [信息] 未找到requirements.txt，跳过依赖安装
)

REM ================ 主执行流程 ================
set "ERROR_FLAG=0"
set "TASK_COUNTER=0"

REM [阶段1/4] 编译C模块
echo [阶段1/4] 编译C模块...
gcc -o "%BUILD_DIR%\%EXE_NAME%" "%SRC_DIR%\%C_SRC%" -I"%CONDA_BASE%\include" -L"%CONDA_BASE%\libs" || (
    echo [错误] C模块编译失败
    set "ERROR_FLAG=1"
    goto CLEANUP
)

REM [阶段2/4] 执行Python预处理脚本
for %%s in (%PY_SCRIPTS%) do (
    set /a TASK_COUNTER+=1
    echo [阶段2/4][!TASK_COUNTER!] 执行 %%~s
    
    REM 使用24小时制时间避免AM/PM问题
    for /f "tokens=1-3 delims=/" %%a in ("%date%") do (
        set "log_date=%%a%%b%%c"
    )
    set "log_time=%time%"
    set "log_time=!log_time::=!"
    set "log_time=!log_time:.=!"
    set "log_time=!log_time: =0!"
    
    set "LOG_FILE=%LOG_DIR%\%%~ns_!log_date!!log_time:~0,4!.log"
    
    python -X utf8 "%SRC_DIR%\%%~s" > "!LOG_FILE!" 2>&1 || (
        echo [错误] 执行失败 (代码: !ERRORLEVEL!^)
        echo 查看日志: "!LOG_FILE!"
        type "!LOG_FILE!"
        set "ERROR_FLAG=1"
        goto CLEANUP
    )
)

REM [阶段3/4] 运行C程序
echo [阶段3/4] 执行%PROJECT_TYPE%程序...
"%BUILD_DIR%\%EXE_NAME%" "%DATA_DIR%\input.txt" "%DATA_DIR%\output.bin" || (
    echo [错误] 程序执行失败 (代码: %errorlevel%)
    set "ERROR_FLAG=1"
    goto CLEANUP
)

REM [阶段4/4] 打包输出
echo [阶段4/4] 生成发布包...
if not exist "%BUILD_DIR%\%EXE_NAME%" (
    echo [错误] 核心模块缺失
    set "ERROR_FLAG=1"
    goto CLEANUP
)

set "ZIPFILE=%BUILD_DIR%\release_%PROJECT_TYPE%_%date:~0,4%%date:~5,2%%date:~8,2%.zip"
if exist "%ProgramFiles%\7-Zip\7z.exe" (
    "%ProgramFiles%\7-Zip\7z.exe" a -tzip "%ZIPFILE%" "%BUILD_DIR%\%EXE_NAME%" "%DATA_DIR%\output.bin"
) else (
    powershell Compress-Archive -Path "%BUILD_DIR%\%EXE_NAME%", "%DATA_DIR%\output.bin" -DestinationPath "%ZIPFILE%"
)
if errorlevel 1 (
    echo [警告] 打包失败，但主要流程已完成
)

:CLEANUP
if "%ERROR_FLAG%"=="1" (
    echo 执行过程中发生错误，请检查日志
    pause
    goto MAIN_MENU
)

echo.
echo 所有任务成功完成！
echo 生成输出文件: "%DATA_DIR%\output.bin"
echo 发布包位置: "%ZIPFILE%"
timeout /t 10 >nul
goto MAIN_MENU

REM ================ 所有测试功能 ================
:ALL_TESTS
echo.
echo [功能测试和随机性测试] 开始运行...

REM 确保测试日志目录存在
set "TEST_LOG_DIR=%PROJECT_ROOT%logs"
if not exist "%TEST_LOG_DIR%" (
    echo [信息] 创建日志目录: %TEST_LOG_DIR%
    mkdir "%TEST_LOG_DIR%" || (
        echo [错误] 无法创建日志目录
        pause
        goto MAIN_MENU
    )
)

REM 使用统一的时间戳格式
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%"

REM 运行功能测试
set "TEST_LOG=%TEST_LOG_DIR%\test_log_%TIMESTAMP%.log"
echo 执行测试脚本: test.py
echo 日志文件: %TEST_LOG%
python -X utf8 "%PROJECT_ROOT%test.py" > "%TEST_LOG%" 2>&1

if errorlevel 1 (
    echo [错误] 功能测试失败 (代码: %errorlevel%)
    echo 查看日志: "%TEST_LOG%"
) else (
    echo [成功] 功能测试通过
)

REM 运行随机性测试
set "RANDOM_LOG=%TEST_LOG_DIR%\random_test_log_%TIMESTAMP%.log"
echo 执行随机性测试: test_random.py
echo 日志文件: %RANDOM_LOG%
python -X utf8 "%PROJECT_ROOT%test_random.py" > "%RANDOM_LOG%" 2>&1

if errorlevel 1 (
    echo [错误] 随机性测试失败 (代码: %errorlevel%)
    echo 查看日志: "%RANDOM_LOG%"
) else (
    echo [成功] 随机性测试通过
    echo 测试报告摘要:
    type "%RANDOM_LOG%" | findstr "Report"
)

echo.
echo 测试执行完成，按任意键返回主菜单...
pause >nul
goto MAIN_MENU