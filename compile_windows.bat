@echo off
echo ============================================
echo    Compilation Fix 6 pour Windows
echo ============================================
echo.

REM Nettoyage
echo Nettoyage des anciens builds...
rmdir /S /Q build 2>nul
rmdir /S /Q dist 2>nul
del /Q *.spec 2>nul
echo.

REM Compilation
echo Compilation en cours...
py -m PyInstaller --onefile --windowed ^
    --add-data "fix6_model.py;." ^
    --add-data "fix6_visualization.py;." ^
    --add-data "fix6_model_history.py;." ^
    --add-data "check_unique_fix6.py;." ^
    --add-data "design;design" ^
    --collect-all ortools ^
    --collect-all PyQt5 ^
    --collect-all PIL ^
    --hidden-import fix6_model ^
    --hidden-import fix6_visualization ^
    --hidden-import fix6_model_history ^
    --hidden-import check_unique_fix6 ^
    --hidden-import ortools ^
    --hidden-import ortools.sat ^
    --hidden-import ortools.sat.python ^
    --hidden-import ortools.sat.python.cp_model ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageDraw ^
    --hidden-import PIL.ImageFont ^
    --name Fix6Builder ^
    fix6_gui.py

echo.
if exist dist\Fix6Builder.exe (
    echo ============================================
    echo    SUCCES ! Executable cree :
    echo    dist\Fix6Builder.exe
    echo ============================================
    powershell -command "Write-Host ('Taille : ' + [math]::Round((Get-Item dist\Fix6Builder.exe).Length / 1MB, 1) + ' MB')"
) else (
    echo ============================================
    echo    ECHEC de la compilation
    echo ============================================
)
echo.
pause
