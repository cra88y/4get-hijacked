# ~/.agents/load_roslyn.ps1

Write-Host "Attempting to load Roslyn assemblies from NuGet cache..."

$nugetCache = "$env:USERPROFILE\.nuget\packages"
$loadedAssemblies = @()
$loadErrors = @()

# --- Helper Function to find and load a specific DLL ---
function FindAndLoadRoslynDll {
    param (
        [string]$packageName,
        [string]$dllName
    )
    $dllPath = Get-ChildItem -Path "$nugetCache\$packageName" -Recurse -Filter "$dllName.dll" |
        Where-Object { $_.FullName -match "\\lib\\net(standard|[0-9.]+|coreapp[0-9.])+\\" } | # More robust regex
        Sort-Object FullName -Descending | # Get latest version
        Select-Object -First 1

    if ($dllPath) {
        try {
            Add-Type -LiteralPath $dllPath.FullName -ErrorAction Stop # Use LiteralPath for safety with special chars
            $loadedAssemblies += $dllPath.FullName
            Write-Host "✓ Loaded: $($dllPath.FullName)"
            return $true
        } catch {
            $loadErrors += "Error loading $($dllPath.FullName): $($_.Exception.Message)"
            Write-Error "Error loading $($dllPath.FullName): $($_.Exception.Message)"
            return $false
        }
    } else {
        $loadErrors += "$dllName.dll not found in NuGet cache for package $packageName"
        Write-Warning "$dllName.dll not found in NuGet cache for package $packageName"
        return $false
    }
}

# --- Execute loads for necessary Roslyn DLLs ---
FindAndLoadRoslynDll -packageName 'microsoft.codeanalysis' -dllName 'Microsoft.CodeAnalysis'
FindAndLoadRoslynDll -packageName 'microsoft.codeanalysis.csharp' -dllName 'Microsoft.CodeAnalysis.CSharp'

# Optionally, load more if you need semantic models, workspaces, etc.
# FindAndLoadRoslynDll -packageName 'microsoft.codeanalysis.workspaces' -dllName 'Microsoft.CodeAnalysis.Workspaces'
# FindAndLoadRoslynDll -packageName 'microsoft.codeanalysis.csharp.workspaces' -dllName 'Microsoft.CodeAnalysis.CSharp.Workspaces'


# --- Provide summary output ---
if ($loadErrors.Count -eq 0) {
    Write-Host "`nAll required Roslyn assemblies loaded successfully."
} else {
    Write-Host "`nFinished loading Roslyn assemblies with some issues:"
    $loadErrors | ForEach-Object { Write-Host "  - $_" }
    exit 1 # Indicate failure to Kilocode
}