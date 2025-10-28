@echo off
REM Parallel PDF Parser - Batch script for Windows
REM Usage: parse_large_parallel.bat

echo ============================================================
echo Parallel PDF Parser for Large Documents
echo ============================================================
echo.

cd src

REM Configuration
set "PDF_FILE=..\data\input\80-PC674-2_REV_FL_QTI_Tools_Serial_Interface_Control_Document_for_NR5G_Document.pdf"
set "DB_FILE=..\data\parsed_logcodes.db"
set "BATCH_SIZE=200"
set "NUM_WORKERS=4"
set "TIMEOUT=300"

echo Configuration:
echo   PDF File: %PDF_FILE%
echo   Database: %DB_FILE%
echo   Batch Size: %BATCH_SIZE% pages
echo   Workers: %NUM_WORKERS%
echo   Timeout: %TIMEOUT% seconds
echo.
echo Starting parallel parsing...
echo Press Ctrl+C to stop (progress will be saved)
echo.

python parallel_pdf_parser.py "%PDF_FILE%" "%DB_FILE%" %BATCH_SIZE% %NUM_WORKERS% %TIMEOUT%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo Parsing completed successfully!
    echo ============================================================
    echo.
    echo You can now query the database using:
    echo   python app.py query 0x1C07 2
    echo   python app.py list
    echo   python app.py search TxAGC
    echo.
) else (
    echo.
    echo ============================================================
    echo Parsing failed or was interrupted
    echo ============================================================
    echo.
    echo If interrupted, you can resume by running this script again.
    echo Check data\parsing_progress.log for details.
    echo.
)

cd ..
pause
