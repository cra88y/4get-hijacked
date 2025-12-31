param([string]$Path = "./src")

$interfaces = @{}
$implementations = @{}

Write-Host "--- INTERFACE COMPOSITION MAP ---" -ForegroundColor Cyan

# 1. Find all Interfaces
Get-ChildItem -Path $Path -Recurse -Include "*.cs" | Select-String -Pattern 'public\s+interface\s+(I\w+)' | ForEach-Object {
    $name = $_.Matches.Groups[1].Value
    $interfaces[$name] = $_.Filename
}

# 2. Find all Implementations
Get-ChildItem -Path $Path -Recurse -Include "*.cs" | Select-String -Pattern 'class\s+(\w+)\s*:\s*.*?(I\w+)' | ForEach-Object {
    $class = $_.Matches.Groups[1].Value
    $interface = $_.Matches.Groups[2].Value
    
    if ($interfaces.ContainsKey($interface)) {
        if (-not $implementations.ContainsKey($interface)) { $implementations[$interface] = @() }
        $implementations[$interface] += $class
    }
}

# 3. Output
foreach ($i in $interfaces.Keys | Sort-Object) {
    $impls = if ($implementations[$i]) { $implementations[$i] -join ", " } else { "NO IMPLEMENTATION FOUND" }
    $color = if ($impls -eq "NO IMPLEMENTATION FOUND") { "Red" } else { "Green" }
    
    Write-Host "$i" -ForegroundColor Cyan -NoNewline
    Write-Host " -> [$impls]" -ForegroundColor $color
}