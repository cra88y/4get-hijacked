param([string]$ScenePath, [string]$ScriptPath)

$sceneContent = Get-Content $ScenePath
$scriptContent = Get-Content $ScriptPath

# 1. Find all GetNode calls in C#
$scriptContent | Select-String 'GetNode<.+?>\("(.+?)"\)' | ForEach-Object {
    $nodeName = $_.Matches.Groups[1].Value
    
    # 2. Check if that name exists in the .tscn
    if ($sceneContent -notmatch "name=`"$nodeName`"") {
        Write-Host "⚠️  WARNING: Script looks for '$nodeName', but it is NOT in the Scene file!" -ForegroundColor Red
    } else {
        Write-Host "✅ Verified: '$nodeName' exists." -ForegroundColor Green
    }
}