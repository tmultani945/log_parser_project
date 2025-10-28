@echo off
REM Batch script to parse large PDF in background without hanging VSCode

echo ========================================
echo Large PDF Parser - Background Mode
echo ========================================
echo.
echo This script will parse the PDF in background mode.
echo Progress will be logged to: data\parsing_progress.log
echo.
echo You can monitor progress by checking the log file.
echo The parser will save checkpoints every 100 pages.
echo If interrupted, you can resume by running this script again.
echo.
echo Starting parser...
echo.

cd src
start /B python large_pdf_parser.py "../data/input/80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf" "../data/parsed_logcodes.db" 100

echo.
echo Parser started in background!
echo.
echo To monitor progress:
echo   1. Check: data\parsing_progress.log
echo   2. Check: data\parse_checkpoint.json
echo.
echo The process will continue even if you close this window.
echo.
pause
