# PowerShell script to verify virtual memory settings

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Virtual Memory Settings Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get page file information
Write-Host "Page File Configuration:" -ForegroundColor Yellow
Get-CimInstance Win32_PageFileSetting | Format-Table Name, InitialSize, MaximumSize -AutoSize

Write-Host ""
Write-Host "Current Page File Usage:" -ForegroundColor Yellow
Get-CimInstance Win32_PageFileUsage | Format-Table Name, AllocatedBaseSize, CurrentUsage, PeakUsage -AutoSize

Write-Host ""
Write-Host "Computer System Memory:" -ForegroundColor Yellow
$computerSystem = Get-CimInstance Win32_ComputerSystem
$totalRAM = [math]::Round($computerSystem.TotalPhysicalMemory / 1GB, 2)
Write-Host "  Total Physical RAM: $totalRAM GB"

$os = Get-CimInstance Win32_OperatingSystem
$freeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
Write-Host "  Free RAM: $freeRAM GB"

Write-Host ""
Write-Host "Recommendations:" -ForegroundColor Green
Write-Host "  - Initial size should be at least 8192 MB (8 GB)"
Write-Host "  - Maximum size should be at least 16384 MB (16 GB)"
Write-Host "  - If values are lower, follow the instructions to increase them"
Write-Host ""

# Check if values are adequate
$pageFile = Get-CimInstance Win32_PageFileSetting
if ($pageFile) {
    $initial = $pageFile.InitialSize
    $maximum = $pageFile.MaximumSize

    if ($initial -eq 0 -or $maximum -eq 0) {
        Write-Host "STATUS: System-managed (automatic)" -ForegroundColor Yellow
        Write-Host "RECOMMENDATION: Change to custom size for better performance with large PDFs" -ForegroundColor Yellow
    }
    elseif ($initial -ge 8192 -and $maximum -ge 16384) {
        Write-Host "STATUS: GOOD - Virtual memory is adequately configured!" -ForegroundColor Green
        Write-Host "You can now run the PDF parser." -ForegroundColor Green
    }
    else {
        Write-Host "STATUS: Too low - Please increase virtual memory" -ForegroundColor Red
        Write-Host "Current: Initial=$initial MB, Maximum=$maximum MB" -ForegroundColor Red
        Write-Host "Needed: Initial=8192 MB, Maximum=16384 MB" -ForegroundColor Red
    }
}
else {
    Write-Host "STATUS: Could not detect page file settings" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to close..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
