param([string]$Path = "./")

$registered = @{}
$resolved = @{}

Write-Host "--- CUSTOM DI AUDIT ---" -ForegroundColor Cyan

# 1. DYNAMICALLY FIND APPINITIALIZER
$initFile = Get-ChildItem -Path $Path -Recurse -Filter "AppInitializer.cs" | Select-Object -First 1

if ($initFile) {
    Write-Host "Found AppInitializer at: $($initFile.FullName)" -ForegroundColor Gray
    $content = Get-Content $initFile.FullName

    # A. Find 'new Service()' assignments
    $content | Select-String -Pattern 'new\s+(\w+)\(' | ForEach-Object {
        $type = $_.Matches.Groups[1].Value
        # Filter out system types
        if ($type -notin @("List", "Dictionary", "Stopwatch", "HashSet", "Exception", "AOTInit", "Callable", "Task")) {
            $registered[$type] = "AppInitializer"
        }
    }
    
    # B. Find Singleton Registrations (e.g. Config.Singleton)
    $content | Select-String -Pattern 'registry\.Register\((.+?)\.Singleton\)' | ForEach-Object {
        $type = $_.Matches.Groups[1].Value
        $registered[$type] = "Autoload/Singleton"
    }
} else {
    Write-Error "Could not find 'AppInitializer.cs' anywhere in '$Path'. Check your path."
    exit
}

# 2. FIND RESOLUTIONS (Get<T> and Dependencies)
# We exclude 'InputStream.cs' or similar generated files if they are too noisy, 
# but for now we just filter the TYPES.

Get-ChildItem -Path $Path -Recurse -Include "*.cs" | ForEach-Object {
    $fileContent = Get-Content $_.FullName
    
    # Pattern A: ServiceRegistry.Registry.Get<T>()
    $fileContent | Select-String -Pattern '(?:Get|TryGet|IsRegistered)<(\w+)>' | ForEach-Object {
        $type = $_.Matches.Groups[1].Value
        if (-not $resolved.ContainsKey($type)) { $resolved[$type] = @() }
        $resolved[$type] += "$($_.Filename)"
    }

    # Pattern B: typeof(T) inside Dependencies lists
    # We try to be stricter: only look for typeof() if the line looks like a list or dependency definition
    $fileContent | Select-String -Pattern 'typeof\((\w+)\)' | ForEach-Object {
        $type = $_.Matches.Groups[1].Value
        
        # NOISE FILTER: Ignore Data Types, Payloads, Responses, and Godot Structs
        if ($type -notmatch "(Payload|Response|Data|Config|Vector|Error|Exception|List|Dictionary|Task)") {
            if (-not $resolved.ContainsKey($type)) { $resolved[$type] = @() }
            $resolved[$type] += "$($_.Filename) (Dependency)"
        }
    }
}

# 3. ANALYSIS
Write-Host "`n[REGISTERED SERVICES] ($($registered.Count))" -ForegroundColor Green
$registered.Keys | Sort-Object | ForEach-Object { Write-Host "  - $_" }

Write-Host "`n[POTENTIAL ORPHANS] (Registered but never Get<> or listed as Dependency)" -ForegroundColor Yellow
foreach ($key in $registered.Keys) {
    if (-not $resolved.ContainsKey($key)) {
        Write-Host "  - $key"
    }
}

Write-Host "`n[MISSING SERVICES] (Requested via Get<> but not found in AppInitializer)" -ForegroundColor Red
foreach ($key in $resolved.Keys) {
    if (-not $registered.ContainsKey($key) -and $key -ne "T") {
        # Double check: Is it an Interface? (We might register 'NakamaService' but request 'INakamaService')
        # If the requested type starts with 'I' and the registered type contains the rest, it's likely fine.
        $likelyMatch = $registered.Keys | Where-Object { "I$_" -eq $key }
        
        if ($likelyMatch) {
             # It's mapped (e.g. Registered 'Auth', Requested 'IAuth') - Skip or show as Green
             # Write-Host "  - $key (Mapped to $likelyMatch)" -ForegroundColor DarkGray
        } else {
             Write-Host "  - $key (Requested in $($resolved[$key][0]))"
        }
    }
}