param([string]$Path = "./")
Get-ChildItem -Path $Path -Recurse -Include "*.cs" | ForEach-Object {
    $file = $_
    $content = Get-Content $file.FullName
    
    $exports = $content | Select-String -Pattern '\[Export.*?\]\s*(?:public|private|protected)\s+(.+?)\s+(\w+)\s*\{' 
    $signals = $content | Select-String -Pattern '\[Signal\]\s*public\s+delegate\s+void\s+(\w+)EventHandler'
    $nodes   = $content | Select-String -Pattern 'GetNode<(.+?)>\("(.+?)"\)'

    if ($exports -or $signals -or $nodes) {
        Write-Host "--- $($file.Name) ---" -ForegroundColor Cyan
        if ($exports) { 
            Write-Host "EXPORTS (Editor Variables):" -ForegroundColor Yellow
            $exports | ForEach-Object { "  - $($_.Matches.Groups[2].Value) ($($_.Matches.Groups[1].Value))" } 
        }
        if ($signals) { 
            Write-Host "SIGNALS (Events):" -ForegroundColor Magenta
            $signals | ForEach-Object { "  - $($_.Matches.Groups[1].Value)" } 
        }
        if ($nodes) {
            Write-Host "DEPENDENCIES (GetNode):" -ForegroundColor Green
            $nodes | ForEach-Object { "  - Fetches '$($_.Matches.Groups[2].Value)' as $($_.Matches.Groups[1].Value)" }
        }
        Write-Host ""
    }
}