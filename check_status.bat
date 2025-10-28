@echo off
REM Quick status check for PDF parsing

echo ========================================
echo PDF Parsing Status Check
echo ========================================
echo.

REM Check if parsing is complete by looking for completion message
findstr /C:"PARSING COMPLETE" data\parser_output.log >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo STATUS: COMPLETE ✓
    echo.
    echo Parsing finished successfully!
    echo.
    echo Summary from log:
    findstr /C:"Total time:" /C:"Total pages:" /C:"Total logcodes:" /C:"Total tables:" data\parser_output.log
    echo.
    echo Database created: data\parsed_logcodes.db
    echo.
    echo You can now query the data:
    echo   cd src
    echo   python app.py list
    echo   python app.py query 0x1C07 2
    echo.
) else (
    REM Check if checkpoint file exists (means still running or was interrupted)
    if exist data\parse_checkpoint.json (
        echo STATUS: RUNNING or PAUSED
        echo.
        echo Checkpoint file found. Parser is either:
        echo   1. Still running in background, or
        echo   2. Was interrupted and can be resumed
        echo.
        echo Current checkpoint:
        type data\parse_checkpoint.json
        echo.
        echo Last 5 log lines:
        powershell -Command "Get-Content data\parser_output.log -Tail 5"
        echo.
        echo To see live progress:
        echo   tail -f data\parser_output.log
        echo.
    ) else (
        REM No checkpoint and no completion message
        if exist data\parser_output.log (
            echo STATUS: ERROR or NOT STARTED
            echo.
            echo Checkpoint file not found and no completion message.
            echo.
            echo Last 10 log lines:
            powershell -Command "Get-Content data\parser_output.log -Tail 10"
            echo.
        ) else (
            echo STATUS: NOT STARTED
            echo.
            echo No parsing has been started yet.
            echo To start parsing, run:
            echo   parse_large_pdf.bat
            echo.
        )
    )
)

echo.
pause
