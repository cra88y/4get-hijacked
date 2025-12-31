param([string]$Path = "./")

Write-Host "--- SERVICE DEPENDENCY GRAPH ---" -ForegroundColor Cyan

$services = @{}

# Scan all files for class definitions that implement IInitializableService (or just have Dependencies)
Get-ChildItem -Path $Path -Recurse -Include "*.cs" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    
    # 1. Find Class Name
    if ($content -match 'class\s+(\w+)\s*:\s*.*?IInitializableService') {
        $className = $matches[1]
        
        # 2. Find Dependencies Block
        # Looks for: public List<Type> Dependencies => new() { typeof(A), typeof(B) };
        # Or: get { return new List<Type> { typeof(A) }; }
        
        $deps = @()
        if ($content -match 'Dependencies[\s\S]+?new\s*List<Type>[\s\S]+?{([\s\S]+?)}') {
            $innerBlock = $matches[1]
            [regex]::Matches($innerBlock, 'typeof\((\w+)\)') | ForEach-Object {
                $deps += $_.Groups[1].Value
            }
        }
        
        $services[$className] = $deps
    }
}

# Output Graph
foreach ($svc in $services.Keys | Sort-Object) {
    $depList = $services[$svc]
    if ($depList.Count -eq 0) {
        Write-Host "$svc" -ForegroundColor Green
    } else {
        Write-Host "$svc" -ForegroundColor Cyan -NoNewline
        Write-Host " depends on: $($depList -join ', ')" -ForegroundColor Gray
    }
}