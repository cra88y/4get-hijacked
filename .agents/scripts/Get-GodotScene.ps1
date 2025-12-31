param([string]$Path)
if (-not (Test-Path $Path)) { return "Scene file not found." }

$content = Get-Content $Path
Write-Host "--- SCENE: $(Split-Path $Path -Leaf) ---" -ForegroundColor Cyan

# 1. Find External Resources (Scripts)
$scripts = @{}
$content | Select-String '\[ext_resource type="Script" path="res://(.+?)" id="(\w+)"\]' | ForEach-Object {
    $scripts[$_.Matches.Groups[2].Value] = $_.Matches.Groups[1].Value
}

# 2. Parse Nodes
$content | Select-String '\[node name="(.+?)" type="(.+?)"(?: parent="(.+?)")?(?: index="\d+")?\]' | ForEach-Object {
    $name = $_.Matches.Groups[1].Value
    $type = $_.Matches.Groups[2].Value
    $parent = $_.Matches.Groups[3].Value
    
    # Check if this node has a script attached
    $scriptName = ""
    $lineIndex = $_.LineNumber - 1
    # Look ahead a few lines for script resource
    for ($i = 1; $i -lt 5; $i++) {
        if ($content[$lineIndex + $i] -match 'script = ExtResource\("(\w+)"\)') {
            $id = $matches[1]
            if ($scripts.ContainsKey($id)) { $scriptName = " [Script: $($scripts[$id])]" }
        }
    }

    $indent = if ($parent) { "  " } else { "" }
    "$indent|-- $name ($type)$scriptName"
}