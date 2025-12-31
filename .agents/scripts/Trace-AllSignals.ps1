param([string]$Path = "./")

Write-Host "--- SIGNAL TRACE START ---" -ForegroundColor Cyan

# 1. SCAN C# FILES
Get-ChildItem -Path $Path -Recurse -Include "*.cs" | ForEach-Object {
    $file = $_
    $content = Get-Content $file.FullName
    $hasOutput = $false
    $outputBuffer = @()

    # A. Find Definitions (Godot & C#)
    $content | Select-String -Pattern '\[Signal\]\s*public\s+delegate\s+void\s+(\w+)EventHandler' | ForEach-Object {
        $outputBuffer += "  [DEF] GODOT SIGNAL: '$($_.Matches.Groups[1].Value)' (Line $($_.LineNumber))"
        $hasOutput = $true
    }
    $content | Select-String -Pattern 'public\s+event\s+[\w<>\.]+\s+(\w+);' | ForEach-Object {
        $outputBuffer += "  [DEF] C# EVENT:     '$($_.Matches.Groups[1].Value)' (Line $($_.LineNumber))"
        $hasOutput = $true
    }

    # B. Find Emissions
    $content | Select-String -Pattern 'EmitSignal\(SignalName\.(\w+)' | ForEach-Object {
        $outputBuffer += "  [EMIT] Emits:       '$($_.Matches.Groups[1].Value)' (Line $($_.LineNumber))"
        $hasOutput = $true
    }
    $content | Select-String -Pattern '(\w+)\?\.Invoke' | ForEach-Object {
        $outputBuffer += "  [EMIT] Invokes:     '$($_.Matches.Groups[1].Value)' (Line $($_.LineNumber))"
        $hasOutput = $true
    }

    # C. Find Connections (Subscriptions) with NOISE FILTER
    $content | Select-String -Pattern '(\w+)\s*\+=\s*(\w+)' | ForEach-Object {
        $signal = $_.Matches.Groups[1].Value
        $handler = $_.Matches.Groups[2].Value
        
        # FILTER: Ignore Protobuf CalculateSize() noise and other common false positives.
        if ($signal -ne "size" -and $handler -notmatch "^\d+$" -and $handler -notlike "_*" -and $signal -notlike "_*") {
            $outputBuffer += "  [LINK] Subscribes:  '$signal' -> Calls '$handler' (Line $($_.LineNumber))"
            $hasOutput = $true
        }
    }
    $content | Select-String -Pattern 'Connect\(SignalName\.(\w+)' | ForEach-Object {
        $outputBuffer += "  [LINK] Connects:    '$($_.Matches.Groups[1].Value)' (Line $($_.LineNumber))"
        $hasOutput = $true
    }

    if ($hasOutput) {
        Write-Host "FILE: $($file.Name)" -ForegroundColor Yellow
        $outputBuffer | ForEach-Object { Write-Host $_ }
        Write-Host ""
    }
}

# 2. SCAN SCENE FILES
Get-ChildItem -Path $Path -Recurse -Include "*.tscn" | ForEach-Object {
    $file = $_
    $content = Get-Content $file.FullName
    $connections = $content | Select-String -Pattern '\[connection signal="(\w+)" from="(.+?)" to="(.+?)" method="(.+?)"'
    
    if ($connections) {
        Write-Host "SCENE: $($file.Name)" -ForegroundColor Magenta
        $connections | ForEach-Object {
            $sig = $_.Matches.Groups[1].Value
            $src = $_.Matches.Groups[2].Value
            $target = $_.Matches.Groups[3].Value
            $method = $_.Matches.Groups[4].Value
            Write-Host "  [EDITOR LINK] '$src' emits '$sig' -> '$target' calls '$method'"
        }
        Write-Host ""
    }
}