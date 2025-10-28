@echo off
REM Batch file to verify virtual memory settings

echo ========================================
echo Virtual Memory Verification
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File verify_memory.ps1

echo.
pause
