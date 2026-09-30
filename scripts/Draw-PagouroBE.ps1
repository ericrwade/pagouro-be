# Pagouro BE desktop launcher: asks what to draw, draws it, opens the picture.
# Runs from the stick (D:\Pagouro-BE) when it is plugged in, else from the local release folder.
param([string]$Prompt = "", [int]$Steps = 20)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms

$candidates = @("D:\Pagouro-BE", "C:\Users\Eric Wade\PAGOURO_BE\release\Pagouro-BE-1.0")
$dir = $candidates | Where-Object { Test-Path (Join-Path $_ "PAGOURO-BE.bat") } | Select-Object -First 1
if (-not $dir) {
    [System.Windows.Forms.MessageBox]::Show("Pagouro BE was not found on D:\ or in the local release folder.", "Pagouro BE") | Out-Null
    exit 1
}

if (-not $Prompt) {
    $Prompt = [Microsoft.VisualBasic.Interaction]::InputBox("What do you want to draw?`n`nOne plain sentence, e.g. 'a black cat sitting upright' or 'a lighthouse on a rocky coast at dusk'.", "Pagouro BE", "")
}
if (-not $Prompt) { exit 0 }

$host.UI.RawUI.WindowTitle = "Pagouro BE - drawing"
Write-Host ""
Write-Host "  Pagouro BE  (from $dir)"
Write-Host "  Drawing: $Prompt"
Write-Host "  About 95 seconds on this machine when it is idle; a few minutes if the miner is running."
Write-Host ""

Set-Location $dir
$t = [Diagnostics.Stopwatch]::StartNew()
$out = & .\PAGOURO-BE.bat $Prompt $Steps 2>&1 | Out-String
$secs = [int]$t.Elapsed.TotalSeconds
$m = [regex]::Match($out, 'Saved (workspace\\art\\[^\s]+\.png)')
if ($m.Success) {
    $png = Join-Path $dir $m.Groups[1].Value
    Write-Host "  Done in $secs s: $png"
    Invoke-Item $png
} else {
    Write-Host $out
    [System.Windows.Forms.MessageBox]::Show("Nothing was drawn after $secs s. The window behind this box shows why.", "Pagouro BE") | Out-Null
}
