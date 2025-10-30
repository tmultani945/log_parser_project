#!/bin/bash
# End-to-end example for NR5G Hex Decoder
# Demonstrates the complete two-step workflow

set -e  # Exit on error

echo "========================================"
echo "NR5G Hex Decoder - End-to-End Example"
echo "========================================"
echo ""

# Configuration
LOGCODE="0xB888"
PDF_PATH="../data/input/YOUR_ICD.pdf"  # Update this path
METADATA_FILE="metadata_0xB888.json"
PAYLOAD_FILE="sample_payload.hex"
OUTPUT_FILE="decoded_output.json"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PDF exists
if [ ! -f "$PDF_PATH" ]; then
    echo -e "${RED}ERROR: ICD PDF not found at: $PDF_PATH${NC}"
    echo ""
    echo "Please update PDF_PATH in this script or use the provided metadata:"
    echo "  python ../scripts/parse_payload.py -i $PAYLOAD_FILE -m $METADATA_FILE -o $OUTPUT_FILE -v"
    echo ""
    echo "Skipping Step 1 (metadata generation)..."
    SKIP_STEP1=true
else
    SKIP_STEP1=false
fi

# Step 1: Generate Metadata (if PDF exists)
if [ "$SKIP_STEP1" = false ]; then
    echo -e "${BLUE}STEP 1: Generating Metadata${NC}"
    echo "========================================"
    echo "Logcode: $LOGCODE"
    echo "PDF: $PDF_PATH"
    echo "Output: $METADATA_FILE"
    echo ""

    python -m hex_decoder_module.metadata_cli single \
        --logcode "$LOGCODE" \
        --pdf "$PDF_PATH" \
        --output "$METADATA_FILE" \
        --verbose

    echo ""
    echo -e "${GREEN}Step 1 completed successfully!${NC}"
    echo ""
else
    echo -e "${BLUE}STEP 1: Using Provided Metadata${NC}"
    echo "========================================"
    echo "Using existing metadata file: $METADATA_FILE"
    echo ""
fi

# Check if metadata file exists
if [ ! -f "$METADATA_FILE" ]; then
    echo -e "${RED}ERROR: Metadata file not found: $METADATA_FILE${NC}"
    echo "Please generate metadata first or check the file path."
    exit 1
fi

# Step 2: Parse Payload
echo -e "${BLUE}STEP 2: Parsing Payload${NC}"
echo "========================================"
echo "Input: $PAYLOAD_FILE"
echo "Metadata: $METADATA_FILE"
echo "Output: $OUTPUT_FILE"
echo ""

python ../scripts/parse_payload.py \
    --input "$PAYLOAD_FILE" \
    --metadata "$METADATA_FILE" \
    --output "$OUTPUT_FILE" \
    --verbose

echo ""
echo -e "${GREEN}Step 2 completed successfully!${NC}"
echo ""

# Display Results
echo -e "${BLUE}RESULTS${NC}"
echo "========================================"
echo ""

# Check if jq is available for pretty JSON display
if command -v jq &> /dev/null; then
    echo "Decoded output (first 30 lines):"
    echo ""
    jq '.' "$OUTPUT_FILE" | head -30
    echo "..."
    echo ""
    echo -e "${GREEN}Full output saved to: $OUTPUT_FILE${NC}"
else
    echo -e "${GREEN}Output saved to: $OUTPUT_FILE${NC}"
    echo ""
    echo "Tip: Install 'jq' for pretty JSON display:"
    echo "  sudo apt-get install jq   # Ubuntu/Debian"
    echo "  brew install jq           # macOS"
fi

echo ""
echo "========================================"
echo -e "${GREEN}End-to-end example completed!${NC}"
echo "========================================"
echo ""
echo "Files generated:"
if [ "$SKIP_STEP1" = false ]; then
    echo "  - $METADATA_FILE (metadata)"
fi
echo "  - $OUTPUT_FILE (decoded payload)"
echo ""
echo "Next steps:"
echo "  1. Open $OUTPUT_FILE to view decoded data"
echo "  2. Try parsing your own hex payloads"
echo "  3. Generate metadata for other logcodes"
echo ""
