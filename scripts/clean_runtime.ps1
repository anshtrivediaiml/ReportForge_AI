param(
    [switch]$IncludeDependencies
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$targets = @(
    "__pycache__",
    "logs",
    "outputs",
    "api\\outputs",
    "temp_extract",
    "api\\temp_extract",
    "uploads"
)

if ($IncludeDependencies) {
    $targets += @(
        "venv",
        "web\\node_modules"
    )
}

foreach ($target in $targets) {
    if (Test-Path $target) {
        try {
            $children = Get-ChildItem $target -Force -ErrorAction Stop
            if ($children.Count -eq 0) {
                Write-Host "Skipping empty $target"
                continue
            }

            Write-Host "Clearing $target"
            $children | Remove-Item -Recurse -Force -ErrorAction Stop
        } catch {
            Write-Warning "Failed to remove ${target}: $($_.Exception.Message)"
        }
    }
}

Write-Host "Runtime cleanup complete."
