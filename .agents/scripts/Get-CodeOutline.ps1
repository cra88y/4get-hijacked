param([string]$Path)
if (-not (Test-Path $Path)) { return "File not found." }
$lines = Get-Content $Path
$lines | Select-String -Pattern "(public|private|protected|internal).*?(class|interface|void|int|string|bool|Task|async).*" | ForEach-Object {
    $clean = $_.Line.Trim()
    if ($clean -notmatch "^//") { # Skip comments
        "Line $($_.LineNumber): $clean"
    }
}