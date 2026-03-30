@echo off
echo ============================================
echo  Shop Inventory - Environment Setup
echo ============================================

REM ── Auto-detect conda base (works for Miniconda, Anaconda, Mambaforge) ──
FOR /F "tokens=* usebackq" %%i IN (`where conda 2^>nul`) DO (
    SET CONDA_EXE=%%i
    GOTO :found
)
echo ERROR: conda not found in PATH.
echo Please install Miniconda from https://docs.conda.io/en/latest/miniconda.html
echo Or if already installed, open "Anaconda Prompt" instead of regular cmd.
pause
EXIT /B 1

:found
REM Strip \Scripts\conda.exe to get base dir
SET CONDA_BASE=%CONDA_EXE:\Scripts\conda.exe=%
echo Detected conda at: %CONDA_BASE%

REM ── Initialize conda in this shell session ──
CALL "%CONDA_BASE%\Scripts\activate.bat" "%CONDA_BASE%"
IF ERRORLEVEL 1 (
    echo ERROR: Failed to activate conda base.
    pause
    EXIT /B 1
)

REM ── Create or update environment ──
echo.
echo Setting up inventory_env...
CALL conda env create -f environment.yml 2>nul
IF ERRORLEVEL 1 (
    echo Environment already exists, checking for updates...
    CALL conda env update -f environment.yml --prune
)

REM ── Activate the project environment ──
CALL conda activate inventory_env
IF ERRORLEVEL 1 (
    echo ERROR: Failed to activate inventory_env.
    pause
    EXIT /B 1
)

REM ── Verify PyQt6 is available ──
python -c "from PyQt6.QtWidgets import QApplication" 2>nul
IF ERRORLEVEL 1 (
    echo PyQt6 not found, installing via conda-forge...
    CALL conda install -c conda-forge pyqt6 -y
)

echo.
echo Running the inventory shop...
echo.
python main.py
pause
