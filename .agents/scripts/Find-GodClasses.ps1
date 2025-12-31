param([string]$Path = "./")

Write-Host "--- COULD BE A GOD CLASS DETECTION (>500 Lines) ---" -ForegroundColor Cyan

Get-ChildItem -Path $Path -Recurse -Include "*.cs" | ForEach-Object {
    $count = (Get-Content $_.FullName).Count
    if ($count -gt 500) {
        [PSCustomObject]@{
            Lines = $count
            File = $_.Name
            Path = $_.FullName
        }
    }
} | Sort-Object Lines -Descending | Format-Table -AutoSize