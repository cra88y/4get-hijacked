param([string]$Path = "./project.godot")

if (-not (Test-Path $Path)) { Write-Error "project.godot not found at $Path"; exit }

$content = Get-Content $Path
Write-Host "--- GODOT PROJECT SETTINGS ---" -ForegroundColor Cyan

# 1. Autoloads (Global Singletons)
$autoloads = $content | Select-String -Pattern '^\s*(\w+)="res://(.+?)"'
if ($autoloads) {
    Write-Host "[AUTOLOADS] (Global Singletons)" -ForegroundColor Yellow
    foreach ($match in $autoloads) {
        Write-Host "  $($match.Matches.Groups[1].Value) -> $($match.Matches.Groups[2].Value)"
    }
}

# 2. Input Actions
$inputs = $content | Select-String -Pattern '^\s*(\w+)={'
if ($inputs) {
    Write-Host "`n[INPUT MAP] (Defined Actions)" -ForegroundColor Green
    foreach ($match in $inputs) {
        $action = $match.Matches.Groups[1].Value
        if ($action -notmatch "^(run|test|application|display|rendering)") { # Filter out engine settings
            Write-Host "  Action: '$action'"
        }
    }
}

# 3. Physics Layers
$layers = $content | Select-String -Pattern '^layer_(\d+)="(.+?)"'
if ($layers) {
    Write-Host "`n[PHYSICS LAYERS]" -ForegroundColor Magenta
    foreach ($match in $layers) {
        Write-Host "  Layer $($match.Matches.Groups[1].Value): $($match.Matches.Groups[2].Value)"
    }
}