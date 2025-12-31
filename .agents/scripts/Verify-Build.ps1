# Run the build, capturing all output (stdout and stderr)
Write-Host "--- STARTING BUILD VERIFICATION ---" -ForegroundColor Cyan
$output = dotnet build --nologo --verbosity normal 2>&1

# Check exit code (0 = Success, anything else = Fail)
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ BUILD SUCCEEDED" -ForegroundColor Green
    Write-Host "Action: You may proceed to logic verification or commit." -ForegroundColor Gray
}
else {
    Write-Host "❌ BUILD FAILED" -ForegroundColor Red
    
    # Filter: Show ONLY lines with ": error"
    # This strips out warnings, "Restore completed", and other noise
    $errors = $output | Select-String ": error"
    
    if ($errors) {
        foreach ($err in $errors) {
            Write-Host $err.Line.Trim() -ForegroundColor Red
        }
        Write-Host "`nAction: The build is broken. You MUST fix these errors before proceeding." -ForegroundColor Yellow
        Write-Host "Tip: Use 'read_file' on the file mentioned in the error to see the context." -ForegroundColor Gray
    } else {
        # Fallback if regex fails but build failed (e.g., project file issues)
        Write-Host "Fatal Error (Raw Output):"
        $output | Select-Object -Last 10
    }
}