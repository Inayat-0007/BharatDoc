$files = git ls-files
$outputFile = "docs\BharatDoc_Source_Code.md"
$excludeExtensions = @(".pdf", ".png", ".svg", ".jpg", ".jpeg", ".ico", ".zip", ".exe", ".bin")
$excludeFiles = @("package-lock.json")

if (!(Test-Path "docs")) { New-Item -ItemType Directory -Path "docs" }
"Project Source Code Documentation`n" | Out-File $outputFile

foreach ($file in $files) {
    $extension = [System.IO.Path]::GetExtension($file).ToLower()
    $filename = [System.IO.Path]::GetFileName($file)
    
    if ($excludeExtensions -contains $extension) { continue }
    if ($excludeFiles -contains $filename) { continue }
    
    "## File: $file" | Out-File $outputFile -Append
    $lang = $extension.Trim('.')
    if ($lang -eq "") { $lang = "text" }
    '```' + $lang | Out-File $outputFile -Append
    Get-Content $file | Out-File $outputFile -Append
    '```' | Out-File $outputFile -Append
    '' | Out-File $outputFile -Append
}
