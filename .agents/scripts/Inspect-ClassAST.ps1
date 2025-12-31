param(
    [Parameter(Mandatory=$true)]
    [string]$Path
)

# 1. SILENTLY LOAD ROSLYN (Suppress output to keep context clean)
try {
    # Adjust this path to where your load_roslyn logic lives
    . "$PSScriptRoot/load_roslyn.ps1" | Out-Null
} catch {
    Write-Error "Failed to load Roslyn assemblies. Ensure load_roslyn.ps1 is in the same folder."
    exit 1
}

# 2. PERFORM ANALYSIS
if (-not (Test-Path $Path)) { Write-Error "File not found: $Path"; exit 1 }

$src = Get-Content $Path -Raw
$tree = [Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText($src)
$root = $tree.GetRoot()

# 3. OUTPUT CLEAN DATA FOR THE AGENT
$classes = $root.DescendantNodes().OfType([Microsoft.CodeAnalysis.CSharp.Syntax.ClassDeclarationSyntax])

foreach ($class in $classes) {
    $methods = ($class.Members.OfType([Microsoft.CodeAnalysis.CSharp.Syntax.MethodDeclarationSyntax]) | ForEach-Object { $_.Identifier.ValueText }) -join ", "
    
    Write-Host "--- CLASS: $($class.Identifier.ValueText) ---" -ForegroundColor Cyan
    Write-Host "Inherits: $($if ($class.BaseList) { $class.BaseList.Types.ToString() } else { "Object" })"
    Write-Host "Methods:  $methods"
    Write-Host ""
}