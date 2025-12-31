<#
.SYNOPSIS
  Generates a clean, targeted directory tree, ignoring common noise folders and allowing for depth and extension filtering.

.DESCRIPTION
  This script provides a highly configurable way to visualize a project's structure.
  - It automatically ignores common development folders like .git, bin, obj, etc.
  - The -MaxDepth parameter prevents overwhelmingly large outputs from deep folder structures.
  - The -IncludeExtensions parameter focuses the output on specific file types (e.g., '.cs', '.tscn'),
    while still showing the directory structure that contains them.

.EXAMPLE
  # Get a high-level overview of the entire project, 3 levels deep
  powershell -File ./Get-FileTree.ps1 -Path ../../ -MaxDepth 3

.EXAMPLE
  # Map out all C# scripts and Godot scene files in the 'src' directory
  powershell -File ./Get-FileTree.ps1 -Path ../../src -IncludeExtensions .cs,.tscn

.EXAMPLE
  # Add a custom folder to the ignore list
  powershell -File ./Get-FileTree.ps1 -Path ../../ -IgnorePatterns 'assets/legacy_art'
#>
[CmdletBinding()]
param(
    [string]$Path = ".",
    [int]$MaxDepth = 6,
    [string[]]$IncludeExtensions,
    [string[]]$IgnorePatterns
)

# 1. Standard set of folders to ignore. Add to this list as needed.
$DefaultIgnores = @(
    "bin", "obj", ".git", "node_modules", ".vs", ".vscode",
    ".godot", ".import", "__pycache__", "venv", ".env"
)
$AllIgnores = $DefaultIgnores + $IgnorePatterns
$IgnoreRegex = "[\\/]($($AllIgnores -join '|'))([\\/]|$)"

# 2. Resolve the absolute path to ensure accurate depth calculation
$Root = (Resolve-Path $Path).Path

# 3. Get all items up to the specified depth
$AllItems = Get-ChildItem -Path $Root -Recurse -Depth $MaxDepth -ErrorAction SilentlyContinue

# 4. Apply filters
$FilteredItems = $AllItems | Where-Object {
    # Exclude anything matching the ignore regex
    $_.FullName -notmatch $IgnoreRegex
}

# 5. If specific extensions are requested, apply a more advanced filter
if ($IncludeExtensions.Count -gt 0) {
    # Ensure extensions have a leading dot for consistent matching
    $NormalizedExtensions = $IncludeExtensions | ForEach-Object {
        if ($_ -notlike ".*") { ".$_" } else { $_ }
    }

    $FilteredItems = $FilteredItems | Where-Object {
        # Always keep directories, but only keep files that match the extension list
        $_.PSIsContainer -or $NormalizedExtensions -contains $_.Extension
    }
}

# 6. Format and print the tree
$FilteredItems | ForEach-Object {
    $Relative = $_.FullName.Substring($Root.Length).TrimStart('\', '/')
    
    # In PowerShell, a file in the root has 0 separators. A file in a subfolder has 1.
    # We add 1 to the count for root files to make the depth calculation work correctly.
    if ($Relative -notcontains [System.IO.Path]::DirectorySeparatorChar) {
        $Depth = 0
    } else {
        $Depth = ($Relative -split "[\\/]").Count - 1
    }

    $Indent = "  " * $Depth
    if ($_.PSIsContainer) {
        "$Indent|-- [$($_.Name)]"
    } else {
        "$Indent|   $($_.Name)"
    }
}