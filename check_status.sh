#!/bin/bash
# Quick status check for PDF parsing (Git Bash version)

echo "========================================"
echo "PDF Parsing Status Check"
echo "========================================"
echo ""

# Check if parsing is complete
if grep -q "PARSING COMPLETE" data/parser_output.log 2>/dev/null; then
    echo "STATUS: ✓ COMPLETE"
    echo ""
    echo "Parsing finished successfully!"
    echo ""
    echo "Summary:"
    grep -E "Total time:|Total pages:|Total logcodes:|Total tables:" data/parser_output.log
    echo ""
    echo "Database: data/parsed_logcodes.db"
    echo ""
    echo "You can now query the data:"
    echo "  cd src"
    echo "  python app.py list"
    echo "  python app.py query 0x1C07 2"
    echo ""

elif [ -f data/parse_checkpoint.json ]; then
    echo "STATUS: ⏳ RUNNING or PAUSED"
    echo ""
    echo "Checkpoint file found. Parser is either:"
    echo "  1. Still running in background, or"
    echo "  2. Was interrupted and can be resumed"
    echo ""
    echo "Current checkpoint:"
    cat data/parse_checkpoint.json
    echo ""
    echo ""
    echo "Last 5 log lines:"
    tail -5 data/parser_output.log 2>/dev/null || echo "  (log file not found)"
    echo ""
    echo "To see live progress:"
    echo "  tail -f data/parser_output.log"
    echo ""

elif [ -f data/parser_output.log ]; then
    echo "STATUS: ❌ ERROR or STOPPED"
    echo ""
    echo "Checkpoint not found and no completion message."
    echo ""
    echo "Last 10 log lines:"
    tail -10 data/parser_output.log
    echo ""

else
    echo "STATUS: ⏸️  NOT STARTED"
    echo ""
    echo "No parsing has been started yet."
    echo "To start parsing, run:"
    echo "  cd src"
    echo "  python large_pdf_parser.py ../data/input/YOUR_PDF.pdf"
    echo ""
fi

echo "Press Enter to close..."
read
