param([Parameter(Mandatory=$true)][string]$Path)

try { . "$PSScriptRoot/load_roslyn.ps1" | Out-Null } catch { exit 1 }

$code = Get-Content $Path -Raw
$tree = [Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText($code)
$root = $tree.GetRoot()

Write-Host "--- DEAD CODE ANALYSIS: $(Split-Path $Path -Leaf) ---" -ForegroundColor Cyan

# Find all Private Fields and Methods
$privates = $root.DescendantNodes() | Where-Object { 
    ($_.Kind() -eq "FieldDeclaration" -or $_.Kind() -eq "MethodDeclaration") -and 
    $_.Modifiers.Any({ $_.ValueText -eq "private" }) 
}

foreach ($member in $privates) {
    $name = ""
    if ($member.Kind() -eq "FieldDeclaration") { 
        $name = $member.Declaration.Variables[0].Identifier.ValueText 
    } else { 
        $name = $member.Identifier.ValueText 
    }

    # Simple check: Does the identifier appear elsewhere in the file?
    # (We subtract 1 because the definition itself counts as 1 match)
    $matches = [regex]::Matches($code, "\b$name\b").Count
    
    if ($matches -le 1) {
        Write-Host "⚠️  UNUSED PRIVATE: '$name' (Line $($member.GetLocation().GetLineSpan().StartLinePosition.Line + 1))" -ForegroundColor Yellow
    }
}