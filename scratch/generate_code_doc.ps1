$include = @("*.py", "*.ts", "*.tsx", "*.css", "*.html", "*.md", "Dockerfile*", "docker-compose*.yml")
$exclude = @("node_modules", ".git", "dist", ".next", "BharatDoc_Source_Code.md")

$files = Get-ChildItem -Path . -Recurse -Include $include -File | Where-Object { 
    $path = $_.FullName
    $shouldExclude = $false
    foreach ($ex in $exclude) {
        if ($path -like "*\$ex\*") { $shouldExclude = $true; break }
    }
    -not $shouldExclude
}

$outputFile = "docs\BharatDoc_Source_Code.md"
if (!(Test-Path "docs")) { New-Item -ItemType Directory -Path "docs" }
"" | Out-File $outputFile

foreach ($file in $files) {
    $relativePath = $file.FullName.Replace("c:\Users\moham\Music\New folder\", "")
    "## File: $relativePath" | Out-File $outputFile -Append
    '```' + $file.Extension.Trim('.') | Out-File $outputFile -Append
    Get-Content $file.FullName | Out-File $outputFile -Append
    '```' | Out-File $outputFile -Append
    '' | Out-File $outputFile -Append
}
