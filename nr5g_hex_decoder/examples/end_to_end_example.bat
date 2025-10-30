@echo off
REM End-to-end example for NR5G Hex Decoder (Windows)
REM Demonstrates the complete two-step workflow

echo ========================================
echo NR5G Hex Decoder - End-to-End Example
echo ========================================
echo.

REM Configuration
set LOGCODE=0xB888
set PDF_PATH=..\data\input\YOUR_ICD.pdf
set METADATA_FILE=metadata_0xB888.json
set PAYLOAD_FILE=sample_payload.hex
set OUTPUT_FILE=decoded_output.json

REM Check if PDF exists
if not exist "%PDF_PATH%" (
    echo ERROR: ICD PDF not found at: %PDF_PATH%
    echo.
    echo Please update PDF_PATH in this script or use the provided metadata:
    echo   python ..\scripts\parse_payload.py -i %PAYLOAD_FILE% -m %METADATA_FILE% -o %OUTPUT_FILE% -v
    echo.
    echo Skipping Step 1 ^(metadata generation^)...
    set SKIP_STEP1=true
) else (
    set SKIP_STEP1=false
)

REM Step 1: Generate Metadata (if PDF exists)
if "%SKIP_STEP1%"=="false" (
    echo STEP 1: Generating Metadata
    echo ========================================
    echo Logcode: %LOGCODE%
    echo PDF: %PDF_PATH%
    echo Output: %METADATA_FILE%
    echo.

    python -m hex_decoder_module.metadata_cli single --logcode %LOGCODE% --pdf "%PDF_PATH%" --output %METADATA_FILE% --verbose

    if errorlevel 1 (
        echo ERROR: Metadata generation failed
        exit /b 1
    )

    echo.
    echo Step 1 completed successfully!
    echo.
) else (
    echo STEP 1: Using Provided Metadata
    echo ========================================
    echo Using existing metadata file: %METADATA_FILE%
    echo.
)

REM Check if metadata file exists
if not exist "%METADATA_FILE%" (
    echo ERROR: Metadata file not found: %METADATA_FILE%
    echo Please generate metadata first or check the file path.
    exit /b 1
)

REM Step 2: Parse Payload
echo STEP 2: Parsing Payload
echo ========================================
echo Input: %PAYLOAD_FILE%
echo Metadata: %METADATA_FILE%
echo Output: %OUTPUT_FILE%
echo.

python ..\scripts\parse_payload.py --input %PAYLOAD_FILE% --metadata %METADATA_FILE% --output %OUTPUT_FILE% --verbose

if errorlevel 1 (
    echo ERROR: Payload parsing failed
    exit /b 1
)

echo.
echo Step 2 completed successfully!
echo.

REM Display Results
echo RESULTS
echo ========================================
echo.
echo Output saved to: %OUTPUT_FILE%
echo.
echo ========================================
echo End-to-end example completed!
echo ========================================
echo.
echo Files generated:
if "%SKIP_STEP1%"=="false" (
    echo   - %METADATA_FILE% ^(metadata^)
)
echo   - %OUTPUT_FILE% ^(decoded payload^)
echo.
echo Next steps:
echo   1. Open %OUTPUT_FILE% to view decoded data
echo   2. Try parsing your own hex payloads
echo   3. Generate metadata for other logcodes
echo.
pause
