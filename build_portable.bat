@echo off
chcp 65001 >nul
echo ======================================
echo Windows Search Tool - 便携版打包脚本
echo ======================================
echo.

REM 检查 Tesseract 便携版是否存在
if not exist "portable\tesseract\tesseract.exe" (
    echo [警告] Tesseract 便携版未找到
    echo 正在复制 Tesseract 文件...

    if not exist "portable\tesseract" mkdir "portable\tesseract"

    REM 复制 Tesseract 文件
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo 复制 tesseract.exe...
        copy "C:\Program Files\Tesseract-OCR\tesseract.exe" "portable\tesseract\" >nul

        echo 复制 DLL 文件...
        copy "C:\Program Files\Tesseract-OCR\*.dll" "portable\tesseract\" >nul

        echo 复制语言数据...
        xcopy "C:\Program Files\Tesseract-OCR\tessdata" "portable\tesseract\tessdata\" /E /I /Y >nul

        echo Tesseract 便携版准备完成!
    ) else (
        echo [错误] 未找到 Tesseract 安装
        echo 请先安装 Tesseract OCR 或手动复制到 portable\tesseract\
        pause
        exit /b 1
    )
)

echo.
echo [1/3] 清理旧的构建文件...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

echo [2/3] 执行 PyInstaller 打包...
echo 这可能需要几分钟,请耐心等待...
echo.

pyinstaller build_portable.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 打包失败!
    echo 请检查错误信息并重试
    pause
    exit /b 1
)

echo.
echo [3/3] 创建便携版压缩包...

REM 重命名输出目录
if exist "dist\WindowsSearchTool_Portable" (
    rmdir /s /q "dist\WindowsSearchTool_Portable" 2>nul
)
ren "dist\WindowsSearchTool" "WindowsSearchTool_Portable"

REM 复制说明文件
copy "README_PORTABLE.md" "dist\WindowsSearchTool_Portable\" 2>nul

echo.
echo ======================================
echo 打包完成!
echo ======================================
echo.
echo 便携版程序位置: dist\WindowsSearchTool_Portable\
echo 可执行文件: dist\WindowsSearchTool_Portable\WindowsSearchTool.exe
echo.
echo 提示:
echo - 整个 WindowsSearchTool_Portable 文件夹可以直接复制到其他电脑
echo - 支持 Windows 10 和 Windows 7
echo - 无需安装任何软件,双击 exe 即可运行
echo.
pause
