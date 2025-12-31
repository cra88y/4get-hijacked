param([string]$Path = ".")
$projects = Get-ChildItem -Path $Path -Recurse -Filter "*.csproj"
$output = foreach ($proj in $projects) {
    $xml = [xml](Get-Content $proj.FullName)
    [PSCustomObject]@{
        Project = $proj.Name
        Framework = $xml.Project.PropertyGroup.TargetFramework
        Packages = ($xml.Project.ItemGroup.PackageReference | ForEach-Object { "$($_.Include) ($($_.Version))" }) -join ", "
        ProjectRefs = ($xml.Project.ItemGroup.ProjectReference | ForEach-Object { $_.Include }) -join ", "
    }
} 
$output | Format-List