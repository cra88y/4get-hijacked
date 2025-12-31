param([string]$Term, [string]$Path = ".")

Get-ChildItem -Path $Path -Recurse -Include "*.cs" | Select-String -Pattern "\b$Term\b" -Context 1,1 | ForEach-Object {
    Write-Host "--- FILE: $($_.Path) (Line $($_.LineNumber)) ---" -ForegroundColor Cyan
    $_.Context.PreContext
    ">>> " + $_.Line.Trim()
    $_.Context.PostContext
    Write-Host ""
}